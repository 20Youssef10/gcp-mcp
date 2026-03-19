"""
Google Workspace Admin MCP Tools

This module provides MCP tools for interacting with Google Workspace Admin SDK.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def list_users_impl(
    service,
    user_google_email: str,
    domain: str,
    max_results: int = 50,
    query: Optional[str] = None,
) -> str:
    """Implementation for listing users."""
    params = {
        "domain": domain,
        "maxResults": max_results,
    }
    if query:
        params["query"] = query

    users = await asyncio.to_thread(service.users().list(**params).execute)

    items = users.get("users", [])
    if not items:
        return f"No users found in domain '{domain}'."

    output_parts = [
        f"Found {len(items)} user(s) in domain '{domain}':",
        "",
    ]

    for user in items:
        primary_email = user.get("primaryEmail", "")
        name = user.get("name", {})
        full_name = name.get("fullName", "")
        given_name = name.get("givenName", "")
        family_name = name.get("familyName", "")
        suspended = user.get("suspended", False)
        admin = user.get("isAdmin", False)

        output_parts.append(f"- {primary_email}")
        if full_name:
            output_parts.append(f"  Name: {full_name}")
        elif given_name or family_name:
            output_parts.append(f"  Name: {given_name} {family_name}")
        output_parts.append(f"  Suspended: {suspended}")
        output_parts.append(f"  Admin: {admin}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_users", is_read_only=True, service_type="admin")
@require_google_service("admin", "admin_read")
async def list_users(
    service,
    user_google_email: str,
    domain: str,
    max_results: int = 50,
    query: Optional[str] = None,
) -> str:
    """
    Lists users in a Google Workspace domain.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        domain (str): The domain to list users from. Required.
        max_results (int): Maximum number of users. Defaults to 50.
        query (Optional[str]): Search query (e.g., "name:John*").

    Returns:
        str: Formatted list of users.
    """
    logger.info(f"[list_users] Invoked. Email: '{user_google_email}', Domain: {domain}")
    return await list_users_impl(service, user_google_email, domain, max_results, query)


async def get_user_impl(
    service,
    user_google_email: str,
    user_key: str,
) -> str:
    """Implementation for getting user details."""
    user = await asyncio.to_thread(service.users().get(userKey=user_key).execute)

    primary_email = user.get("primaryEmail", "")
    name = user.get("name", {})
    full_name = name.get("fullName", "")
    given_name = name.get("givenName", "")
    family_name = name.get("familyName", "")
    suspended = user.get("suspended", False)
    admin = user.get("isAdmin", False)
    delegate = user.get("isDelegatedAdmin", False)
    org = user.get("orgUnitPath", "")
    creation_time = user.get("creationTime", "")
    last_login = user.get("lastLoginTime", "")
    aliases = user.get("aliases", [])
    emails = user.get("emails", [])
    phones = user.get("phones", [])

    output_parts = [
        f"User Details for {user_google_email}:",
        f"Primary Email: {primary_email}",
    ]

    if full_name:
        output_parts.append(f"Full Name: {full_name}")
    if given_name or family_name:
        output_parts.append(f"Name: {given_name} {family_name}")

    output_parts.extend(
        [
            f"Suspended: {suspended}",
            f"Admin: {admin}",
            f"Delegated Admin: {delegate}",
        ]
    )

    if org:
        output_parts.append(f"Organization: {org}")
    if creation_time:
        output_parts.append(f"Created: {creation_time}")
    if last_login and last_login != "1970-01-01T00:00:00.000Z":
        output_parts.append(f"Last Login: {last_login}")

    if aliases:
        output_parts.append(f"Aliases: {', '.join(aliases)}")

    if emails:
        output_parts.append("Email Addresses:")
        for email in emails[:5]:
            output_parts.append(
                f"  - {email.get('address', '')} ({email.get('type', 'other')})"
            )

    if phones:
        output_parts.append("Phone Numbers:")
        for phone in phones[:5]:
            output_parts.append(
                f"  - {phone.get('value', '')} ({phone.get('type', 'other')})"
            )

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_user", is_read_only=True, service_type="admin")
@require_google_service("admin", "admin_read")
async def get_user(
    service,
    user_google_email: str,
    user_key: str,
) -> str:
    """
    Gets details of a specific user.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        user_key (str): The user's email or unique ID. Required.

    Returns:
        str: Full details of the user.
    """
    logger.info(f"[get_user] Invoked. Email: '{user_google_email}', User: {user_key}")
    return await get_user_impl(service, user_google_email, user_key)


async def create_user_impl(
    service,
    user_google_email: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    org_unit_path: Optional[str] = None,
) -> str:
    """Implementation for creating a user."""
    user_body = {
        "primaryEmail": email,
        "name": {
            "givenName": first_name,
            "familyName": last_name,
        },
        "password": password,
    }

    if org_unit_path:
        user_body["orgUnitPath"] = org_unit_path

    created = await asyncio.to_thread(service.users().insert(body=user_body).execute)

    primary_email = created.get("primaryEmail", email)
    user_id = created.get("id", "")

    text_output = (
        f"Successfully created user for {user_google_email}:\n"
        f"Email: {primary_email}\n"
        f"User ID: {user_id}"
    )

    logger.info(f"Successfully created user: {email}")
    return text_output


@server.tool()
@handle_http_errors("create_user", service_type="admin")
@require_google_service("admin", "admin_write")
async def create_user(
    service,
    user_google_email: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    org_unit_path: Optional[str] = None,
) -> str:
    """
    Creates a new user in Google Workspace.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        email (str): The new user's email address. Required.
        first_name (str): User's first name. Required.
        last_name (str): User's last name. Required.
        password (str): Initial password. Required.
        org_unit_path (Optional[str]): Organization unit path.

    Returns:
        str: Confirmation message with user details.
    """
    logger.info(f"[create_user] Invoked. Email: '{user_google_email}', User: {email}")
    return await create_user_impl(
        service,
        user_google_email,
        email,
        first_name,
        last_name,
        password,
        org_unit_path,
    )


async def delete_user_impl(
    service,
    user_google_email: str,
    user_key: str,
) -> str:
    """Implementation for deleting a user."""
    await asyncio.to_thread(service.users().delete(userKey=user_key).execute)

    text_output = f"Successfully deleted user '{user_key}' for {user_google_email}."

    logger.info(f"Successfully deleted user: {user_key}")
    return text_output


@server.tool()
@handle_http_errors("delete_user", service_type="admin")
@require_google_service("admin", "admin_write")
async def delete_user(
    service,
    user_google_email: str,
    user_key: str,
) -> str:
    """
    Deletes a user from Google Workspace.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        user_key (str): The user's email or unique ID to delete. Required.

    Returns:
        str: Confirmation message.
    """
    logger.info(
        f"[delete_user] Invoked. Email: '{user_google_email}', User: {user_key}"
    )
    return await delete_user_impl(service, user_google_email, user_key)


async def list_groups_impl(
    service,
    user_google_email: str,
    domain: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """Implementation for listing groups."""
    params = {"maxResults": max_results}
    if domain:
        params["domain"] = domain

    groups = await asyncio.to_thread(service.groups().list(**params).execute)

    items = groups.get("groups", [])
    if not items:
        return f"No groups found for {user_google_email}."

    output_parts = [
        f"Found {len(items)} group(s):",
        "",
    ]

    for group in items:
        email = group.get("email", "")
        name = group.get("name", "")
        description = group.get("description", "")
        direct_members_count = group.get("directMembersCount", "")

        output_parts.append(f"- {email}")
        if name and name != email:
            output_parts.append(f"  Name: {name}")
        if description:
            output_parts.append(f"  Description: {description[:80]}...")
        output_parts.append(f"  Members: {direct_members_count}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_groups", is_read_only=True, service_type="admin")
@require_google_service("admin", "admin_read")
async def list_groups(
    service,
    user_google_email: str,
    domain: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """
    Lists groups in a Google Workspace domain.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        domain (Optional[str]): Filter by domain.
        max_results (int): Maximum number of groups. Defaults to 50.

    Returns:
        str: Formatted list of groups.
    """
    logger.info(
        f"[list_groups] Invoked. Email: '{user_google_email}', Domain: {domain}"
    )
    return await list_groups_impl(service, user_google_email, domain, max_results)


async def get_group_impl(
    service,
    user_google_email: str,
    group_key: str,
) -> str:
    """Implementation for getting group details."""
    group = await asyncio.to_thread(service.groups().get(groupKey=group_key).execute)

    email = group.get("email", "")
    name = group.get("name", "")
    description = group.get("description", "")
    direct_members_count = group.get("directMembersCount", "")
    admin_created = group.get("adminCreated", False)

    output_parts = [
        f"Group Details for {user_google_email}:",
        f"Email: {email}",
    ]

    if name and name != email:
        output_parts.append(f"Name: {name}")
    if description:
        output_parts.append(f"Description: {description}")
    output_parts.append(f"Members: {direct_members_count}")
    output_parts.append(f"Admin Created: {admin_created}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_group", is_read_only=True, service_type="admin")
@require_google_service("admin", "admin_read")
async def get_group(
    service,
    user_google_email: str,
    group_key: str,
) -> str:
    """
    Gets details of a specific group.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        group_key (str): The group's email or unique ID. Required.

    Returns:
        str: Full details of the group.
    """
    logger.info(
        f"[get_group] Invoked. Email: '{user_google_email}', Group: {group_key}"
    )
    return await get_group_impl(service, user_google_email, group_key)


async def create_group_impl(
    service,
    user_google_email: str,
    email: str,
    name: str,
    description: Optional[str] = None,
) -> str:
    """Implementation for creating a group."""
    group_body = {
        "email": email,
        "name": name,
    }
    if description:
        group_body["description"] = description

    created = await asyncio.to_thread(service.groups().insert(body=group_body).execute)

    group_email = created.get("email", email)
    group_id = created.get("id", "")

    text_output = (
        f"Successfully created group for {user_google_email}:\n"
        f"Email: {group_email}\n"
        f"Group ID: {group_id}"
    )

    logger.info(f"Successfully created group: {email}")
    return text_output


@server.tool()
@handle_http_errors("create_group", service_type="admin")
@require_google_service("admin", "admin_write")
async def create_group(
    service,
    user_google_email: str,
    email: str,
    name: str,
    description: Optional[str] = None,
) -> str:
    """
    Creates a new group in Google Workspace.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        email (str): The group's email address. Required.
        name (str): The group's display name. Required.
        description (Optional[str]): Group description.

    Returns:
        str: Confirmation message with group details.
    """
    logger.info(f"[create_group] Invoked. Email: '{user_google_email}', Group: {email}")
    return await create_group_impl(service, user_google_email, email, name, description)


async def add_group_member_impl(
    service,
    user_google_email: str,
    group_key: str,
    member_email: str,
    role: str = "MEMBER",
) -> str:
    """Implementation for adding a group member."""
    allowed_roles = {"MEMBER", "MANAGER", "OWNER"}
    if role.upper() not in allowed_roles:
        raise UserInputError(f"role must be one of {allowed_roles}, got '{role}'.")

    member_body = {
        "email": member_email,
        "role": role.upper(),
    }

    created = await asyncio.to_thread(
        service.members().insert(groupKey=group_key, body=member_body).execute
    )

    member_id = created.get("id", member_email)

    text_output = (
        f"Successfully added member to group for {user_google_email}:\n"
        f"Group: {group_key}\n"
        f"Member: {member_id}\n"
        f"Role: {role.upper()}"
    )

    logger.info(f"Successfully added member: {member_email}")
    return text_output


@server.tool()
@handle_http_errors("add_group_member", service_type="admin")
@require_google_service("admin", "admin_write")
async def add_group_member(
    service,
    user_google_email: str,
    group_key: str,
    member_email: str,
    role: str = "MEMBER",
) -> str:
    """
    Adds a member to a group.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        group_key (str): The group's email or ID. Required.
        member_email (str): Member's email address. Required.
        role (str): Role - MEMBER, MANAGER, OWNER. Defaults to MEMBER.

    Returns:
        str: Confirmation message.
    """
    logger.info(
        f"[add_group_member] Invoked. Email: '{user_google_email}', Group: {group_key}, Member: {member_email}"
    )
    return await add_group_member_impl(
        service, user_google_email, group_key, member_email, role
    )


async def list_group_members_impl(
    service,
    user_google_email: str,
    group_key: str,
    max_results: int = 50,
) -> str:
    """Implementation for listing group members."""
    members = await asyncio.to_thread(
        service.members().list(groupKey=group_key, maxResults=max_results).execute
    )

    items = members.get("members", [])
    if not items:
        return f"No members found in group '{group_key}'."

    output_parts = [
        f"Found {len(items)} member(s) in group '{group_key}':",
        "",
    ]

    for member in items:
        email = member.get("email", "")
        role = member.get("role", "MEMBER")
        status = member.get("status", "")

        output_parts.append(f"- {email}")
        output_parts.append(f"  Role: {role}")
        if status:
            output_parts.append(f"  Status: {status}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_group_members", is_read_only=True, service_type="admin")
@require_google_service("admin", "admin_read")
async def list_group_members(
    service,
    user_google_email: str,
    group_key: str,
    max_results: int = 50,
) -> str:
    """
    Lists members of a group.

    Args:
        user_google_email (str): The admin's Google email address. Required.
        group_key (str): The group's email or ID. Required.
        max_results (int): Maximum number of members. Defaults to 50.

    Returns:
        str: Formatted list of members.
    """
    logger.info(
        f"[list_group_members] Invoked. Email: '{user_google_email}', Group: {group_key}"
    )
    return await list_group_members_impl(
        service, user_google_email, group_key, max_results
    )
