"""
Unit tests for Google Keep tools
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def create_mock_keep_service():
    """Create a properly configured mock Keep service."""
    mock_service = Mock()
    return mock_service


@pytest.mark.asyncio
async def test_list_notes_returns_formatted_output():
    """Test list_notes returns formatted notes list"""
    from gkeep.keep_tools import list_notes_impl

    mock_service = create_mock_keep_service()
    mock_service.notes().list().execute = Mock(
        return_value={
            "notes": [
                {
                    "name": "notes/note1",
                    "title": "Test Note",
                    "createdTime": "2024-01-01T00:00:00Z",
                    "updatedTime": "2024-01-02T00:00:00Z",
                }
            ]
        }
    )

    result = await list_notes_impl(
        service=mock_service, user_google_email="test@example.com", page_size=10
    )

    assert "Test Note" in result
    assert "test@example.com" in result


@pytest.mark.asyncio
async def test_get_note_returns_details():
    """Test get_note returns full note details"""
    from gkeep.keep_tools import get_note_impl

    mock_service = create_mock_keep_service()
    mock_service.notes().get().execute = Mock(
        return_value={
            "name": "notes/note1",
            "title": "Test Note",
            "body": {"text": "Test content"},
            "createdTime": "2024-01-01T00:00:00Z",
            "updatedTime": "2024-01-02T00:00:00Z",
        }
    )

    result = await get_note_impl(
        service=mock_service, user_google_email="test@example.com", note_id="note1"
    )

    assert "Test Note" in result
    assert "Test content" in result


@pytest.mark.asyncio
async def test_create_note_success():
    """Test create_note creates a new note"""
    from gkeep.keep_tools import create_note_impl

    mock_service = create_mock_keep_service()
    mock_service.notes().create().execute = Mock(
        return_value={
            "name": "notes/new-note-id",
            "title": "New Note",
            "createdTime": "2024-01-01T00:00:00Z",
        }
    )

    result = await create_note_impl(
        service=mock_service,
        user_google_email="test@example.com",
        title="New Note",
        content="New content",
    )

    assert "New Note" in result
    assert "test@example.com" in result


@pytest.mark.asyncio
async def test_delete_note_success():
    """Test delete_note removes a note"""
    from gkeep.keep_tools import delete_note_impl

    mock_service = create_mock_keep_service()
    mock_service.notes().delete().execute = Mock(return_value={})

    result = await delete_note_impl(
        service=mock_service, user_google_email="test@example.com", note_id="note1"
    )

    assert "Successfully" in result
    assert "note1" in result
