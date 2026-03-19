"""
Unit tests for Google Vault tools
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def create_mock_vault_service():
    """Create a properly configured mock Vault service."""
    mock_service = Mock()
    return mock_service


@pytest.mark.asyncio
async def test_list_matters_returns_list():
    """Test list_matters returns formatted matters list"""
    from gvault.vault_tools import list_matters_impl

    mock_service = create_mock_vault_service()
    mock_service.matters().list().execute = Mock(
        return_value={
            "matters": [
                {
                    "matterId": "matter1",
                    "name": "Legal Case 1",
                    "state": "OPEN",
                }
            ]
        }
    )

    result = await list_matters_impl(
        service=mock_service, user_google_email="admin@example.com"
    )

    assert "Legal Case 1" in result
    assert "matter1" in result
    assert "admin@example.com" in result


@pytest.mark.asyncio
async def test_create_matter_success():
    """Test create_matter creates a new matter"""
    from gvault.vault_tools import create_matter_impl

    mock_service = create_mock_vault_service()
    mock_service.matters().create().execute = Mock(
        return_value={
            "matterId": "new-matter-id",
            "name": "New Matter",
            "state": "OPEN",
        }
    )

    result = await create_matter_impl(
        service=mock_service, user_google_email="admin@example.com", name="New Matter"
    )

    assert "New Matter" in result
    assert "Successfully" in result


@pytest.mark.asyncio
async def test_close_matter_success():
    """Test close_matter closes a matter"""
    from gvault.vault_tools import close_matter_impl

    mock_service = create_mock_vault_service()
    mock_service.matters().close().execute = Mock(return_value={})

    result = await close_matter_impl(
        service=mock_service, user_google_email="admin@example.com", matter_id="matter1"
    )

    assert "Successfully" in result
    assert "matter1" in result
