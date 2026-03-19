"""
Gmail Drafts MCP Tools

Provides MCP tools for creating, listing, reading, sending, and deleting Gmail drafts.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Literal

from auth.service_decorator import require_google_service
from auth.scopes import GMAIL_COMPOSE_SCOPE, GMAIL_READONLY_SCOPE, GMAIL_MODIFY_SCOPE
from core.server import server
from core.utils import handle_http_errors
from gmail.gmail_tools import _prepare_gmail_message

logger = logging.getLogger(__name__)


def _format_draft(draft: dict, detailed: bool = False) -> str:
    lines = [f"Draft ID: {draft.get('id', 'Unknown')}"]
    msg = draft.get("message", {})
    payload = msg.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    if headers.get("subject"):
        lines.append(f"Subject: {headers['subject']}")
    if headers.get("to"):
        lines.append(f"To: {headers['to']}")
    if headers.get("date"):
        lines.append(f"Date: {headers['date']}")
    snippet = msg.get("snippet", "")
    if snippet:
        lines.append(f"Snippet: {snippet}")
    return "\n".join(lines)


@server.tool()
@handle_http_errors("create_gmail_draft", service_type="gmail")
@require_google_service("gmail", GMAIL_COMPOSE_SCOPE)
async def create_gmail_draft(
    service,
    user_google_email: str,
    subject: str,
    body: str,
    to: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    body_format: Literal["plain", "html"] = "plain",
    thread_id: Optional[str] = None,
) -> str:
    """
    Creates a Gmail draft message (does not send it).

    Args:
        user_google_email (str): The user's Google email address.
        subject (str): The email subject.
        body (str): The email body.
        to (Optional[str]): Recipient email address.
        cc (Optional[str]): CC email address.
        bcc (Optional[str]): BCC email address.
        body_format (Literal["plain", "html"]): Body content type, 'plain' or 'html'.
        thread_id (Optional[str]): Gmail thread ID to associate the draft with.

    Returns:
        str: Confirmation with the new draft's ID.
    """
    logger.info(f"[create_gmail_draft] Creating draft for: {user_google_email}, subject: {subject}")

    raw_message, thread_id_final, _ = _prepare_gmail_message(
        subject=subject,
        body=body,
        to=to,
        cc=cc,
        bcc=bcc,
        thread_id=thread_id,
        body_format=body_format,
    )

    draft_body: Dict = {"message": {"raw": raw_message}}
    if thread_id_final:
        draft_body["message"]["threadId"] = thread_id_final

    draft = await asyncio.to_thread(
        service.users().drafts().create(userId="me", body=draft_body).execute
    )

    draft_id = draft.get("id", "unknown")
    logger.info(f"[create_gmail_draft] Draft created: {draft_id}")
    return f"Draft created successfully. Draft ID: {draft_id}"


@server.tool()
@handle_http_errors("list_gmail_drafts", is_read_only=True, service_type="gmail")
@require_google_service("gmail", GMAIL_READONLY_SCOPE)
async def list_gmail_drafts(
    service,
    user_google_email: str,
    max_results: int = 20,
    query: Optional[str] = None,
) -> str:
    """
    Lists Gmail draft messages.

    Args:
        user_google_email (str): The user's Google email address.
        max_results (int): Maximum number of drafts to return (default 20, max 500).
        query (Optional[str]): Optional Gmail search query to filter drafts (e.g. 'subject:meeting').

    Returns:
        str: A formatted list of draft messages.
    """
    logger.info(f"[list_gmail_drafts] Listing drafts for: {user_google_email}")

    max_results = min(max(1, max_results), 500)
    params = {"userId": "me", "maxResults": max_results, "includeSpamTrash": False}
    if query:
        params["q"] = query

    result = await asyncio.to_thread(service.users().drafts().list(**params).execute)
    drafts = result.get("drafts", [])

    if not drafts:
        return "No drafts found."

    detailed_drafts = []
    for d in drafts:
        detail = await asyncio.to_thread(
            service.users().drafts().get(userId="me", id=d["id"], format="metadata").execute
        )
        detailed_drafts.append(_format_draft(detail))

    return f"Found {len(detailed_drafts)} draft(s):\n\n" + "\n\n---\n\n".join(detailed_drafts)


@server.tool()
@handle_http_errors("get_gmail_draft", is_read_only=True, service_type="gmail")
@require_google_service("gmail", GMAIL_READONLY_SCOPE)
async def get_gmail_draft(
    service,
    user_google_email: str,
    draft_id: str,
) -> str:
    """
    Gets the full details of a specific Gmail draft.

    Args:
        user_google_email (str): The user's Google email address.
        draft_id (str): The draft ID to retrieve.

    Returns:
        str: Full details of the draft message.
    """
    logger.info(f"[get_gmail_draft] Getting draft {draft_id} for: {user_google_email}")

    draft = await asyncio.to_thread(
        service.users().drafts().get(userId="me", id=draft_id, format="full").execute
    )

    return _format_draft(draft, detailed=True)


@server.tool()
@handle_http_errors("send_gmail_draft", service_type="gmail")
@require_google_service("gmail", GMAIL_COMPOSE_SCOPE)
async def send_gmail_draft(
    service,
    user_google_email: str,
    draft_id: str,
) -> str:
    """
    Sends an existing Gmail draft.

    Args:
        user_google_email (str): The user's Google email address.
        draft_id (str): The ID of the draft to send.

    Returns:
        str: Confirmation with the sent message's ID.
    """
    logger.info(f"[send_gmail_draft] Sending draft {draft_id} for: {user_google_email}")

    result = await asyncio.to_thread(
        service.users().drafts().send(userId="me", body={"id": draft_id}).execute
    )

    message_id = result.get("id", "unknown")
    thread_id = result.get("threadId", "")
    return f"Draft sent successfully. Message ID: {message_id}, Thread ID: {thread_id}"


@server.tool()
@handle_http_errors("delete_gmail_draft", service_type="gmail")
@require_google_service("gmail", GMAIL_MODIFY_SCOPE)
async def delete_gmail_draft(
    service,
    user_google_email: str,
    draft_id: str,
) -> str:
    """
    Permanently deletes a Gmail draft.

    Args:
        user_google_email (str): The user's Google email address.
        draft_id (str): The ID of the draft to delete.

    Returns:
        str: Confirmation that the draft was deleted.
    """
    logger.info(f"[delete_gmail_draft] Deleting draft {draft_id} for: {user_google_email}")

    await asyncio.to_thread(
        service.users().drafts().delete(userId="me", id=draft_id).execute
    )

    return f"Draft {draft_id} deleted successfully."
