"""
Unit tests for Google Photos tools
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def create_mock_photos_service():
    """Create a properly configured mock Photos service."""
    mock_service = Mock()
    return mock_service


@pytest.mark.asyncio
async def test_list_albums_returns_formatted_output():
    """Test list_albums returns formatted albums list"""
    from gphotos.photos_tools import list_albums_impl

    mock_service = create_mock_photos_service()
    mock_service.albums().list().execute = Mock(
        return_value={
            "albums": [
                {
                    "id": "album1",
                    "title": "Vacation Photos",
                    "totalMediaItemsCount": 50,
                    "createdAt": "2024-01-01T00:00:00Z",
                }
            ]
        }
    )

    result = await list_albums_impl(
        service=mock_service, user_google_email="test@example.com", page_size=10
    )

    assert "Vacation Photos" in result
    assert "album1" in result
    assert "test@example.com" in result


@pytest.mark.asyncio
async def test_create_album_success():
    """Test create_album creates a new album"""
    from gphotos.photos_tools import create_album_impl

    mock_service = create_mock_photos_service()
    mock_service.albums().create().execute = Mock(
        return_value={
            "id": "new-album-id",
            "title": "New Album",
            "createdAt": "2024-01-01T00:00:00Z",
        }
    )

    result = await create_album_impl(
        service=mock_service, user_google_email="test@example.com", title="New Album"
    )

    assert "New Album" in result
    assert "test@example.com" in result


@pytest.mark.asyncio
async def test_list_media_items_returns_items():
    """Test list_media_items returns media items"""
    from gphotos.photos_tools import list_media_items_impl

    mock_service = create_mock_photos_service()
    mock_service.mediaItems().list().execute = Mock(
        return_value={
            "mediaItems": [
                {
                    "id": "photo1",
                    "filename": "photo.jpg",
                    "mimeType": "image/jpeg",
                    "createdAt": "2024-01-01T00:00:00Z",
                }
            ]
        }
    )

    result = await list_media_items_impl(
        service=mock_service, user_google_email="test@example.com", page_size=10
    )

    assert "photo.jpg" in result
    assert "photo1" in result
