"""
Google Photos MCP Tools

This module provides MCP tools for interacting with Google Photos API.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def list_albums_impl(
    service,
    user_google_email: str,
    page_size: int = 20,
) -> str:
    """Implementation for listing albums."""
    albums = await asyncio.to_thread(
        service.albums()
        .list(
            pageSize=page_size,
        )
        .execute
    )

    albums_list = albums.get("albums", [])
    if not albums_list:
        return f"No albums found for {user_google_email}."

    output_parts = [
        f"Found {len(albums_list)} album(s) for {user_google_email}:",
        "",
    ]

    for i, album in enumerate(albums_list, 1):
        title = album.get("title", "Untitled")
        album_id = album.get("id", "")
        total_photos = album.get("totalMediaItemsCount", "0")

        created = album.get("createdAt", "Unknown")
        updated = album.get("updatedAt", "Unknown")

        cover_photo = album.get("coverPhotoBaseUrl", "")

        output_parts.append(f"{i}. {title}")
        output_parts.append(f"   ID: {album_id}")
        output_parts.append(f"   Photos: {total_photos}")
        output_parts.append(f"   Created: {created}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_albums", is_read_only=True, service_type="photos")
@require_google_service("photos", "photos_read")
async def list_albums(
    service,
    user_google_email: str,
    page_size: int = 20,
) -> str:
    """
    Lists the user's photo albums from Google Photos.

    Args:
        user_google_email (str): The user's Google email address. Required.
        page_size (int): Maximum number of albums to return. Defaults to 20.

    Returns:
        str: Formatted list of albums with titles and photo counts.
    """
    logger.info(
        f"[list_albums] Invoked. Email: '{user_google_email}', Page size: {page_size}"
    )
    return await list_albums_impl(service, user_google_email, page_size)


async def get_album_impl(
    service,
    user_google_email: str,
    album_id: str,
    page_size: int = 20,
) -> str:
    """Implementation for getting an album."""
    album = await asyncio.to_thread(
        service.albums()
        .get(
            albumId=album_id,
            pageSize=page_size,
        )
        .execute
    )

    title = album.get("title", "Untitled")
    total_photos = album.get("totalMediaItemsCount", "0")
    created = album.get("createdAt", "Unknown")
    updated = album.get("updatedAt", "Unknown")

    output_parts = [
        f"Album Details for {user_google_email}:",
        f"Title: {title}",
        f"ID: {album_id}",
        f"Total Photos: {total_photos}",
        f"Created: {created}",
        f"Updated: {updated}",
        "",
    ]

    media_items = album.get("mediaItems", [])
    if media_items:
        output_parts.append(f"Media Items ({len(media_items)} shown):")
        for i, item in enumerate(media_items[:10], 1):
            item_id = item.get("id", "")
            filename = item.get("filename", "Unknown")
            mime_type = item.get("mimeType", "Unknown")
            output_parts.append(f"  {i}. {filename} ({mime_type})")
            output_parts.append(f"     ID: {item_id}")
        if len(media_items) > 10:
            output_parts.append(f"  ... and {len(media_items) - 10} more")
    else:
        output_parts.append("No media items in this album yet.")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_album", is_read_only=True, service_type="photos")
@require_google_service("photos", "photos_read")
async def get_album(
    service,
    user_google_email: str,
    album_id: str,
    page_size: int = 20,
) -> str:
    """
    Gets details of a specific album from Google Photos.

    Args:
        user_google_email (str): The user's Google email address. Required.
        album_id (str): The ID of the album. Required.
        page_size (int): Number of media items to return. Defaults to 20.

    Returns:
        str: Full details of the album including media items.
    """
    logger.info(
        f"[get_album] Invoked. Email: '{user_google_email}', Album ID: {album_id}"
    )
    return await get_album_impl(service, user_google_email, album_id, page_size)


async def create_album_impl(
    service,
    user_google_email: str,
    title: str,
) -> str:
    """Implementation for creating an album."""
    album_body = {
        "album": {
            "title": title,
        }
    }

    created_album = await asyncio.to_thread(
        service.albums().create(body=album_body).execute
    )

    album_id = created_album.get("id", "")
    created = created_album.get("createdAt", "Unknown")

    text_output = (
        f"Successfully created album for {user_google_email}:\n"
        f"Title: {title}\n"
        f"ID: {album_id}\n"
        f"Created: {created}"
    )

    logger.info(f"Successfully created album: {album_id}")
    return text_output


@server.tool()
@handle_http_errors("create_album", service_type="photos")
@require_google_service("photos", "photos_write")
async def create_album(
    service,
    user_google_email: str,
    title: str,
) -> str:
    """
    Creates a new album in Google Photos.

    Args:
        user_google_email (str): The user's Google email address. Required.
        title (str): The title for the new album. Required.

    Returns:
        str: Confirmation message with the created album details.
    """
    logger.info(
        f"[create_album] Invoked. Email: '{user_google_email}', Title: '{title}'"
    )
    return await create_album_impl(service, user_google_email, title)


async def add_media_to_album_impl(
    service,
    user_google_email: str,
    album_id: str,
    media_item_ids: List[str],
) -> str:
    """Implementation for adding media to an album."""
    if not media_item_ids:
        raise UserInputError("At least one media_item_id must be provided.")

    batch_body = {
        "mediaItemIds": media_item_ids,
    }

    result = await asyncio.to_thread(
        service.albums()
        .addEnrichment(
            albumId=album_id,
            body=batch_body,
        )
        .execute
    )

    text_output = (
        f"Successfully added {len(media_item_ids)} media item(s) to album '{album_id}' "
        f"for {user_google_email}."
    )

    logger.info(f"Successfully added media to album: {album_id}")
    return text_output


@server.tool()
@handle_http_errors("add_media_to_album", service_type="photos")
@require_google_service("photos", "photos_write")
async def add_media_to_album(
    service,
    user_google_email: str,
    album_id: str,
    media_item_ids: List[str],
) -> str:
    """
    Adds media items to an album in Google Photos.

    Args:
        user_google_email (str): The user's Google email address. Required.
        album_id (str): The ID of the album to add items to. Required.
        media_item_ids (List[str]): List of media item IDs to add. Required.

    Returns:
        str: Confirmation message of the added items.
    """
    logger.info(
        f"[add_media_to_album] Invoked. Email: '{user_google_email}', "
        f"Album: {album_id}, Items: {len(media_item_ids)}"
    )
    return await add_media_to_album_impl(
        service, user_google_email, album_id, media_item_ids
    )


async def list_media_items_impl(
    service,
    user_google_email: str,
    page_size: int = 20,
    album_id: Optional[str] = None,
) -> str:
    """Implementation for listing media items."""
    if album_id:
        album = await asyncio.to_thread(
            service.albums().get(albumId=album_id, pageSize=page_size).execute
        )
        media_items = album.get("mediaItems", [])
        album_title = album.get("title", "Unknown")
    else:
        result = await asyncio.to_thread(
            service.mediaItems().list(pageSize=page_size).execute
        )
        media_items = result.get("mediaItems", [])
        album_title = "All Photos"

    if not media_items:
        return f"No media items found for {user_google_email}."

    output_parts = [
        f"Found {len(media_items)} media item(s) in '{album_title}' for {user_google_email}:",
        "",
    ]

    for i, item in enumerate(media_items, 1):
        item_id = item.get("id", "")
        filename = item.get("filename", "Unknown")
        mime_type = item.get("mimeType", "Unknown")
        created = item.get("createdAt", "Unknown")

        base_url = item.get("baseUrl", "")
        if base_url:
            if mime_type.startswith("image"):
                preview_url = f"{base_url}=w320-h320"
            elif mime_type.startswith("video"):
                preview_url = f"{base_url}=w320-h320"
            else:
                preview_url = base_url
        else:
            preview_url = "N/A"

        output_parts.append(f"{i}. {filename}")
        output_parts.append(f"   ID: {item_id}")
        output_parts.append(f"   Type: {mime_type}")
        output_parts.append(f"   Created: {created}")
        output_parts.append(
            f"   Preview: {preview_url[:80]}..."
            if len(preview_url) > 80
            else f"   Preview: {preview_url}"
        )
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_media_items", is_read_only=True, service_type="photos")
@require_google_service("photos", "photos_read")
async def list_media_items(
    service,
    user_google_email: str,
    page_size: int = 20,
    album_id: Optional[str] = None,
) -> str:
    """
    Lists media items from Google Photos.

    Args:
        user_google_email (str): The user's Google email address. Required.
        page_size (int): Maximum number of items to return. Defaults to 20.
        album_id (Optional[str]): If provided, lists items from specific album.

    Returns:
        str: Formatted list of media items.
    """
    logger.info(
        f"[list_media_items] Invoked. Email: '{user_google_email}', "
        f"Page size: {page_size}, Album: {album_id}"
    )
    return await list_media_items_impl(service, user_google_email, page_size, album_id)


async def get_media_item_impl(
    service,
    user_google_email: str,
    media_item_id: str,
) -> str:
    """Implementation for getting a media item."""
    media_item = await asyncio.to_thread(
        service.mediaItems().get(mediaItemId=media_item_id).execute
    )

    filename = media_item.get("filename", "Unknown")
    mime_type = media_item.get("mimeType", "Unknown")
    created = media_item.get("createdAt", "Unknown")
    width = media_item.get("width", "Unknown")
    height = media_item.get("height", "Unknown")

    base_url = media_item.get("baseUrl", "")

    output_parts = [
        f"Media Item Details for {user_google_email}:",
        f"Filename: {filename}",
        f"ID: {media_item_id}",
        f"Type: {mime_type}",
        f"Created: {created}",
        f"Dimensions: {width} x {height}",
        "",
    ]

    if base_url:
        if mime_type.startswith("image"):
            output_parts.append("Download URLs:")
            output_parts.append(f"  Original: {base_url}")
            output_parts.append(f"  2048px: {base_url}=w2048-h2048")
            output_parts.append(f"  1024px: {base_url}=w1024-h1024")
            output_parts.append(f"  512px: {base_url}=w512-h512")
        elif mime_type.startswith("video"):
            output_parts.append("Video URLs:")
            output_parts.append(f"  Base: {base_url}")
        else:
            output_parts.append(f"Download URL: {base_url}")

    metadata = media_item.get("mediaMetadata", {})
    if metadata:
        camera_make = metadata.get("cameraMake", "")
        camera_model = metadata.get("cameraModel", "")
        if camera_make or camera_model:
            output_parts.append(f"Camera: {camera_make} {camera_model}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_media_item", is_read_only=True, service_type="photos")
@require_google_service("photos", "photos_read")
async def get_media_item(
    service,
    user_google_email: str,
    media_item_id: str,
) -> str:
    """
    Gets details of a specific media item from Google Photos.

    Args:
        user_google_email (str): The user's Google email address. Required.
        media_item_id (str): The ID of the media item. Required.

    Returns:
        str: Full details of the media item.
    """
    logger.info(
        f"[get_media_item] Invoked. Email: '{user_google_email}', Media ID: {media_item_id}"
    )
    return await get_media_item_impl(service, user_google_email, media_item_id)
