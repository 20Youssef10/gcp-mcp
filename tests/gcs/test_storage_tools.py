"""
Unit tests for Google Cloud Storage tools
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def create_mock_storage_service():
    """Create a properly configured mock Storage service."""
    mock_service = Mock()
    return mock_service


@pytest.mark.asyncio
async def test_list_buckets_returns_list():
    """Test list_buckets returns formatted buckets list"""
    from gcs.storage_tools import list_buckets_impl

    mock_service = create_mock_storage_service()
    mock_service.buckets().list().execute = Mock(
        return_value={
            "items": [
                {
                    "name": "test-bucket",
                    "location": "US",
                    "storageClass": "STANDARD",
                    "timeCreated": "2024-01-01T00:00:00Z",
                }
            ]
        }
    )

    result = await list_buckets_impl(
        service=mock_service,
        user_google_email="test@example.com",
        project_id="my-project",
    )

    assert "test-bucket" in result
    assert "US" in result
    assert "test@example.com" in result


@pytest.mark.asyncio
async def test_create_bucket_success():
    """Test create_bucket creates a new bucket"""
    from gcs.storage_tools import create_bucket_impl

    mock_service = create_mock_storage_service()
    mock_service.buckets().insert().execute = Mock(
        return_value={
            "name": "new-bucket",
            "location": "US",
            "storageClass": "STANDARD",
            "timeCreated": "2024-01-01T00:00:00Z",
        }
    )

    result = await create_bucket_impl(
        service=mock_service,
        user_google_email="test@example.com",
        bucket_name="new-bucket",
        project_id="my-project",
    )

    assert "new-bucket" in result
    assert "Successfully" in result


@pytest.mark.asyncio
async def test_delete_bucket_success():
    """Test delete_bucket removes a bucket"""
    from gcs.storage_tools import delete_bucket_impl

    mock_service = create_mock_storage_service()
    mock_service.buckets().delete().execute = Mock(return_value={})

    result = await delete_bucket_impl(
        service=mock_service,
        user_google_email="test@example.com",
        bucket_name="old-bucket",
    )

    assert "Successfully" in result
    assert "old-bucket" in result
