"""
Unit tests for YouTube tools
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def create_mock_youtube_service():
    """Create a properly configured mock YouTube service."""
    mock_service = Mock()
    return mock_service


@pytest.mark.asyncio
async def test_search_videos_returns_results():
    """Test search_videos returns search results"""
    from gyoutube.youtube_tools import search_videos_impl

    mock_service = create_mock_youtube_service()
    mock_service.search().list().execute = Mock(
        return_value={
            "items": [
                {
                    "id": {"videoId": "video123"},
                    "snippet": {
                        "title": "Test Video",
                        "description": "A test video",
                        "channelTitle": "Test Channel",
                    },
                }
            ]
        }
    )

    result = await search_videos_impl(
        service=mock_service, user_google_email="test@example.com", query="test video"
    )

    assert "Test Video" in result
    assert "video123" in result


@pytest.mark.asyncio
async def test_get_video_returns_details():
    """Test get_video returns video details"""
    from gyoutube.youtube_tools import get_video_impl

    mock_service = create_mock_youtube_service()
    mock_service.videos().list().execute = Mock(
        return_value={
            "items": [
                {
                    "id": "video123",
                    "snippet": {
                        "title": "Test Video",
                        "description": "Description",
                        "channelTitle": "Channel",
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "50",
                    },
                }
            ]
        }
    )

    result = await get_video_impl(
        service=mock_service, user_google_email="test@example.com", video_id="video123"
    )

    assert "Test Video" in result
    assert "video123" in result


@pytest.mark.asyncio
async def test_list_youtube_subscriptions_returns_list():
    """Test list_youtube_subscriptions returns subscriptions"""
    from gyoutube.youtube_tools import list_youtube_subscriptions_impl

    mock_service = create_mock_youtube_service()
    mock_service.subscriptions().list().execute = Mock(
        return_value={
            "items": [
                {
                    "snippet": {
                        "title": "My Channel",
                        "resourceId": {"channelId": "channel123"},
                    }
                }
            ],
            "pageInfo": {"totalResults": 1},
        }
    )

    result = await list_youtube_subscriptions_impl(
        service=mock_service, user_google_email="test@example.com"
    )

    assert "My Channel" in result
    assert "test@example.com" in result
