"""Email-forensics contracts."""

from .interfaces import EmailForensicsService

__all__ = ["EmailForensicsService"]
"""Safe, offline RFC/MIME email parsing service."""

from .parser import EmailForensicsParser, parse_email

__all__ = ["EmailForensicsParser", "parse_email"]
