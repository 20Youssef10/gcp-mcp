"""
Unit tests for Google Pub/Sub tools
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def create_mock_pubsub_service():
    """Create a properly configured mock Pub/Sub service."""
    mock_service = Mock()
    return mock_service


@pytest.mark.asyncio
async def test_list_topics_returns_list():
    """Test list_topics returns formatted topics list"""
    from gpubsub.pubsub_tools import list_topics_impl

    mock_service = create_mock_pubsub_service()
    mock_service.projects().topics().list().execute = Mock(
        return_value={
            "topics": [
                {
                    "name": "projects/my-project/topics/my-topic",
                    "ackDeadlineSeconds": "10",
                }
            ]
        }
    )

    result = await list_topics_impl(
        service=mock_service,
        user_google_email="test@example.com",
        project_id="my-project",
    )

    assert "my-topic" in result
    assert "test@example.com" in result


@pytest.mark.asyncio
async def test_create_topic_success():
    """Test create_topic creates a new topic"""
    from gpubsub.pubsub_tools import create_topic_impl

    mock_service = create_mock_pubsub_service()
    mock_service.projects().topics().create().execute = Mock(
        return_value={
            "name": "projects/my-project/topics/new-topic",
            "ackDeadlineSeconds": "30",
        }
    )

    result = await create_topic_impl(
        service=mock_service,
        user_google_email="test@example.com",
        topic_name="new-topic",
        project_id="my-project",
    )

    assert "new-topic" in result
    assert "Successfully" in result


@pytest.mark.asyncio
async def test_publish_message_success():
    """Test publish_message publishes messages"""
    from gpubsub.pubsub_tools import publish_message_impl

    mock_service = create_mock_pubsub_service()
    mock_service.projects().topics().publish().execute = Mock(
        return_value={"messageIds": ["msg1", "msg2"]}
    )

    result = await publish_message_impl(
        service=mock_service,
        user_google_email="test@example.com",
        topic_name="projects/my-project/topics/my-topic",
        messages=[{"data": "Hello"}],
    )

    assert "Successfully" in result
    assert "msg1" in result


@pytest.mark.asyncio
async def test_delete_topic_success():
    """Test delete_topic removes a topic"""
    from gpubsub.pubsub_tools import delete_topic_impl

    mock_service = create_mock_pubsub_service()
    mock_service.projects().topics().delete().execute = Mock(return_value={})

    result = await delete_topic_impl(
        service=mock_service,
        user_google_email="test@example.com",
        topic_name="projects/my-project/topics/old-topic",
    )

    assert "Successfully" in result
    assert "old-topic" in result
