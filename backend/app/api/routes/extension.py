"""Developer Gmail endpoints used by the Chrome extension.

These endpoints intentionally keep the extension's existing Gmail workflow
separate from Raj's canonical .eml/case endpoints.

Current prototype flow:

    Chrome extension
        -> /api/v1/extension/auth/status
        -> /api/v1/extension/auth/login
        -> Google OAuth in the host browser
        -> /api/v1/extension/auth/callback
        -> /api/v1/extension/emails
        -> user selects Gmail message
        -> /api/v1/extension/emails/{message_id}/scan
        -> Gmail raw RFC 5322 bytes
        -> canonical Raj analysis orchestrator
        -> extension-compatible response

This is a local/developer prototype integration for one configured Gmail
account. It must not be exposed publicly without an authentication boundary.
"""

from __future__ import annotations

from html import escape
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool

from ...core import AppError
from ...services.extension_gmail import (
    GmailAuthenticationError,
    GmailFetchError,
    complete_authorization,
    create_authorization_url,
    get_raw_message,
    get_service,
    is_authenticated,
    list_recent_messages,
)
from ...services.orchestrator import EmailAnalysisError
from ...services.orchestrator.interfaces import AnalysisOrchestrator
from ..dependencies import get_analysis_orchestrator


router = APIRouter(
    prefix="/api/v1/extension",
    tags=["Chrome Extension"],
)


def _geo_payload(
    *,
    ip: str,
    country: str | None = None,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    isp: str | None = None,
    source: str | None = None,
    ok: bool = False,
) -> dict[str, Any]:
    """Return the geographic shape expected by the existing extension UI."""

    return {
        "ip": ip,
        "country": country,
        "city": city,
        "lat": lat,
        "lon": lon,
        "isp": isp,
        "source": source,
        "ok": ok,
    }


def _geo_by_ip(analysis: Any) -> dict[str, dict[str, Any]]:
    """Index canonical geolocation results by normalized IP address."""

    indexed: dict[str, dict[str, Any]] = {}

    for location in analysis.geolocations:
        ip = location.ip_address

        valid_coordinates = (
            isinstance(location.latitude, (int, float))
            and isinstance(location.longitude, (int, float))
            and not (
                location.latitude == 0
                and location.longitude == 0
            )
        )

        indexed[ip] = _geo_payload(
            ip=ip,
            country=location.country,
            city=location.city,
            lat=location.latitude,
            lon=location.longitude,
            isp=location.isp or location.organization,
            source=location.provider,
            ok=(
                location.status.value == "FOUND"
                and valid_coordinates
            ),
        )

    return indexed


def _extension_result(analysis: Any) -> dict[str, Any]:
    """Adapt canonical EmailAnalysis into the legacy extension response shape."""

    parsed = analysis.parsed_email

    if parsed is None:
        raise AppError(
            status_code=500,
            code="EXTENSION_RESULT_INVALID",
            message="The analysis service returned no parsed email evidence.",
        )

    geo_by_ip = _geo_by_ip(analysis)

    received_chain: list[dict[str, Any]] = []

    for hop in parsed.received_hops:
        hop_geo: dict[str, Any] | None = None

        if hop.source_ip:
            hop_geo = geo_by_ip.get(hop.source_ip)

            if hop_geo is None:
                hop_geo = _geo_payload(
                    ip=hop.source_ip,
                    country=None,
                    city=None,
                    lat=None,
                    lon=None,
                    isp=None,
                    source=None,
                    ok=False,
                )

        received_chain.append(
            {
                "raw": hop.raw_header,
                "from_host": hop.from_host,
                "by_host": hop.by_host,
                "ip": hop.source_ip,
                "geo": hop_geo,
            }
        )

    authentication = {
        "spf": analysis_auth_value(parsed.authentication.spf),
        "dkim": analysis_auth_value(parsed.authentication.dkim),
        "dmarc": analysis_auth_value(parsed.authentication.dmarc),
    }

    from_address = (
        parsed.sender.address
        if parsed.sender is not None
        else None
    )

    reply_to_addresses = [
        mailbox.address
        for mailbox in parsed.reply_to
    ]

    return_path_values = parsed.headers.get(
        "return-path",
        (),
    )

    return_path = (
        return_path_values[0]
        if return_path_values
        else None
    )

    normalized_from = (
        from_address.casefold()
        if from_address
        else None
    )

    reply_to_mismatch = any(
        normalized_from is not None
        and reply_to.casefold() != normalized_from
        for reply_to in reply_to_addresses
    )

    urls = [
        ioc.normalized_value
        for ioc in parsed.iocs
        if ioc.type.value == "URL"
    ]

    domains = [
        ioc.normalized_value
        for ioc in parsed.iocs
        if ioc.type.value == "DOMAIN"
    ]

    body_ips = [
        ioc.normalized_value
        for ioc in parsed.iocs
        if ioc.type.value == "IP_ADDRESS"
        and ioc.source.value not in {"RECEIVED_HEADER"}
    ]

    all_warnings = list(parsed.parse_warnings)
    all_warnings.extend(analysis.warnings)

    auth_ok = (
        authentication["spf"].casefold() == "pass"
        and authentication["dkim"].casefold() == "pass"
        and authentication["dmarc"].casefold() == "pass"
    )

    suspicious = (
        not auth_ok
        or reply_to_mismatch
    )

    return {
        "email": {
            "subject": parsed.subject,
            "from": from_address,
            "to": [
                mailbox.address
                for mailbox in parsed.to
            ],
            "date": (
                parsed.sent_at.isoformat()
                if parsed.sent_at is not None
                else None
            ),
            "message_id": parsed.message_id,
        },
        "headers": {
            "reply_to": (
                ", ".join(reply_to_addresses)
                if reply_to_addresses
                else None
            ),
            "return_path": return_path,
            "reply_to_mismatch": reply_to_mismatch,
        },
        "received_chain": received_chain,
        "authentication": authentication,
        "indicators": {
            "urls": urls,
            "domains": domains,
            "ips": body_ips,
        },
        "geolocation": [
            value
            for value in geo_by_ip.values()
        ],
        "verdict": (
            "suspicious"
            if suspicious
            else "clean"
        ),
        "parse_warnings": list(
            dict.fromkeys(all_warnings)
        ),
    }


def analysis_auth_value(value: Any) -> str:
    """Normalize StrEnum authentication values for the extension UI."""

    enum_value = getattr(value, "value", value)
    return str(enum_value)


@router.get("/auth/status")
async def extension_auth_status() -> dict[str, Any]:
    """Check whether the configured developer Gmail account is authenticated."""

    try:
        authenticated = await run_in_threadpool(
            is_authenticated
        )
    except GmailAuthenticationError:
        return {
            "authenticated": False,
            "error": "Gmail authentication is not configured or could not be established.",
        }
    except Exception:
        return {
            "authenticated": False,
            "error": "The Gmail service is temporarily unavailable.",
        }

    if not authenticated:
        return {
            "authenticated": False,
            "error": "Gmail authentication is required.",
            "login_url": "/api/v1/extension/auth/login",
        }

    return {
        "authenticated": True,
    }


@router.get("/auth/login")
async def extension_auth_login() -> RedirectResponse:
    """Start Gmail OAuth in the user's normal browser."""

    try:
        authorization_url = await run_in_threadpool(
            create_authorization_url
        )
    except GmailAuthenticationError as exc:
        raise AppError(
            status_code=500,
            code="GMAIL_OAUTH_CONFIGURATION_ERROR",
            message=str(exc),
        ) from exc

    return RedirectResponse(
        url=authorization_url,
        status_code=302,
    )


@router.get(
    "/auth/callback",
    response_class=HTMLResponse,
)
async def extension_auth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    """Receive Google's OAuth callback and persist token.json."""

    if error:
        safe_error = escape(error)

        return HTMLResponse(
            content=f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gmail Authorization</title>
</head>
<body>
  <h2>Gmail authorization was not completed.</h2>
  <p>Google returned: <strong>{safe_error}</strong></p>
  <p>You can close this tab and try again.</p>
</body>
</html>
""",
            status_code=400,
        )

    if not code:
        return HTMLResponse(
            content="""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gmail Authorization</title>
</head>
<body>
  <h2>Gmail authorization failed.</h2>
  <p>No authorization code was received.</p>
  <p>You can close this tab and try again.</p>
</body>
</html>
""",
            status_code=400,
        )

    try:
        await run_in_threadpool(
            complete_authorization,
            code=code,
            state=state,
        )
    except GmailAuthenticationError as exc:
        safe_error = escape(str(exc))

        return HTMLResponse(
            content=f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gmail Authorization</title>
</head>
<body>
  <h2>Gmail authorization failed.</h2>
  <p>{safe_error}</p>
  <p>You can close this tab and try again.</p>
</body>
</html>
""",
            status_code=400,
        )

    return HTMLResponse(
        content="""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Gmail Authorization Complete</title>
</head>
<body>
  <h2>Gmail authorization successful.</h2>
  <p>Your Gmail token has been saved.</p>
  <p>You can close this tab and return to the Chrome extension.</p>
</body>
</html>
""",
        status_code=200,
    )


@router.get("/emails")
async def extension_list_emails(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=50,
            description="Maximum number of Gmail messages to return.",
        ),
    ] = 10,
    page_token: Annotated[
        str | None,
        Query(
            description="Optional Gmail pagination token.",
        ),
    ] = None,
) -> dict[str, Any]:
    """Return recent messages from the configured developer Gmail account."""

    try:
        return await run_in_threadpool(
            list_recent_messages,
            limit=limit,
            page_token=page_token,
        )
    except GmailAuthenticationError as exc:
        raise AppError(
            status_code=401,
            code="GMAIL_AUTHENTICATION_REQUIRED",
            message="Gmail authentication is required for the extension.",
        ) from exc
    except GmailFetchError as exc:
        raise AppError(
            status_code=502,
            code="GMAIL_FETCH_FAILED",
            message="Gmail messages could not be retrieved.",
        ) from exc
    except ValueError as exc:
        raise AppError(
            status_code=400,
            code="INVALID_GMAIL_REQUEST",
            message=str(exc),
        ) from exc
    except Exception as exc:
        raise AppError(
            status_code=502,
            code="GMAIL_FETCH_FAILED",
            message="Gmail messages could not be retrieved.",
        ) from exc


@router.post("/emails/{message_id}/scan")
async def extension_scan_email(
    message_id: Annotated[
        str,
        Path(
            min_length=1,
            description="Gmail message ID selected by the extension.",
        ),
    ],
    orchestrator: Annotated[
        AnalysisOrchestrator,
        Depends(get_analysis_orchestrator),
    ],
) -> dict[str, Any]:
    """Retrieve one Gmail message and run Raj's canonical analysis pipeline."""

    clean_message_id = message_id.strip()

    if not clean_message_id:
        raise AppError(
            status_code=400,
            code="INVALID_MESSAGE_ID",
            message="A Gmail message ID is required.",
            field="message_id",
        )

    try:
        raw_email = await run_in_threadpool(
            get_raw_message,
            clean_message_id,
        )
    except GmailAuthenticationError as exc:
        raise AppError(
            status_code=401,
            code="GMAIL_AUTHENTICATION_REQUIRED",
            message="Gmail authentication is required for the extension.",
        ) from exc
    except GmailFetchError as exc:
        raise AppError(
            status_code=502,
            code="GMAIL_FETCH_FAILED",
            message="The selected Gmail message could not be retrieved.",
        ) from exc
    except Exception as exc:
        raise AppError(
            status_code=502,
            code="GMAIL_FETCH_FAILED",
            message="The selected Gmail message could not be retrieved.",
        ) from exc

    try:
        analysis = await orchestrator.analyze(
            raw_email,
            original_filename=f"gmail-{clean_message_id}.eml",
        )
    except EmailAnalysisError as exc:
        raise AppError(
            status_code=422,
            code="INVALID_EMAIL",
            message="The selected Gmail message could not be parsed as an email.",
            field="message_id",
        ) from exc
    except Exception as exc:
        raise AppError(
            status_code=500,
            code="EXTENSION_SCAN_FAILED",
            message="The email analysis service could not complete the scan.",
        ) from exc

    return _extension_result(analysis)