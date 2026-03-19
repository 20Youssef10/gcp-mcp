"""
Gmail Settings MCP Tools

Provides MCP tools for managing Gmail settings including vacation responder and mail filters.
"""

import asyncio
import logging
from typing import Optional, List, Dict

from auth.service_decorator import require_google_service
from auth.scopes import GMAIL_SETTINGS_BASIC_SCOPE, GMAIL_READONLY_SCOPE
from core.server import server
from core.utils import handle_http_errors

logger = logging.getLogger(__name__)


def _format_filter(f: dict) -> str:
    criteria = f.get("criteria", {})
    action = f.get("action", {})
    lines = [f"Filter ID: {f.get('id', 'unknown')}"]
    if criteria:
        if criteria.get("from"):
            lines.append(f"From: {criteria['from']}")
        if criteria.get("to"):
            lines.append(f"To: {criteria['to']}")
        if criteria.get("subject"):
            lines.append(f"Subject: {criteria['subject']}")
        if criteria.get("query"):
            lines.append(f"Has words: {criteria['query']}")
        if criteria.get("negatedQuery"):
            lines.append(f"Does not have: {criteria['negatedQuery']}")
        if criteria.get("hasAttachment"):
            lines.append("Has attachment: yes")
    if action:
        if action.get("addLabelIds"):
            lines.append(f"Add labels: {', '.join(action['addLabelIds'])}")
        if action.get("removeLabelIds"):
            lines.append(f"Remove labels: {', '.join(action['removeLabelIds'])}")
    return "\n".join(lines)


@server.tool()
@handle_http_errors("get_gmail_vacation_responder", is_read_only=True, service_type="gmail")
@require_google_service("gmail", GMAIL_SETTINGS_BASIC_SCOPE)
async def get_gmail_vacation_responder(
    service,
    user_google_email: str,
) -> str:
    """
    Gets the current Gmail vacation (out-of-office) auto-responder settings.

    Args:
        user_google_email (str): The user's Google email address.

    Returns:
        str: Current vacation responder settings including status, subject, and message.
    """
    logger.info(f"[get_gmail_vacation_responder] Getting vacation settings for: {user_google_email}")

    result = await asyncio.to_thread(
        service.users().settings().getVacation(userId="me").execute
    )

    enabled = result.get("enableAutoReply", False)
    lines = [f"Vacation Responder: {'Enabled' if enabled else 'Disabled'}"]

    if result.get("responseSubject"):
        lines.append(f"Subject: {result['responseSubject']}")
    if result.get("responseBodyPlainText"):
        lines.append(f"Message: {result['responseBodyPlainText']}")
    elif result.get("responseBodyHtml"):
        lines.append(f"Message (HTML): {result['responseBodyHtml']}")
    if result.get("startTime"):
        lines.append(f"Start Time: {result['startTime']}")
    if result.get("endTime"):
        lines.append(f"End Time: {result['endTime']}")

    restrict = []
    if result.get("restrictToContacts"):
        restrict.append("contacts only")
    if result.get("restrictToDomain"):
        restrict.append("same domain only")
    if restrict:
        lines.append(f"Send to: {', '.join(restrict)}")

    return "\n".join(lines)


@server.tool()
@handle_http_errors("set_gmail_vacation_responder", service_type="gmail")
@require_google_service("gmail", GMAIL_SETTINGS_BASIC_SCOPE)
async def set_gmail_vacation_responder(
    service,
    user_google_email: str,
    response_subject: str,
    response_body: str,
    start_time_ms: Optional[int] = None,
    end_time_ms: Optional[int] = None,
    restrict_to_contacts: bool = False,
    restrict_to_domain: bool = False,
) -> str:
    """
    Enables and configures the Gmail vacation (out-of-office) auto-responder.

    Args:
        user_google_email (str): The user's Google email address.
        response_subject (str): Subject line of the auto-reply email.
        response_body (str): Plain text body of the auto-reply email.
        start_time_ms (Optional[int]): Start time in milliseconds since epoch. Defaults to now.
        end_time_ms (Optional[int]): End time in milliseconds since epoch. Omit for no end date.
        restrict_to_contacts (bool): Only send auto-replies to people in your contacts.
        restrict_to_domain (bool): Only send auto-replies to people in the same Google Workspace domain.

    Returns:
        str: Confirmation that the vacation responder was enabled.
    """
    logger.info(f"[set_gmail_vacation_responder] Setting vacation responder for: {user_google_email}")

    body: Dict = {
        "enableAutoReply": True,
        "responseSubject": response_subject,
        "responseBodyPlainText": response_body,
        "restrictToContacts": restrict_to_contacts,
        "restrictToDomain": restrict_to_domain,
    }
    if start_time_ms is not None:
        body["startTime"] = str(start_time_ms)
    if end_time_ms is not None:
        body["endTime"] = str(end_time_ms)

    await asyncio.to_thread(
        service.users().settings().updateVacation(userId="me", body=body).execute
    )

    return f"Vacation responder enabled with subject: '{response_subject}'"


@server.tool()
@handle_http_errors("disable_gmail_vacation_responder", service_type="gmail")
@require_google_service("gmail", GMAIL_SETTINGS_BASIC_SCOPE)
async def disable_gmail_vacation_responder(
    service,
    user_google_email: str,
) -> str:
    """
    Disables the Gmail vacation (out-of-office) auto-responder.

    Args:
        user_google_email (str): The user's Google email address.

    Returns:
        str: Confirmation that the vacation responder was disabled.
    """
    logger.info(f"[disable_gmail_vacation_responder] Disabling vacation responder for: {user_google_email}")

    await asyncio.to_thread(
        service.users().settings().updateVacation(userId="me", body={"enableAutoReply": False}).execute
    )

    return "Vacation responder disabled successfully."


@server.tool()
@handle_http_errors("list_gmail_filters", is_read_only=True, service_type="gmail")
@require_google_service("gmail", GMAIL_READONLY_SCOPE)
async def list_gmail_filters(
    service,
    user_google_email: str,
) -> str:
    """
    Lists all Gmail filter rules configured for the account.

    Args:
        user_google_email (str): The user's Google email address.

    Returns:
        str: A formatted list of all Gmail filters with their criteria and actions.
    """
    logger.info(f"[list_gmail_filters] Listing filters for: {user_google_email}")

    result = await asyncio.to_thread(
        service.users().settings().filters().list(userId="me").execute
    )
    filters = result.get("filter", [])

    if not filters:
        return "No filters configured."

    formatted = [_format_filter(f) for f in filters]
    return f"Found {len(formatted)} filter(s):\n\n" + "\n\n---\n\n".join(formatted)


@server.tool()
@handle_http_errors("create_gmail_filter", service_type="gmail")
@require_google_service("gmail", GMAIL_SETTINGS_BASIC_SCOPE)
async def create_gmail_filter(
    service,
    user_google_email: str,
    from_address: Optional[str] = None,
    to_address: Optional[str] = None,
    subject: Optional[str] = None,
    has_words: Optional[str] = None,
    does_not_have: Optional[str] = None,
    has_attachment: bool = False,
    add_label_ids: Optional[List[str]] = None,
    remove_label_ids: Optional[List[str]] = None,
    mark_as_read: bool = False,
    star: bool = False,
    archive: bool = False,
    mark_as_spam: bool = False,
) -> str:
    """
    Creates a new Gmail filter rule that automatically processes matching incoming messages.

    Args:
        user_google_email (str): The user's Google email address.
        from_address (Optional[str]): Filter emails from this address.
        to_address (Optional[str]): Filter emails sent to this address.
        subject (Optional[str]): Filter emails containing this text in the subject.
        has_words (Optional[str]): Filter emails containing these words.
        does_not_have (Optional[str]): Filter emails that do NOT contain these words.
        has_attachment (bool): Filter emails that have attachments.
        add_label_ids (Optional[List[str]]): Label IDs to apply to matching messages.
        remove_label_ids (Optional[List[str]]): Label IDs to remove from matching messages.
        mark_as_read (bool): Automatically mark matching messages as read.
        star (bool): Automatically star matching messages.
        archive (bool): Automatically archive (skip inbox) matching messages.
        mark_as_spam (bool): Automatically mark matching messages as spam.

    Returns:
        str: Confirmation with the new filter's ID.
    """
    logger.info(f"[create_gmail_filter] Creating filter for: {user_google_email}")

    criteria: Dict = {}
    if from_address:
        criteria["from"] = from_address
    if to_address:
        criteria["to"] = to_address
    if subject:
        criteria["subject"] = subject
    if has_words:
        criteria["query"] = has_words
    if does_not_have:
        criteria["negatedQuery"] = does_not_have
    if has_attachment:
        criteria["hasAttachment"] = True

    if not criteria:
        return "At least one filter criterion must be specified."

    action: Dict = {}
    final_add_labels = list(add_label_ids or [])
    final_remove_labels = list(remove_label_ids or [])

    if mark_as_read:
        final_remove_labels.append("UNREAD")
    if star:
        final_add_labels.append("STARRED")
    if archive:
        final_remove_labels.append("INBOX")
    if mark_as_spam:
        final_add_labels.append("SPAM")
        final_remove_labels.append("INBOX")

    if final_add_labels:
        action["addLabelIds"] = list(set(final_add_labels))
    if final_remove_labels:
        action["removeLabelIds"] = list(set(final_remove_labels))

    if not action:
        return "At least one filter action must be specified (add/remove labels, mark as read, star, archive, or mark as spam)."

    body = {"criteria": criteria, "action": action}

    result = await asyncio.to_thread(
        service.users().settings().filters().create(userId="me", body=body).execute
    )

    return f"Filter created successfully. Filter ID: {result.get('id', 'unknown')}"


@server.tool()
@handle_http_errors("delete_gmail_filter", service_type="gmail")
@require_google_service("gmail", GMAIL_SETTINGS_BASIC_SCOPE)
async def delete_gmail_filter(
    service,
    user_google_email: str,
    filter_id: str,
) -> str:
    """
    Deletes a Gmail filter rule.

    Args:
        user_google_email (str): The user's Google email address.
        filter_id (str): The ID of the filter to delete (from list_gmail_filters).

    Returns:
        str: Confirmation that the filter was deleted.
    """
    logger.info(f"[delete_gmail_filter] Deleting filter {filter_id} for: {user_google_email}")

    await asyncio.to_thread(
        service.users().settings().filters().delete(userId="me", id=filter_id).execute
    )

    return f"Filter {filter_id} deleted successfully."
