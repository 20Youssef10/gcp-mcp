"""
Google Keep MCP Tools

This module provides MCP tools for interacting with Google Keep API.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def list_notes_impl(
    service,
    user_google_email: str,
    page_size: int = 20,
) -> str:
    """Implementation for listing notes."""
    notes = await asyncio.to_thread(
        service.notes()
        .list(
            pageSize=page_size,
        )
        .execute
    )

    notes_list = notes.get("notes", [])
    if not notes_list:
        return f"No notes found for {user_google_email}."

    output_parts = [
        f"Found {len(notes_list)} note(s) for {user_google_email}:",
        "",
    ]

    for i, note in enumerate(notes_list, 1):
        title = note.get("title", "Untitled")
        note_id = note.get("name", "").replace("notes/", "")

        created = note.get("createdTime", "Unknown")
        updated = note.get("updatedTime", "Unknown")

        output_parts.append(f"{i}. {title}")
        output_parts.append(f"   ID: {note_id}")
        output_parts.append(f"   Created: {created}")

        if note.get("trashed"):
            output_parts.append("   Status: Trashed")

        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_notes", is_read_only=True, service_type="keep")
@require_google_service("keep", "keep_read")
async def list_notes(
    service,
    user_google_email: str,
    page_size: int = 20,
) -> str:
    """
    Lists the user's notes from Google Keep.

    Args:
        user_google_email (str): The user's Google email address. Required.
        page_size (int): Maximum number of notes to return. Defaults to 20.

    Returns:
        str: Formatted list of notes with titles and timestamps.
    """
    logger.info(
        f"[list_notes] Invoked. Email: '{user_google_email}', Page size: {page_size}"
    )
    return await list_notes_impl(service, user_google_email, page_size)


async def get_note_impl(
    service,
    user_google_email: str,
    note_id: str,
) -> str:
    """Implementation for getting a note."""
    note_name = f"notes/{note_id}"

    note = await asyncio.to_thread(service.notes().get(name=note_name).execute)

    title = note.get("title", "Untitled")
    created = note.get("createdTime", "Unknown")
    updated = note.get("updatedTime", "Unknown")
    trashed = note.get("trashed", False)

    output_parts = [
        f"Note Details for {user_google_email}:",
        f"Title: {title}",
        f"ID: {note_id}",
        f"Created: {created}",
        f"Updated: {updated}",
        f"Trashed: {trashed}",
        "",
    ]

    body_content = note.get("body", {})
    text_content = body_content.get("text", "")
    if text_content:
        output_parts.append("Content:")
        output_parts.append(text_content)
        output_parts.append("")

    attachments = body_content.get("attachments", [])
    if attachments:
        output_parts.append("Attachments:")
        for att in attachments:
            att_id = att.get("id", "Unknown")
            mime_type = att.get("mimeType", "Unknown")
            output_parts.append(f"  - {att_id} ({mime_type})")
        output_parts.append("")

    labels = note.get("labels", [])
    if labels:
        output_parts.append("Labels:")
        for label in labels:
            label_name = label.get("name", "").replace("labels/", "")
            output_parts.append(f"  - {label_name}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_note", is_read_only=True, service_type="keep")
@require_google_service("keep", "keep_read")
async def get_note(
    service,
    user_google_email: str,
    note_id: str,
) -> str:
    """
    Gets a specific note from Google Keep.

    Args:
        user_google_email (str): The user's Google email address. Required.
        note_id (str): The ID of the note to retrieve. Required.

    Returns:
        str: Full details of the note including content.
    """
    logger.info(f"[get_note] Invoked. Email: '{user_google_email}', Note ID: {note_id}")
    return await get_note_impl(service, user_google_email, note_id)


async def create_note_impl(
    service,
    user_google_email: str,
    title: str,
    content: str,
) -> str:
    """Implementation for creating a note."""
    note_body = {
        "title": title,
        "body": {
            "text": content,
        },
    }

    created_note = await asyncio.to_thread(
        service.notes().create(body=note_body).execute
    )

    note_id = created_note.get("name", "").replace("notes/", "")
    created_time = created_note.get("createdTime", "Unknown")

    return (
        f"Successfully created note for {user_google_email}:\n"
        f"Title: {title}\n"
        f"ID: {note_id}\n"
        f"Created: {created_time}"
    )


@server.tool()
@handle_http_errors("create_note", service_type="keep")
@require_google_service("keep", "keep_write")
async def create_note(
    service,
    user_google_email: str,
    title: str,
    content: str,
) -> str:
    """
    Creates a new note in Google Keep.

    Args:
        user_google_email (str): The user's Google email address. Required.
        title (str): The title of the note. Required.
        content (str): The text content of the note. Required.

    Returns:
        str: Confirmation message with the created note details.
    """
    logger.info(
        f"[create_note] Invoked. Email: '{user_google_email}', Title: '{title}'"
    )
    return await create_note_impl(service, user_google_email, title, content)


@server.tool()
@handle_http_errors("update_note", service_type="keep")
@require_google_service("keep", "keep_write")
async def update_note(
    service,
    user_google_email: str,
    note_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
) -> str:
    """
    Updates an existing note in Google Keep.

    Args:
        user_google_email (str): The user's Google email address. Required.
        note_id (str): The ID of the note to update. Required.
        title (Optional[str]): New title for the note.
        content (Optional[str]): New text content for the note.

    Returns:
        str: Confirmation message with updated note details.
    """
    logger.info(
        f"[update_note] Invoked. Email: '{user_google_email}', Note ID: {note_id}"
    )

    if not title and not content:
        raise UserInputError("At least one of 'title' or 'content' must be provided.")

    note_name = f"notes/{note_id}"

    await asyncio.to_thread(service.notes().get(name=note_name).execute)

    note_body: Dict[str, Any] = {"name": note_name}

    if title is not None:
        note_body["title"] = title

    if content is not None:
        note_body["body"] = {"text": content}

    updated_note = await asyncio.to_thread(
        service.notes()
        .update(
            name=note_name,
            body=note_body,
        )
        .execute
    )

    new_title = updated_note.get("title", "Untitled")
    updated_time = updated_note.get("updatedTime", "Unknown")

    text_output = (
        f"Successfully updated note for {user_google_email}:\n"
        f"ID: {note_id}\n"
        f"New Title: {new_title}\n"
        f"Updated: {updated_time}"
    )

    logger.info(f"Successfully updated note: {note_id}")
    return text_output


async def delete_note_impl(
    service,
    user_google_email: str,
    note_id: str,
) -> str:
    """Implementation for deleting a note."""
    note_name = f"notes/{note_id}"

    await asyncio.to_thread(service.notes().delete(name=note_name).execute)

    return f"Successfully deleted note '{note_id}' for {user_google_email}."


@server.tool()
@handle_http_errors("delete_note", service_type="keep")
@require_google_service("keep", "keep_write")
async def delete_note(
    service,
    user_google_email: str,
    note_id: str,
) -> str:
    """
    Permanently deletes a note from Google Keep.

    Args:
        user_google_email (str): The user's Google email address. Required.
        note_id (str): The ID of the note to delete. Required.

    Returns:
        str: Confirmation message of the deletion.
    """
    logger.info(
        f"[delete_note] Invoked. Email: '{user_google_email}', Note ID: {note_id}"
    )
    return await delete_note_impl(service, user_google_email, note_id)


@server.tool()
@handle_http_errors("trash_note", service_type="keep")
@require_google_service("keep", "keep_write")
async def trash_note(
    service,
    user_google_email: str,
    note_id: str,
) -> str:
    """
    Moves a note to the trash in Google Keep.

    Args:
        user_google_email (str): The user's Google email address. Required.
        note_id (str): The ID of the note to trash. Required.

    Returns:
        str: Confirmation message of the trash operation.
    """
    logger.info(
        f"[trash_note] Invoked. Email: '{user_google_email}', Note ID: {note_id}"
    )

    note_name = f"notes/{note_id}"

    note_body: Dict[str, Any] = {
        "name": note_name,
        "trashed": True,
    }

    await asyncio.to_thread(
        service.notes()
        .update(
            name=note_name,
            body=note_body,
        )
        .execute
    )

    text_output = f"Successfully trashed note '{note_id}' for {user_google_email}."

    logger.info(f"Successfully trashed note: {note_id}")
    return text_output
