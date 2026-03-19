"""
Gmail Labels MCP Tools

Provides MCP tools for listing, creating, updating, and deleting Gmail labels.
"""

import asyncio
import logging
from typing import Optional, Literal

from auth.service_decorator import require_google_service
from auth.scopes import GMAIL_LABELS_SCOPE, GMAIL_READONLY_SCOPE
from core.server import server
from core.utils import handle_http_errors

logger = logging.getLogger(__name__)

_SYSTEM_LABEL_IDS = {
    "INBOX", "SENT", "TRASH", "SPAM", "DRAFT", "STARRED", "UNREAD",
    "IMPORTANT", "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES", "CATEGORY_FORUMS",
}


def _format_label(label: dict) -> str:
    lines = [
        f"Label ID: {label.get('id', '')}",
        f"Name: {label.get('name', '')}",
        f"Type: {label.get('type', 'user')}",
    ]
    if label.get("messagesTotal") is not None:
        lines.append(f"Total Messages: {label['messagesTotal']}")
    if label.get("messagesUnread") is not None:
        lines.append(f"Unread Messages: {label['messagesUnread']}")
    visibility = label.get("labelListVisibility", "")
    if visibility:
        lines.append(f"List Visibility: {visibility}")
    return "\n".join(lines)


@server.tool()
@handle_http_errors("list_gmail_labels", is_read_only=True, service_type="gmail")
@require_google_service("gmail", GMAIL_READONLY_SCOPE)
async def list_gmail_labels(
    service,
    user_google_email: str,
    include_system_labels: bool = False,
) -> str:
    """
    Lists all Gmail labels for the user.

    Args:
        user_google_email (str): The user's Google email address.
        include_system_labels (bool): Whether to include built-in system labels like INBOX, SENT, etc.
                                       Defaults to False (user-created labels only).

    Returns:
        str: A formatted list of Gmail labels with their IDs and message counts.
    """
    logger.info(f"[list_gmail_labels] Listing labels for: {user_google_email}")

    result = await asyncio.to_thread(
        service.users().labels().list(userId="me").execute
    )
    labels = result.get("labels", [])

    if not include_system_labels:
        labels = [l for l in labels if l.get("type") != "system"]

    if not labels:
        return "No labels found."

    formatted = [_format_label(l) for l in labels]
    return f"Found {len(formatted)} label(s):\n\n" + "\n\n---\n\n".join(formatted)


@server.tool()
@handle_http_errors("create_gmail_label", service_type="gmail")
@require_google_service("gmail", GMAIL_LABELS_SCOPE)
async def create_gmail_label(
    service,
    user_google_email: str,
    name: str,
    label_list_visibility: Literal["labelShow", "labelShowIfUnread", "labelHide"] = "labelShow",
    message_list_visibility: Literal["show", "hide"] = "show",
) -> str:
    """
    Creates a new Gmail label.

    Args:
        user_google_email (str): The user's Google email address.
        name (str): The display name of the new label (e.g. 'Work/Projects').
        label_list_visibility (str): Visibility in the label list.
            'labelShow' = always visible, 'labelShowIfUnread' = only when unread, 'labelHide' = hidden.
        message_list_visibility (str): Visibility of messages with this label in the message list.
            'show' = visible, 'hide' = hidden.

    Returns:
        str: Confirmation with the new label's ID and name.
    """
    logger.info(f"[create_gmail_label] Creating label '{name}' for: {user_google_email}")

    label_body = {
        "name": name,
        "labelListVisibility": label_list_visibility,
        "messageListVisibility": message_list_visibility,
    }

    label = await asyncio.to_thread(
        service.users().labels().create(userId="me", body=label_body).execute
    )

    return f"Label created. ID: {label.get('id')}, Name: {label.get('name')}"


@server.tool()
@handle_http_errors("update_gmail_label", service_type="gmail")
@require_google_service("gmail", GMAIL_LABELS_SCOPE)
async def update_gmail_label(
    service,
    user_google_email: str,
    label_id: str,
    new_name: Optional[str] = None,
    label_list_visibility: Optional[Literal["labelShow", "labelShowIfUnread", "labelHide"]] = None,
    message_list_visibility: Optional[Literal["show", "hide"]] = None,
) -> str:
    """
    Updates an existing Gmail label's name or visibility settings.

    Args:
        user_google_email (str): The user's Google email address.
        label_id (str): The ID of the label to update.
        new_name (Optional[str]): New display name for the label.
        label_list_visibility (Optional[str]): New label list visibility setting.
        message_list_visibility (Optional[str]): New message list visibility setting.

    Returns:
        str: Confirmation of the updated label.
    """
    logger.info(f"[update_gmail_label] Updating label {label_id} for: {user_google_email}")

    if label_id in _SYSTEM_LABEL_IDS:
        return f"Cannot update system label '{label_id}'."

    label_body: dict = {}
    if new_name is not None:
        label_body["name"] = new_name
    if label_list_visibility is not None:
        label_body["labelListVisibility"] = label_list_visibility
    if message_list_visibility is not None:
        label_body["messageListVisibility"] = message_list_visibility

    if not label_body:
        return "No changes specified. Provide at least one field to update."

    updated = await asyncio.to_thread(
        service.users().labels().patch(userId="me", id=label_id, body=label_body).execute
    )

    return f"Label updated. ID: {updated.get('id')}, Name: {updated.get('name')}"


@server.tool()
@handle_http_errors("delete_gmail_label", service_type="gmail")
@require_google_service("gmail", GMAIL_LABELS_SCOPE)
async def delete_gmail_label(
    service,
    user_google_email: str,
    label_id: str,
) -> str:
    """
    Permanently deletes a Gmail label. Messages with this label will not be deleted.

    Args:
        user_google_email (str): The user's Google email address.
        label_id (str): The ID of the label to delete.

    Returns:
        str: Confirmation that the label was deleted.
    """
    logger.info(f"[delete_gmail_label] Deleting label {label_id} for: {user_google_email}")

    if label_id in _SYSTEM_LABEL_IDS:
        return f"Cannot delete system label '{label_id}'."

    await asyncio.to_thread(
        service.users().labels().delete(userId="me", id=label_id).execute
    )

    return f"Label {label_id} deleted successfully. Associated messages were not deleted."
