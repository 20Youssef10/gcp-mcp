"""
YouTube MCP Tools

This module provides MCP tools for interacting with YouTube Data API.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def search_videos_impl(
    service,
    user_google_email: str,
    query: str,
    max_results: int = 10,
    video_type: str = "video",
) -> str:
    """Implementation for searching videos."""
    search_response = await asyncio.to_thread(
        service.search()
        .list(
            q=query,
            type=video_type,
            part="snippet",
            maxResults=max_results,
            relevanceLanguage="en",
        )
        .execute
    )

    items = search_response.get("items", [])
    if not items:
        return f"No results found for '{query}'."

    output_parts = [
        f"Search results for '{query}' ({len(items)} {video_type}s):",
        "",
    ]

    for i, item in enumerate(items, 1):
        snippet = item.get("snippet", {})
        title = snippet.get("title", "Untitled")
        channel_title = snippet.get("channelTitle", "Unknown")
        description = snippet.get("description", "")

        if video_type == "video":
            video_id = item.get("id", {}).get("videoId", "")
            link = f"https://www.youtube.com/watch?v={video_id}"
            output_parts.append(f"{i}. {title}")
            output_parts.append(f"   Channel: {channel_title}")
            output_parts.append(f"   Link: {link}")
        elif video_type == "channel":
            channel_id = item.get("id", {}).get("channelId", "")
            link = f"https://www.youtube.com/channel/{channel_id}"
            output_parts.append(f"{i}. {title}")
            output_parts.append(f"   Channel ID: {channel_id}")
            output_parts.append(f"   Link: {link}")
        elif video_type == "playlist":
            playlist_id = item.get("id", {}).get("playlistId", "")
            link = f"https://www.youtube.com/playlist?list={playlist_id}"
            output_parts.append(f"{i}. {title}")
            output_parts.append(f"   Channel: {channel_title}")
            output_parts.append(f"   Link: {link}")

        if description:
            desc_preview = (
                description[:100] + "..." if len(description) > 100 else description
            )
            output_parts.append(f"   Description: {desc_preview}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("search_videos", is_read_only=True, service_type="youtube")
@require_google_service("youtube", "youtube_read")
async def search_videos(
    service,
    user_google_email: str,
    query: str,
    max_results: int = 10,
    video_type: str = "video",
) -> str:
    """
    Searches for videos on YouTube.

    Args:
        user_google_email (str): The user's Google email address. Required.
        query (str): The search query string. Required.
        max_results (int): Maximum number of results to return. Defaults to 10.
        video_type (str): Type of search - "video", "channel", or "playlist". Defaults to "video".

    Returns:
        str: Formatted list of search results.
    """
    logger.info(
        f"[search_videos] Invoked. Email: '{user_google_email}', Query: '{query}', "
        f"Max: {max_results}, Type: {video_type}"
    )
    return await search_videos_impl(
        service, user_google_email, query, max_results, video_type
    )


async def get_video_impl(
    service,
    user_google_email: str,
    video_id: str,
) -> str:
    """Implementation for getting a video."""
    video_response = await asyncio.to_thread(
        service.videos()
        .list(
            id=video_id,
            part="snippet,statistics,contentDetails",
        )
        .execute
    )

    videos = video_response.get("items", [])
    if not videos:
        raise UserInputError(f"Video with ID '{video_id}' not found.")

    video = videos[0]
    snippet = video.get("snippet", {})
    statistics = video.get("statistics", {})
    content_details = video.get("contentDetails", {})

    title = snippet.get("title", "Untitled")
    channel_id = snippet.get("channelId", "")
    channel_title = snippet.get("channelTitle", "Unknown")
    description = snippet.get("description", "")
    published = snippet.get("publishedAt", "Unknown")
    thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")

    view_count = statistics.get("viewCount", "0")
    like_count = statistics.get("likeCount", "0")
    comment_count = statistics.get("commentCount", "0")

    duration = content_details.get("duration", "")
    dimension = content_details.get("dimension", "")
    definition = content_details.get("definition", "")
    caption = content_details.get("caption", "")

    output_parts = [
        f"Video Details for {user_google_email}:",
        f"Title: {title}",
        f"Video ID: {video_id}",
        f"Channel: {channel_title} (ID: {channel_id})",
        f"Published: {published}",
        f"Link: https://www.youtube.com/watch?v={video_id}",
        "",
        f"Statistics:",
        f"  Views: {int(view_count):,}",
        f"  Likes: {int(like_count):,}",
        f"  Comments: {int(comment_count):,}",
        "",
        f"Content Details:",
        f"  Duration: {duration}",
        f"  Dimension: {dimension}",
        f"  Definition: {definition}",
        f"  Caption: {caption}",
        "",
    ]

    if description:
        output_parts.append("Description:")
        output_parts.append(
            description[:500] + "..." if len(description) > 500 else description
        )

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_video", is_read_only=True, service_type="youtube")
@require_google_service("youtube", "youtube_read")
async def get_video(
    service,
    user_google_email: str,
    video_id: str,
) -> str:
    """
    Gets details of a specific YouTube video.

    Args:
        user_google_email (str): The user's Google email address. Required.
        video_id (str): The YouTube video ID. Required.

    Returns:
        str: Full details of the video.
    """
    logger.info(
        f"[get_video] Invoked. Email: '{user_google_email}', Video ID: {video_id}"
    )
    return await get_video_impl(service, user_google_email, video_id)


async def get_my_channels_impl(
    service,
    user_google_email: str,
) -> str:
    """Implementation for getting my channels."""
    channels_response = await asyncio.to_thread(
        service.channels()
        .list(
            mine=True,
            part="snippet,statistics,contentDetails",
        )
        .execute
    )

    channels = channels_response.get("items", [])
    if not channels:
        return f"No YouTube channels found for {user_google_email}."

    output_parts = [
        f"YouTube Channels for {user_google_email}:",
        "",
    ]

    for i, channel in enumerate(channels, 1):
        snippet = channel.get("snippet", {})
        statistics = channel.get("statistics", {})
        content_details = channel.get("contentDetails", {})

        title = snippet.get("title", "Untitled")
        description = snippet.get("description", "")
        thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")

        channel_id = channel.get("id", "")

        view_count = statistics.get("viewCount", "0")
        subscriber_count = statistics.get("subscriberCount", "0")
        video_count = statistics.get("videoCount", "0")

        uploads_playlist = content_details.get("relatedPlaylists", {}).get(
            "uploads", ""
        )

        output_parts.append(f"{i}. {title}")
        output_parts.append(f"   Channel ID: {channel_id}")
        output_parts.append(f"   Link: https://www.youtube.com/channel/{channel_id}")
        output_parts.append(f"   Subscribers: {int(subscriber_count):,}")
        output_parts.append(f"   Views: {int(view_count):,}")
        output_parts.append(f"   Videos: {int(video_count):,}")
        if description:
            output_parts.append(f"   Description: {description[:100]}...")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_my_channels", is_read_only=True, service_type="youtube")
@require_google_service("youtube", "youtube_read")
async def get_my_channels(
    service,
    user_google_email: str,
) -> str:
    """
    Gets the user's YouTube channels.

    Args:
        user_google_email (str): The user's Google email address. Required.

    Returns:
        str: List of the user's YouTube channels.
    """
    logger.info(f"[get_my_channels] Invoked. Email: '{user_google_email}'")
    return await get_my_channels_impl(service, user_google_email)


async def get_channel_details_impl(
    service,
    user_google_email: str,
    channel_id: str,
) -> str:
    """Implementation for getting channel details."""
    channel_response = await asyncio.to_thread(
        service.channels()
        .list(
            id=channel_id,
            part="snippet,statistics,contentDetails,brandingSettings",
        )
        .execute
    )

    channels = channel_response.get("items", [])
    if not channels:
        raise UserInputError(f"Channel with ID '{channel_id}' not found.")

    channel = channels[0]
    snippet = channel.get("snippet", {})
    statistics = channel.get("statistics", {})
    content_details = channel.get("contentDetails", {})
    branding = channel.get("brandingSettings", {})

    title = snippet.get("title", "Untitled")
    description = snippet.get("description", "")
    thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")

    view_count = statistics.get("viewCount", "0")
    subscriber_count = statistics.get("subscriberCount", "0")
    video_count = statistics.get("videoCount", "0")
    hidden_subscriber_count = statistics.get("hiddenSubscriberCount", False)

    uploads_playlist = content_details.get("relatedPlaylists", {}).get("uploads", "")

    channel_keywords = branding.get("channel", {}).get("keywords", "")

    output_parts = [
        f"Channel Details for {user_google_email}:",
        f"Title: {title}",
        f"Channel ID: {channel_id}",
        f"Link: https://www.youtube.com/channel/{channel_id}",
        "",
        f"Statistics:",
    ]

    if hidden_subscriber_count:
        output_parts.append(f"  Subscribers: Hidden")
    else:
        output_parts.append(f"  Subscribers: {int(subscriber_count):,}")

    output_parts.extend(
        [
            f"  Views: {int(view_count):,}",
            f"  Videos: {int(video_count):,}",
            "",
        ]
    )

    if description:
        output_parts.append("Description:")
        output_parts.append(description)
        output_parts.append("")

    if channel_keywords:
        output_parts.append(f"Keywords: {channel_keywords[:200]}...")

    output_parts.append(f"Uploads Playlist ID: {uploads_playlist}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_channel_details", is_read_only=True, service_type="youtube")
@require_google_service("youtube", "youtube_read")
async def get_channel_details(
    service,
    user_google_email: str,
    channel_id: str,
) -> str:
    """
    Gets details of a specific YouTube channel.

    Args:
        user_google_email (str): The user's Google email address. Required.
        channel_id (str): The YouTube channel ID. Required.

    Returns:
        str: Full details of the channel.
    """
    logger.info(
        f"[get_channel_details] Invoked. Email: '{user_google_email}', Channel ID: {channel_id}"
    )
    return await get_channel_details_impl(service, user_google_email, channel_id)


async def list_youtube_subscriptions_impl(
    service,
    user_google_email: str,
    max_results: int = 20,
) -> str:
    """Implementation for listing subscriptions."""
    subscriptions_response = await asyncio.to_thread(
        service.subscriptions()
        .list(
            mine=True,
            part="snippet",
            maxResults=max_results,
            order="alphabetical",
        )
        .execute
    )

    items = subscriptions_response.get("items", [])
    if not items:
        return f"No subscriptions found for {user_google_email}."

    output_parts = [
        f"YouTube Subscriptions for {user_google_email}:",
        f"Showing {len(items)} of {subscriptions_response.get('pageInfo', {}).get('totalResults', len(items))} total",
        "",
    ]

    for i, item in enumerate(items, 1):
        snippet = item.get("snippet", {})
        title = snippet.get("title", "Untitled")
        description = snippet.get("description", "")
        channel_id = snippet.get("resourceId", {}).get("channelId", "")

        output_parts.append(f"{i}. {title}")
        output_parts.append(f"   Channel ID: {channel_id}")
        output_parts.append(f"   Link: https://www.youtube.com/channel/{channel_id}")
        if description:
            output_parts.append(f"   Description: {description[:80]}...")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors(
    "list_youtube_subscriptions", is_read_only=True, service_type="youtube"
)
@require_google_service("youtube", "youtube_read")
async def list_youtube_subscriptions(
    service,
    user_google_email: str,
    max_results: int = 20,
) -> str:
    """
    Lists the user's YouTube subscriptions.

    Args:
        user_google_email (str): The user's Google email address. Required.
        max_results (int): Maximum number of subscriptions to return. Defaults to 20.

    Returns:
        str: List of subscribed channels.
    """
    logger.info(
        f"[list_youtube_subscriptions] Invoked. Email: '{user_google_email}', Max: {max_results}"
    )
    return await list_youtube_subscriptions_impl(
        service, user_google_email, max_results
    )


async def list_my_playlists_impl(
    service,
    user_google_email: str,
    max_results: int = 20,
) -> str:
    """Implementation for listing my playlists."""
    playlists_response = await asyncio.to_thread(
        service.playlists()
        .list(
            mine=True,
            part="snippet,status,contentDetails",
            maxResults=max_results,
        )
        .execute
    )

    items = playlists_response.get("items", [])
    if not items:
        return f"No playlists found for {user_google_email}."

    output_parts = [
        f"YouTube Playlists for {user_google_email}:",
        "",
    ]

    for i, item in enumerate(items, 1):
        snippet = item.get("snippet", {})
        status = item.get("status", {})
        content_details = item.get("contentDetails", {})

        title = snippet.get("title", "Untitled")
        description = snippet.get("description", "")
        playlist_id = item.get("id", "")
        item_count = content_details.get("itemCount", 0)
        privacy = status.get("privacyStatus", "private")

        output_parts.append(f"{i}. {title}")
        output_parts.append(f"   Playlist ID: {playlist_id}")
        output_parts.append(
            f"   Link: https://www.youtube.com/playlist?list={playlist_id}"
        )
        output_parts.append(f"   Videos: {item_count}")
        output_parts.append(f"   Privacy: {privacy}")
        if description:
            output_parts.append(f"   Description: {description[:80]}...")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_my_playlists", is_read_only=True, service_type="youtube")
@require_google_service("youtube", "youtube_read")
async def list_my_playlists(
    service,
    user_google_email: str,
    max_results: int = 20,
) -> str:
    """
    Lists the user's YouTube playlists.

    Args:
        user_google_email (str): The user's Google email address. Required.
        max_results (int): Maximum number of playlists to return. Defaults to 20.

    Returns:
        str: List of user playlists.
    """
    logger.info(
        f"[list_my_playlists] Invoked. Email: '{user_google_email}', Max: {max_results}"
    )
    return await list_my_playlists_impl(service, user_google_email, max_results)
