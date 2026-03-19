"""
Unit tests for Google Workspace Admin tools
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def create_mock_admin_service():
    """Create a properly configured mock Admin service."""
    mock_service = Mock()
    return mock_service


@pytest.mark.asyncio
async def test_list_users_returns_list():
    """Test list_users returns formatted users list"""
    from gadmin.admin_tools import list_users_impl

    mock_service = create_mock_admin_service()
    mock_service.users().list().execute = Mock(
        return_value={
            "users": [
                {
                    "primaryEmail": "user1@example.com",
                    "name": {"fullName": "User One"},
                    "suspended": False,
                    "isAdmin": False,
                }
            ]
        }
    )

    result = await list_users_impl(
        service=mock_service,
        user_google_email="admin@example.com",
        domain="example.com",
    )

    assert "user1@example.com" in result
    assert "User One" in result


@pytest.mark.asyncio
async def test_create_user_success():
    """Test create_user creates a new user"""
    from gadmin.admin_tools import create_user_impl

    mock_service = create_mock_admin_service()
    mock_service.users().insert().execute = Mock(
        return_value={
            "primaryEmail": "newuser@example.com",
            "id": "12345",
        }
    )

    result = await create_user_impl(
        service=mock_service,
        user_google_email="admin@example.com",
        email="newuser@example.com",
        first_name="New",
        last_name="User",
        password="password123",
    )

    assert "newuser@example.com" in result
    assert "Successfully" in result


@pytest.mark.asyncio
async def test_delete_user_success():
    """Test delete_user removes a user"""
    from gadmin.admin_tools import delete_user_impl

    mock_service = create_mock_admin_service()
    mock_service.users().delete().execute = Mock(return_value={})

    result = await delete_user_impl(
        service=mock_service,
        user_google_email="admin@example.com",
        user_key="olduser@example.com",
    )

    assert "Successfully" in result
    assert "olduser@example.com" in result


@pytest.mark.asyncio
async def test_create_group_success():
    """Test create_group creates a new group"""
    from gadmin.admin_tools import create_group_impl

    mock_service = create_mock_admin_service()
    mock_service.groups().insert().execute = Mock(
        return_value={
            "email": "newgroup@example.com",
            "id": "67890",
        }
    )

    result = await create_group_impl(
        service=mock_service,
        user_google_email="admin@example.com",
        email="newgroup@example.com",
        name="New Group",
    )

    assert "newgroup@example.com" in result
    assert "Successfully" in result


@pytest.mark.asyncio
async def test_add_group_member_success():
    """Test add_group_member adds a member"""
    from gadmin.admin_tools import add_group_member_impl

    mock_service = create_mock_admin_service()
    mock_service.members().insert().execute = Mock(
        return_value={
            "email": "member@example.com",
            "role": "MEMBER",
        }
    )

    result = await add_group_member_impl(
        service=mock_service,
        user_google_email="admin@example.com",
        group_key="group@example.com",
        member_email="member@example.com",
    )

    assert "member@example.com" in result
    assert "Successfully" in result
