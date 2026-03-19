"""
Google Vault MCP Tools

This module provides MCP tools for interacting with Google Vault API.
Note: Requires Google Vault add-on and appropriate permissions.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def list_matters_impl(
    service,
    user_google_email: str,
    state: str = "OPEN",
    page_size: int = 20,
) -> str:
    """Implementation for listing matters."""
    matters = await asyncio.to_thread(
        service.matters().list(pageSize=page_size, state=state).execute
    )

    items = matters.get("matters", [])
    if not items:
        return f"No {state} matters found for {user_google_email}."

    output_parts = [
        f"Found {len(items)} {state} matter(s) for {user_google_email}:",
        "",
    ]

    for matter in items:
        matter_id = matter.get("matterId", "")
        name = matter.get("name", "")
        description = matter.get("description", "")
        created_time = matter.get("matterMetaData", {}).get("createTime", "")
        status = matter.get("state", "")

        output_parts.append(f"- {name}")
        output_parts.append(f"  ID: {matter_id}")
        if description:
            output_parts.append(f"  Description: {description[:80]}...")
        output_parts.append(f"  Status: {status}")
        if created_time:
            output_parts.append(f"  Created: {created_time}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_matters", is_read_only=True, service_type="vault")
@require_google_service("vault", "vault_read")
async def list_matters(
    service,
    user_google_email: str,
    state: str = "OPEN",
    page_size: int = 20,
) -> str:
    """
    Lists Vault matters.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        state (str): Filter by state - OPEN, CLOSED, DELETED. Defaults to OPEN.
        page_size (int): Maximum number of matters. Defaults to 20.

    Returns:
        str: Formatted list of matters.
    """
    logger.info(f"[list_matters] Invoked. Email: '{user_google_email}', State: {state}")
    return await list_matters_impl(service, user_google_email, state, page_size)


async def get_matter_impl(
    service,
    user_google_email: str,
    matter_id: str,
) -> str:
    """Implementation for getting matter details."""
    matter = await asyncio.to_thread(service.matters().get(matterId=matter_id).execute)

    name = matter.get("name", "")
    description = matter.get("description", "")
    state = matter.get("state", "")
    created_time = matter.get("matterMetaData", {}).get("createTime", "")
    updated_time = matter.get("matterMetaData", {}).get("updateTime", "")

    collaborators = matter.get("matterViewAccesses", [])

    output_parts = [
        f"Matter Details for {user_google_email}:",
        f"Name: {name}",
        f"ID: {matter_id}",
        f"State: {state}",
    ]

    if description:
        output_parts.append(f"Description: {description}")
    if created_time:
        output_parts.append(f"Created: {created_time}")
    if updated_time:
        output_parts.append(f"Updated: {updated_time}")

    if collaborators:
        output_parts.append("Collaborators:")
        for collab in collaborators:
            email = collab.get("email", "")
            output_parts.append(f"  - {email}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_matter", is_read_only=True, service_type="vault")
@require_google_service("vault", "vault_read")
async def get_matter(
    service,
    user_google_email: str,
    matter_id: str,
) -> str:
    """
    Gets details of a specific matter.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        matter_id (str): The matter ID. Required.

    Returns:
        str: Full details of the matter.
    """
    logger.info(
        f"[get_matter] Invoked. Email: '{user_google_email}', Matter: {matter_id}"
    )
    return await get_matter_impl(service, user_google_email, matter_id)


async def create_matter_impl(
    service,
    user_google_email: str,
    name: str,
    description: Optional[str] = None,
) -> str:
    """Implementation for creating a matter."""
    matter_body = {"name": name}
    if description:
        matter_body["description"] = description

    created = await asyncio.to_thread(
        service.matters().create(body=matter_body).execute
    )

    matter_id = created.get("matterId", "")
    state = created.get("state", "")

    text_output = (
        f"Successfully created matter for {user_google_email}:\n"
        f"Name: {name}\n"
        f"ID: {matter_id}\n"
        f"State: {state}"
    )

    logger.info(f"Successfully created matter: {matter_id}")
    return text_output


@server.tool()
@handle_http_errors("create_matter", service_type="vault")
@require_google_service("vault", "vault_write")
async def create_matter(
    service,
    user_google_email: str,
    name: str,
    description: Optional[str] = None,
) -> str:
    """
    Creates a new Vault matter.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        name (str): The name for the matter. Required.
        description (Optional[str]): Matter description.

    Returns:
        str: Confirmation message with matter details.
    """
    logger.info(f"[create_matter] Invoked. Email: '{user_google_email}', Name: {name}")
    return await create_matter_impl(service, user_google_email, name, description)


async def close_matter_impl(
    service,
    user_google_email: str,
    matter_id: str,
) -> str:
    """Implementation for closing a matter."""
    await asyncio.to_thread(
        service.matters().close(matterId=matter_id, body={}).execute
    )

    text_output = f"Successfully closed matter '{matter_id}' for {user_google_email}."

    logger.info(f"Successfully closed matter: {matter_id}")
    return text_output


@server.tool()
@handle_http_errors("close_matter", service_type="vault")
@require_google_service("vault", "vault_write")
async def close_matter(
    service,
    user_google_email: str,
    matter_id: str,
) -> str:
    """
    Closes a Vault matter.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        matter_id (str): The matter ID. Required.

    Returns:
        str: Confirmation message.
    """
    logger.info(
        f"[close_matter] Invoked. Email: '{user_google_email}', Matter: {matter_id}"
    )
    return await close_matter_impl(service, user_google_email, matter_id)


async def list_holds_impl(
    service,
    user_google_email: str,
    matter_id: str,
) -> str:
    """Implementation for listing holds."""
    holds = await asyncio.to_thread(
        service.matters().holds().list(matterId=matter_id).execute
    )

    items = holds.get("holds", [])
    if not items:
        return f"No holds found in matter '{matter_id}' for {user_google_email}."

    output_parts = [
        f"Found {len(items)} hold(s) in matter '{matter_id}' for {user_google_email}:",
        "",
    ]

    for hold in items:
        hold_id = hold.get("holdId", "")
        name = hold.get("name", "")
        email_count = len(hold.get("accounts", []))
        org_unit = hold.get("orgUnit", {})
        query = hold.get("query", {})
        created_time = hold.get("createTime", "")

        output_parts.append(f"- {name}")
        output_parts.append(f"  ID: {hold_id}")

        if email_count > 0:
            output_parts.append(f"  Accounts held: {email_count}")

        if org_unit:
            org_path = org_unit.get("orgUnitPath", "")
            output_parts.append(f"  Org Unit: {org_path}")

        if query:
            query_type = query.get("queryType", "")
            output_parts.append(f"  Query Type: {query_type}")

        if created_time:
            output_parts.append(f"  Created: {created_time}")

        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_holds", is_read_only=True, service_type="vault")
@require_google_service("vault", "vault_read")
async def list_holds(
    service,
    user_google_email: str,
    matter_id: str,
) -> str:
    """
    Lists holds in a matter.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        matter_id (str): The matter ID. Required.

    Returns:
        str: Formatted list of holds.
    """
    logger.info(
        f"[list_holds] Invoked. Email: '{user_google_email}', Matter: {matter_id}"
    )
    return await list_holds_impl(service, user_google_email, matter_id)


async def create_hold_impl(
    service,
    user_google_email: str,
    matter_id: str,
    name: str,
    account_emails: Optional[List[str]] = None,
    org_unit: Optional[str] = None,
) -> str:
    """Implementation for creating a hold."""
    if not account_emails and not org_unit:
        raise UserInputError("Either account_emails or org_unit must be provided.")

    hold_body = {"name": name}

    if account_emails:
        hold_body["accounts"] = [{"email": email} for email in account_emails]

    if org_unit:
        hold_body["orgUnit"] = {"orgUnitPath": org_unit}

    created = await asyncio.to_thread(
        service.matters().holds().create(matterId=matter_id, body=hold_body).execute
    )

    hold_id = created.get("holdId", "")

    text_output = (
        f"Successfully created hold for {user_google_email}:\n"
        f"Matter: {matter_id}\n"
        f"Hold: {name}\n"
        f"ID: {hold_id}"
    )

    logger.info(f"Successfully created hold: {hold_id}")
    return text_output


@server.tool()
@handle_http_errors("create_hold", service_type="vault")
@require_google_service("vault", "vault_write")
async def create_hold(
    service,
    user_google_email: str,
    matter_id: str,
    name: str,
    account_emails: Optional[List[str]] = None,
    org_unit: Optional[str] = None,
) -> str:
    """
    Creates a hold in a matter.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        matter_id (str): The matter ID. Required.
        name (str): Name for the hold. Required.
        account_emails (Optional[List[str]]): List of emails to hold.
        org_unit (Optional[str]): Organizational unit to hold.

    Returns:
        str: Confirmation message.
    """
    logger.info(
        f"[create_hold] Invoked. Email: '{user_google_email}', Matter: {matter_id}, Hold: {name}"
    )
    return await create_hold_impl(
        service, user_google_email, matter_id, name, account_emails, org_unit
    )


async def remove_hold_impl(
    service,
    user_google_email: str,
    matter_id: str,
    hold_id: str,
) -> str:
    """Implementation for removing a hold."""
    await asyncio.to_thread(
        service.matters().holds().delete(matterId=matter_id, holdId=hold_id).execute
    )

    text_output = f"Successfully removed hold '{hold_id}' from matter '{matter_id}' for {user_google_email}."

    logger.info(f"Successfully removed hold: {hold_id}")
    return text_output


@server.tool()
@handle_http_errors("remove_hold", service_type="vault")
@require_google_service("vault", "vault_write")
async def remove_hold(
    service,
    user_google_email: str,
    matter_id: str,
    hold_id: str,
) -> str:
    """
    Removes a hold from a matter.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        matter_id (str): The matter ID. Required.
        hold_id (str): The hold ID to remove. Required.

    Returns:
        str: Confirmation message.
    """
    logger.info(
        f"[remove_hold] Invoked. Email: '{user_google_email}', Matter: {matter_id}, Hold: {hold_id}"
    )
    return await remove_hold_impl(service, user_google_email, matter_id, hold_id)
