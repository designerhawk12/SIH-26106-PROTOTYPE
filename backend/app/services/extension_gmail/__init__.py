"""Gmail acquisition services for the Chrome extension integration."""

from .gmail_service import (
    GmailAuthenticationError,
    GmailFetchError,
    complete_authorization,
    create_authorization_url,
    get_raw_message,
    get_service,
    is_authenticated,
    list_recent_messages,
)

__all__ = [
    "GmailAuthenticationError",
    "GmailFetchError",
    "complete_authorization",
    "create_authorization_url",
    "get_raw_message",
    "get_service",
    "is_authenticated",
    "list_recent_messages",
]