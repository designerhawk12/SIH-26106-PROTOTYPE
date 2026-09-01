"""Deterministic, offline parsing of hostile RFC/MIME email evidence."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import ipaddress
import re
from typing import Iterable
from urllib.parse import urlsplit

from ...schemas import (
    AttachmentEvidence,
    AuthenticationResults,
    AuthenticationVerdict,
    ExtractedIOC,
    IOCSource,
    IOCType,
    MailboxAddress,
    MimePart,
    ParsedEmail,
    ReceivedHop,
)


_EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
_IP_TOKEN_RE = re.compile(r"(?<![A-Fa-f0-9:.])\[?([A-Fa-f0-9:.]+)\]?(?![A-Fa-f0-9:.])")
_SUSPICIOUS_EXTENSIONS = frozenset(
    {".exe", ".scr", ".bat", ".cmd", ".com", ".js", ".jse", ".vbs", ".vbe", ".ps1", ".msi", ".jar", ".hta"}
)
_AUTH_VALUES = {
    "pass": AuthenticationVerdict.PASS,
    "fail": AuthenticationVerdict.FAIL,
    "softfail": AuthenticationVerdict.SOFTFAIL,
    "neutral": AuthenticationVerdict.NEUTRAL,
    "none": AuthenticationVerdict.NONE,
    "temperror": AuthenticationVerdict.TEMPERROR,
    "permerror": AuthenticationVerdict.PERMERROR,
    "unknown": AuthenticationVerdict.UNKNOWN,
}


class _HrefCollector(HTMLParser):
    """Extract anchor href values without rendering or evaluating HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.hrefs.append(value)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(OrderedDict.fromkeys(value for value in values if value))


def _normalise_address(value: str) -> str | None:
    address = value.strip()
    if "@" not in address or address.count("@") != 1:
        return None
    local, domain = address.rsplit("@", 1)
    if not local or not domain:
        return None
    normalized_domain = _normalise_domain(domain)
    return f"{local}@{normalized_domain}" if normalized_domain else None


def _normalise_domain(value: str) -> str | None:
    domain = value.strip().strip(".[](){}<>,;:\"'").lower()
    if not domain or " " in domain or "@" in domain:
        return None
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        return None
    try:
        return domain.encode("idna").decode("ascii")
    except UnicodeError:
        return None


def _domain_from_address(address: str) -> str | None:
    normalized = _normalise_address(address)
    return normalized.rsplit("@", 1)[1] if normalized else None


def _mailboxes(header_values: Iterable[str]) -> tuple[MailboxAddress, ...]:
    result: list[MailboxAddress] = []
    seen: set[str] = set()
    for display_name, address in getaddresses(list(header_values)):
        normalized = _normalise_address(address)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(MailboxAddress(display_name=display_name.strip() or None, address=normalized))
    return tuple(result)


def _safe_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _decode_part(part: Message) -> bytes:
    try:
        payload = part.get_payload(decode=True)
    except (ValueError, TypeError, UnicodeError):
        payload = None
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode(part.get_content_charset() or "utf-8", errors="replace")
    raw_payload = part.get_payload()
    return raw_payload.encode("utf-8", errors="replace") if isinstance(raw_payload, str) else b""


def _decode_text(part: Message) -> str:
    payload = _decode_part(part)
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, UnicodeError):
        return payload.decode("utf-8", errors="replace")


def _clean_url(value: str) -> str | None:
    cleaned = value.strip().strip("<>{}\"'")
    cleaned = cleaned.rstrip(".,;:!?")
    while cleaned.endswith(")") and cleaned.count("(") < cleaned.count(")"):
        cleaned = cleaned[:-1]
    try:
        parsed = urlsplit(cleaned)
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    return cleaned


def _url_domain(value: str) -> str | None:
    try:
        return _normalise_domain(urlsplit(value).hostname or "")
    except ValueError:
        return None


def _global_ips(value: str) -> tuple[str, ...]:
    result: list[str] = []
    for candidate in _IP_TOKEN_RE.findall(value):
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if address.is_global:
            result.append(str(address))
    return _unique(result)


def _parse_authentication(headers: dict[str, tuple[str, ...]]) -> AuthenticationResults:
    auth_headers = headers.get("authentication-results", ())
    received_spf = headers.get("received-spf", ())
    source_headers = tuple((*auth_headers, *received_spf))

    values: dict[str, AuthenticationVerdict] = {
        "spf": AuthenticationVerdict.UNKNOWN,
        "dkim": AuthenticationVerdict.UNKNOWN,
        "dmarc": AuthenticationVerdict.UNKNOWN,
    }
    joined_auth = "\n".join(auth_headers)
    for mechanism in values:
        match = re.search(rf"\b{mechanism}\s*=\s*([a-z]+)\b", joined_auth, re.I)
        if match:
            values[mechanism] = _AUTH_VALUES.get(match.group(1).lower(), AuthenticationVerdict.UNKNOWN)

    if values["spf"] is AuthenticationVerdict.UNKNOWN:
        for value in received_spf:
            match = re.match(r"\s*([a-z]+)\b", value, re.I)
            if match:
                values["spf"] = _AUTH_VALUES.get(match.group(1).lower(), AuthenticationVerdict.UNKNOWN)
                break

    spf_domain = None
    spf_match = re.search(r"\b(?:smtp\.mailfrom|envelope-from)=<?([^\s;>]+)", "\n".join(source_headers), re.I)
    if spf_match:
        spf_domain = _domain_from_address(spf_match.group(1)) or _normalise_domain(spf_match.group(1))

    dkim_domains = _unique(
        domain
        for domain in (
            _normalise_domain(match.group(1))
            for match in re.finditer(r"\b(?:header\.)?d=([^\s;]+)", joined_auth, re.I)
        )
        if domain
    )
    policy_match = re.search(r"\b(?:policy|p)=([a-z]+)\b", joined_auth, re.I)

    return AuthenticationResults(
        spf=values["spf"],
        dkim=values["dkim"],
        dmarc=values["dmarc"],
        spf_domain=spf_domain,
        dkim_domains=dkim_domains,
        dmarc_policy=policy_match.group(1).lower() if policy_match else None,
        source_headers=source_headers,
    )


def _received_hops(raw_headers: Iterable[str], warnings: list[str]) -> tuple[ReceivedHop, ...]:
    """Return hops in RFC header order: position 0 is the first/topmost Received header."""

    hops: list[ReceivedHop] = []
    for position, raw_header in enumerate(raw_headers):
        from_match = re.search(r"\bfrom\s+([^\s(;]+)", raw_header, re.I)
        by_match = re.search(r"\bby\s+([^\s(;]+)", raw_header, re.I)
        protocol_match = re.search(r"\bwith\s+([A-Za-z0-9-]+)", raw_header, re.I)
        message_match = re.search(r"\bid\s+([^\s;]+)", raw_header, re.I)
        for_match = re.search(r"\bfor\s+<?([^\s;>]+)", raw_header, re.I)
        timestamp = _safe_datetime(raw_header.rsplit(";", 1)[1]) if ";" in raw_header else None
        public_ips = _global_ips(raw_header)

        if not (from_match or by_match or ";" in raw_header):
            warnings.append(f"Received header at position {position} is structurally malformed.")

        hops.append(
            ReceivedHop(
                position=position,
                raw_header=raw_header,
                from_host=from_match.group(1) if from_match else None,
                by_host=by_match.group(1) if by_match else None,
                protocol=protocol_match.group(1) if protocol_match else None,
                message_id=message_match.group(1) if message_match else None,
                envelope_for=_normalise_address(for_match.group(1)) if for_match else None,
                timestamp=timestamp,
                source_ip=public_ips[0] if public_ips else None,
                is_public_ip=bool(public_ips),
            )
        )
    return tuple(hops)


class EmailForensicsParser:
    """Offline implementation of :class:`EmailForensicsService`."""

    def parse(self, raw_email: bytes, *, original_filename: str | None = None) -> ParsedEmail:
        del original_filename  # Filename belongs to the case/upload layer, not parsed email evidence.
        if not isinstance(raw_email, bytes):
            raise TypeError("raw_email must be bytes")

        warnings: list[str] = []
        try:
            message = BytesParser(policy=policy.default).parsebytes(raw_email)
        except (ValueError, TypeError, UnicodeError) as exc:
            message = Message(policy=policy.default)
            warnings.append(f"Email parser recovered from malformed input: {type(exc).__name__}.")

        headers: dict[str, tuple[str, ...]] = {}
        for name, value in message.items():
            key = name.lower()
            headers[key] = (*headers.get(key, ()), str(value))

        sender_values = headers.get("from", ())
        sender_mailboxes = _mailboxes(sender_values)
        reply_to = _mailboxes(headers.get("reply-to", ()))
        recipients_to = _mailboxes(headers.get("to", ()))
        recipients_cc = _mailboxes(headers.get("cc", ()))
        recipients_bcc = _mailboxes(headers.get("bcc", ()))
        sender = sender_mailboxes[0] if sender_mailboxes else None
        if sender is None and sender_values:
            warnings.append("From header did not contain a valid mailbox address.")

        text_bodies: list[str] = []
        html_bodies: list[str] = []
        mime_parts: list[MimePart] = []
        attachments: list[AttachmentEvidence] = []
        attachment_hashes: list[tuple[str, str]] = []

        def visit(part: Message, part_id: str, parent_part_id: str | None) -> None:
            content_type = part.get_content_type().lower()
            disposition = part.get_content_disposition()
            filename = part.get_filename()
            decoded = b"" if part.is_multipart() else _decode_part(part)
            mime_parts.append(
                MimePart(
                    part_id=part_id,
                    parent_part_id=parent_part_id,
                    content_type=content_type,
                    content_disposition=disposition,
                    transfer_encoding=part.get("Content-Transfer-Encoding"),
                    decoded_size_bytes=None if part.is_multipart() else len(decoded),
                    filename=filename,
                )
            )

            if part.is_multipart():
                payload = part.get_payload()
                if isinstance(payload, list):
                    for index, child in enumerate(payload, start=1):
                        visit(child, f"{part_id}.{index}", part_id)
                return

            is_attachment = disposition == "attachment" or (
                bool(filename) and disposition != "inline" and not content_type.startswith("text/")
            )
            if is_attachment:
                attachment_id = f"attachment-{len(attachments) + 1}"
                digest = hashlib.sha256(decoded).hexdigest()
                attachments.append(
                    AttachmentEvidence(
                        attachment_id=attachment_id,
                        filename=filename,
                        content_type=content_type,
                        content_disposition=disposition,
                        content_id=part.get("Content-ID"),
                        size_bytes=len(decoded),
                        sha256=digest,
                        executed=False,
                    )
                )
                attachment_hashes.append((digest, filename or attachment_id))
                if filename and _extension_is_suspicious(filename):
                    warnings.append(f"Attachment {attachment_id} has a suspicious extension: {_filename_extension(filename)}.")
                return

            if content_type == "text/plain":
                text_bodies.append(_decode_text(part))
            elif content_type == "text/html":
                html_bodies.append(_decode_text(part))

        visit(message, "1", None)

        if not headers.get("message-id"):
            warnings.append("Message-ID header is missing.")
        if sender and reply_to:
            sender_domain = _domain_from_address(sender.address)
            reply_domain = _domain_from_address(reply_to[0].address)
            if sender_domain and reply_domain and sender_domain != reply_domain:
                warnings.append("From and Reply-To domains differ.")

        received_hops = _received_hops(headers.get("received", ()), warnings)
        originating_ips = _unique(
            hop.source_ip for hop in received_hops if hop.is_public_ip and hop.source_ip
        )
        authentication = _parse_authentication(headers)
        text_body = "\n\n".join(part for part in text_bodies if part) or None
        html_body = "\n\n".join(part for part in html_bodies if part) or None

        iocs = _collect_iocs(
            headers=headers,
            sender=sender,
            reply_to=reply_to,
            text_body=text_body,
            html_body=html_body,
            public_ips=originating_ips,
            attachment_hashes=attachment_hashes,
        )

        return ParsedEmail(
            original_sha256=hashlib.sha256(raw_email).hexdigest(),
            message_id=headers.get("message-id", (None,))[0],
            sent_at=_safe_datetime(headers.get("date", (None,))[0]),
            sender=sender,
            reply_to=reply_to,
            to=recipients_to,
            cc=recipients_cc,
            bcc=recipients_bcc,
            subject=headers.get("subject", (None,))[0],
            text_body=text_body,
            html_body_untrusted=html_body,
            headers=headers,
            mime_parts=tuple(mime_parts),
            received_hops=received_hops,
            originating_public_ips=originating_ips,
            authentication=authentication,
            iocs=iocs,
            attachments=tuple(attachments),
            parse_warnings=tuple(_unique(warnings)),
        )


def _filename_extension(filename: str) -> str:
    leaf_name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    return f".{leaf_name.rsplit('.', 1)[1].lower()}" if "." in leaf_name else ""


def _extension_is_suspicious(filename: str) -> bool:
    return _filename_extension(filename) in _SUSPICIOUS_EXTENSIONS


def _collect_iocs(
    *,
    headers: dict[str, tuple[str, ...]],
    sender: MailboxAddress | None,
    reply_to: tuple[MailboxAddress, ...],
    text_body: str | None,
    html_body: str | None,
    public_ips: tuple[str, ...],
    attachment_hashes: list[tuple[str, str]],
) -> tuple[ExtractedIOC, ...]:
    observed: OrderedDict[tuple[IOCType, str], dict[str, object]] = OrderedDict()

    def add(ioc_type: IOCType, value: str, normalized: str, source: IOCSource) -> None:
        if not normalized:
            return
        key = (ioc_type, normalized)
        existing = observed.get(key)
        if existing:
            existing["occurrences"] = int(existing["occurrences"]) + 1
            return
        observed[key] = {
            "type": ioc_type,
            "value": value,
            "normalized_value": normalized,
            "source": source,
            "occurrences": 1,
        }

    header_mailboxes = [sender, *reply_to, *_mailboxes(headers.get("return-path", ()))]
    for mailbox in (mailbox for mailbox in header_mailboxes if mailbox):
        add(IOCType.EMAIL_ADDRESS, mailbox.address, mailbox.address, IOCSource.HEADER)
        domain = _domain_from_address(mailbox.address)
        if domain:
            add(IOCType.DOMAIN, domain, domain, IOCSource.HEADER)

    for ip_address in public_ips:
        add(IOCType.IP_ADDRESS, ip_address, ip_address, IOCSource.RECEIVED_HEADER)

    def collect_body(content: str | None, source: IOCSource, urls: Iterable[str]) -> None:
        if not content:
            return
        for email_address in _EMAIL_RE.findall(content):
            normalized = _normalise_address(email_address)
            if normalized:
                add(IOCType.EMAIL_ADDRESS, email_address, normalized, source)
                domain = _domain_from_address(normalized)
                if domain:
                    add(IOCType.DOMAIN, domain, domain, source)
        for raw_url in urls:
            url = _clean_url(raw_url)
            if not url:
                continue
            add(IOCType.URL, raw_url, url, source)
            domain = _url_domain(url)
            if domain:
                add(IOCType.DOMAIN, domain, domain, source)

    collect_body(text_body, IOCSource.BODY_TEXT, _URL_RE.findall(text_body or ""))
    hrefs: list[str] = []
    if html_body:
        collector = _HrefCollector()
        try:
            collector.feed(html_body)
            collector.close()
        except (ValueError, AssertionError):
            pass
        hrefs = collector.hrefs
    collect_body(html_body, IOCSource.BODY_HTML, hrefs)

    for digest, label in attachment_hashes:
        add(IOCType.ATTACHMENT_SHA256, digest, digest, IOCSource.ATTACHMENT_METADATA)

    return tuple(ExtractedIOC(**entry) for entry in observed.values())


def parse_email(raw_email: bytes) -> ParsedEmail:
    """Convenience entry point for future orchestration code."""

    return EmailForensicsParser().parse(raw_email)
