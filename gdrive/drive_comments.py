"""
Google Drive Comments MCP Tools

Provides MCP tools for listing, adding, replying to, resolving, and deleting
comments on Google Drive files.
"""

import asyncio
import logging
from typing import Optional

from auth.service_decorator import require_google_service
from auth.scopes import DRIVE_SCOPE, DRIVE_READONLY_SCOPE
from core.server import server
from core.utils import handle_http_errors

logger = logging.getLogger(__name__)

_COMMENT_FIELDS = "id,content,createdTime,modifiedTime,author,resolved,replies,deleted"


def _format_author(author: dict) -> str:
    name = author.get("displayName", "Unknown")
    email = author.get("emailAddress", "")
    return f"{name} ({email})" if email else name


def _format_comment(comment: dict, include_replies: bool = True) -> str:
    lines = [
        f"Comment ID: {comment.get('id', '')}",
        f"Author: {_format_author(comment.get('author', {}))}",
        f"Created: {comment.get('createdTime', '')}",
    ]
    if comment.get("modifiedTime") != comment.get("createdTime"):
        lines.append(f"Modified: {comment.get('modifiedTime', '')}")
    if comment.get("resolved"):
        lines.append("Status: Resolved")
    if comment.get("deleted"):
        lines.append("Status: Deleted")
    content = comment.get("content", "")
    if content:
        lines.append(f"Content: {content}")

    if include_replies:
        replies = comment.get("replies", [])
        active_replies = [r for r in replies if not r.get("deleted")]
        if active_replies:
            lines.append(f"\n  Replies ({len(active_replies)}):")
            for reply in active_replies:
                lines.append(f"    - {_format_author(reply.get('author', {}))}: {reply.get('content', '')}")

    return "\n".join(lines)


@server.tool()
@handle_http_errors("list_drive_file_comments", is_read_only=True, service_type="drive")
@require_google_service("drive", DRIVE_READONLY_SCOPE)
async def list_drive_file_comments(
    service,
    user_google_email: str,
    file_id: str,
    include_resolved: bool = False,
    max_results: int = 20,
) -> str:
    """
    Lists comments on a Google Drive file (Docs, Sheets, Slides, etc.).

    Args:
        user_google_email (str): The user's Google email address.
        file_id (str): The ID of the Drive file to list comments for.
        include_resolved (bool): Whether to include resolved comments (default False).
        max_results (int): Maximum number of comments to return (default 20, max 100).

    Returns:
        str: A formatted list of comments with authors, content, and replies.
    """
    logger.info(f"[list_drive_file_comments] Listing comments on file {file_id} for: {user_google_email}")

    max_results = min(max(1, max_results), 100)
    params = {
        "fileId": file_id,
        "fields": f"comments({_COMMENT_FIELDS}),nextPageToken",
        "pageSize": max_results,
        "includeDeleted": False,
    }

    result = await asyncio.to_thread(
        service.comments().list(**params).execute
    )
    comments = result.get("comments", [])

    if not include_resolved:
        comments = [c for c in comments if not c.get("resolved")]

    if not comments:
        label = "resolved or unresolved" if include_resolved else "unresolved"
        return f"No {label} comments found on this file."

    formatted = [_format_comment(c) for c in comments]
    return f"Found {len(formatted)} comment(s):\n\n" + "\n\n---\n\n".join(formatted)


@server.tool()
@handle_http_errors("add_drive_file_comment", service_type="drive")
@require_google_service("drive", DRIVE_SCOPE)
async def add_drive_file_comment(
    service,
    user_google_email: str,
    file_id: str,
    content: str,
) -> str:
    """
    Adds a new comment to a Google Drive file.

    Args:
        user_google_email (str): The user's Google email address.
        file_id (str): The ID of the Drive file to comment on.
        content (str): The text content of the comment.

    Returns:
        str: Confirmation with the new comment's ID and content.
    """
    logger.info(f"[add_drive_file_comment] Adding comment to file {file_id} for: {user_google_email}")

    comment = await asyncio.to_thread(
        service.comments().create(
            fileId=file_id,
            body={"content": content},
            fields=_COMMENT_FIELDS,
        ).execute
    )

    return f"Comment added. Comment ID: {comment.get('id')}\nContent: {comment.get('content')}"


@server.tool()
@handle_http_errors("reply_to_drive_comment", service_type="drive")
@require_google_service("drive", DRIVE_SCOPE)
async def reply_to_drive_comment(
    service,
    user_google_email: str,
    file_id: str,
    comment_id: str,
    content: str,
) -> str:
    """
    Replies to an existing comment on a Google Drive file.

    Args:
        user_google_email (str): The user's Google email address.
        file_id (str): The ID of the Drive file.
        comment_id (str): The ID of the comment to reply to.
        content (str): The text content of the reply.

    Returns:
        str: Confirmation with the new reply's ID.
    """
    logger.info(f"[reply_to_drive_comment] Replying to comment {comment_id} on file {file_id} for: {user_google_email}")

    reply = await asyncio.to_thread(
        service.replies().create(
            fileId=file_id,
            commentId=comment_id,
            body={"content": content},
            fields="id,content,author,createdTime",
        ).execute
    )

    return f"Reply added. Reply ID: {reply.get('id')}\nContent: {reply.get('content')}"


@server.tool()
@handle_http_errors("resolve_drive_comment", service_type="drive")
@require_google_service("drive", DRIVE_SCOPE)
async def resolve_drive_comment(
    service,
    user_google_email: str,
    file_id: str,
    comment_id: str,
    resolved: bool = True,
) -> str:
    """
    Resolves or re-opens a comment on a Google Drive file.

    Args:
        user_google_email (str): The user's Google email address.
        file_id (str): The ID of the Drive file.
        comment_id (str): The ID of the comment to resolve or re-open.
        resolved (bool): True to resolve the comment, False to re-open it (default True).

    Returns:
        str: Confirmation of the comment's new status.
    """
    logger.info(f"[resolve_drive_comment] {'Resolving' if resolved else 'Re-opening'} comment {comment_id} for: {user_google_email}")

    updated = await asyncio.to_thread(
        service.comments().update(
            fileId=file_id,
            commentId=comment_id,
            body={"resolved": resolved},
            fields="id,resolved",
        ).execute
    )

    status = "resolved" if updated.get("resolved") else "re-opened"
    return f"Comment {comment_id} {status} successfully."


@server.tool()
@handle_http_errors("delete_drive_comment", service_type="drive")
@require_google_service("drive", DRIVE_SCOPE)
async def delete_drive_comment(
    service,
    user_google_email: str,
    file_id: str,
    comment_id: str,
) -> str:
    """
    Permanently deletes a comment from a Google Drive file.

    Args:
        user_google_email (str): The user's Google email address.
        file_id (str): The ID of the Drive file.
        comment_id (str): The ID of the comment to delete.

    Returns:
        str: Confirmation that the comment was deleted.
    """
    logger.info(f"[delete_drive_comment] Deleting comment {comment_id} on file {file_id} for: {user_google_email}")

    await asyncio.to_thread(
        service.comments().delete(fileId=file_id, commentId=comment_id).execute
    )

    return f"Comment {comment_id} deleted successfully."
