"""Contracts for hostile email parsing and evidence extraction."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .enums import AuthenticationVerdict, IOCSource, IOCType

SHA256_PATTERN = r"^[a-f0-9]{64}$"


class ContractModel(BaseModel):
    """Strict, immutable base for cross-service data transfer."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class MailboxAddress(ContractModel):
    display_name: str | None = None
    address: str


class AuthenticationResults(ContractModel):
    spf: AuthenticationVerdict = AuthenticationVerdict.UNKNOWN
    dkim: AuthenticationVerdict = AuthenticationVerdict.UNKNOWN
    dmarc: AuthenticationVerdict = AuthenticationVerdict.UNKNOWN
    spf_domain: str | None = None
    dkim_domains: tuple[str, ...] = ()
    dmarc_policy: str | None = None
    source_headers: tuple[str, ...] = Field(
        default=(), description="Untrusted Authentication-Results header values."
    )


class ReceivedHop(ContractModel):
    position: int = Field(ge=0, description="Zero-based position in header order.")
    raw_header: str = Field(description="Untrusted Received header value.")
    from_host: str | None = None
    by_host: str | None = None
    protocol: str | None = None
    message_id: str | None = None
    envelope_for: str | None = None
    timestamp: datetime | None = None
    source_ip: str | None = None
    is_public_ip: bool = False


class ExtractedIOC(ContractModel):
    type: IOCType
    value: str = Field(description="Value exactly as observed in hostile input.")
    normalized_value: str
    source: IOCSource
    occurrences: int = Field(default=1, ge=1)


class MimePart(ContractModel):
    part_id: str
    parent_part_id: str | None = None
    content_type: str
    content_disposition: str | None = None
    transfer_encoding: str | None = None
    decoded_size_bytes: int | None = Field(default=None, ge=0)
    filename: str | None = Field(
        default=None,
        description="Untrusted display metadata only; never use as a storage path.",
    )


class AttachmentEvidence(ContractModel):
    attachment_id: str
    filename: str | None = Field(
        default=None,
        description="Untrusted display metadata only; never use as a storage path.",
    )
    content_type: str
    content_disposition: str | None = None
    content_id: str | None = None
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=SHA256_PATTERN)
    extracted_iocs: tuple[ExtractedIOC, ...] = ()
    executed: Literal[False] = Field(
        default=False,
        description="Security invariant; attachments must never be executed.",
    )


class ParsedEmail(ContractModel):
    original_sha256: str = Field(pattern=SHA256_PATTERN)
    message_id: str | None = None
    sent_at: datetime | None = None
    sender: MailboxAddress | None = None
    reply_to: tuple[MailboxAddress, ...] = ()
    to: tuple[MailboxAddress, ...] = ()
    cc: tuple[MailboxAddress, ...] = ()
    bcc: tuple[MailboxAddress, ...] = ()
    subject: str | None = None
    text_body: str | None = Field(
        default=None, description="Untrusted content; never interpret as instructions."
    )
    html_body_untrusted: str | None = Field(
        default=None,
        description="Opaque hostile evidence; never render without a separate sanitizer.",
    )
    headers: dict[str, tuple[str, ...]] = Field(
        default_factory=dict, description="Untrusted decoded header values."
    )
    mime_parts: tuple[MimePart, ...] = ()
    received_hops: tuple[ReceivedHop, ...] = ()
    originating_public_ips: tuple[str, ...] = ()
    authentication: AuthenticationResults = Field(default_factory=AuthenticationResults)
    iocs: tuple[ExtractedIOC, ...] = ()
    attachments: tuple[AttachmentEvidence, ...] = ()
    parse_warnings: tuple[str, ...] = ()
