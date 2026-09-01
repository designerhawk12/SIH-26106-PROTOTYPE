"""Email-forensics service boundary owned by Developer 2."""

from typing import Protocol, runtime_checkable

from ...schemas import ParsedEmail


@runtime_checkable
class EmailForensicsService(Protocol):
    """Parse untrusted bytes without executing content or fetching resources."""

    def parse(self, raw_email: bytes, *, original_filename: str | None = None) -> ParsedEmail:
        """Return normalized forensic evidence for a validated upload."""
        ...

