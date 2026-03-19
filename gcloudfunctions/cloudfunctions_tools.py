"""
Google Cloud Functions MCP Tools

This module provides MCP tools for interacting with Google Cloud Functions API.
"""

import logging
import asyncio
import json
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def list_functions_impl(
    service,
    user_google_email: str,
    project_id: str,
    region: str = "us-central1",
) -> str:
    """Implementation for listing functions."""
    parent = f"projects/{project_id}/locations/{region}"

    functions = await asyncio.to_thread(
        service.projects().locations().functions().list(parent=parent).execute
    )

    items = functions.get("functions", [])
    if not items:
        return f"No Cloud Functions found in project '{project_id}', region '{region}' for {user_google_email}."

    output_parts = [
        f"Found {len(items)} Cloud Function(s) in project '{project_id}', region '{region}' for {user_google_email}:",
        "",
    ]

    for func in items:
        name = func.get("name", "")
        entry_point = func.get("entryPoint", "")
        runtime = func.get("runtime", "")
        status = func.get("status", "")
        available_memory = func.get("availableMemoryMb", "")
        timeout = func.get("timeout", "")
        max_instances = func.get("maxInstances", "")

        func_name = name.split("/")[-1]

        output_parts.append(f"- {func_name}")
        output_parts.append(f"  Entry Point: {entry_point}")
        output_parts.append(f"  Runtime: {runtime}")
        output_parts.append(f"  Status: {status}")
        output_parts.append(f"  Memory: {available_memory}MB")
        if timeout:
            output_parts.append(f"  Timeout: {timeout}")
        if max_instances:
            output_parts.append(f"  Max Instances: {max_instances}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_functions", is_read_only=True, service_type="cloudfunctions")
@require_google_service("cloudfunctions", "cloudfunctions_read")
async def list_functions(
    service,
    user_google_email: str,
    project_id: str,
    region: str = "us-central1",
) -> str:
    """
    Lists Cloud Functions in a project and region.

    Args:
        user_google_email (str): The user's Google email address. Required.
        project_id (str): The project ID. Required.
        region (str): The region. Defaults to "us-central1".

    Returns:
        str: Formatted list of Cloud Functions.
    """
    logger.info(
        f"[list_functions] Invoked. Email: '{user_google_email}', Project: {project_id}, Region: {region}"
    )
    return await list_functions_impl(service, user_google_email, project_id, region)


async def get_function_impl(
    service,
    user_google_email: str,
    function_name: str,
    project_id: Optional[str] = None,
    region: str = "us-central1",
) -> str:
    """Implementation for getting function details."""
    if project_id and not function_name.startswith("projects/"):
        full_name = (
            f"projects/{project_id}/locations/{region}/functions/{function_name}"
        )
    else:
        full_name = function_name

    func = await asyncio.to_thread(
        service.projects().locations().functions().get(name=full_name).execute
    )

    name = func.get("name", "")
    entry_point = func.get("entryPoint", "")
    runtime = func.get("runtime", "")
    status = func.get("status", "")
    description = func.get("description", "")
    available_memory = func.get("availableMemoryMb", "")
    timeout = func.get("timeout", "")
    max_instances = func.get("maxInstances", "")
    min_instances = func.get("minInstances", "")
    service_account = func.get("serviceAccountEmail", "")
    source_archive = func.get("sourceArchiveUrl", "")
    source_repository = func.get("sourceRepository", {}).get("url", "")
    https_trigger = func.get("httpsTriggerUrl", "")
    labels = func.get("labels", {})

    func_name = name.split("/")[-1]

    output_parts = [
        f"Cloud Function Details for {user_google_email}:",
        f"Name: {func_name}",
        f"Entry Point: {entry_point}",
        f"Runtime: {runtime}",
        f"Status: {status}",
    ]

    if description:
        output_parts.append(f"Description: {description}")

    output_parts.append(f"Memory: {available_memory}MB")

    if timeout:
        output_parts.append(f"Timeout: {timeout}")
    if max_instances:
        output_parts.append(f"Max Instances: {max_instances}")
    if min_instances:
        output_parts.append(f"Min Instances: {min_instances}")

    if service_account:
        output_parts.append(f"Service Account: {service_account}")

    if https_trigger:
        output_parts.append(f"HTTP Trigger URL: {https_trigger}")

    if source_archive:
        output_parts.append(f"Source Archive: {source_archive}")
    elif source_repository:
        output_parts.append(f"Source Repository: {source_repository}")

    if labels:
        output_parts.append("Labels:")
        for key, value in labels.items():
            output_parts.append(f"  {key}: {value}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_function", is_read_only=True, service_type="cloudfunctions")
@require_google_service("cloudfunctions", "cloudfunctions_read")
async def get_function(
    service,
    user_google_email: str,
    function_name: str,
    project_id: Optional[str] = None,
    region: str = "us-central1",
) -> str:
    """
    Gets details of a specific Cloud Function.

    Args:
        user_google_email (str): The user's Google email address. Required.
        function_name (str): The function name (or short name). Required.
        project_id (Optional[str]): The project ID. Required if function_name is short name.
        region (str): The region. Defaults to "us-central1".

    Returns:
        str: Full details of the Cloud Function.
    """
    logger.info(
        f"[get_function] Invoked. Email: '{user_google_email}', Function: {function_name}"
    )
    return await get_function_impl(
        service, user_google_email, function_name, project_id, region
    )


async def invoke_function_impl(
    service,
    user_google_email: str,
    function_name: str,
    project_id: Optional[str] = None,
    region: str = "us-central1",
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """Implementation for invoking a function."""
    if project_id and not function_name.startswith("projects/"):
        full_name = (
            f"projects/{project_id}/locations/{region}/functions/{function_name}"
        )
    else:
        full_name = function_name

    func = await asyncio.to_thread(
        service.projects().locations().functions().get(name=full_name).execute
    )

    https_trigger = func.get("httpsTriggerUrl", "")
    if not https_trigger:
        raise UserInputError(
            f"Function '{function_name}' does not have an HTTP trigger."
        )

    import httpx

    payload = json.dumps(data) if data else None

    async with httpx.AsyncClient() as client:
        response = await client.post(https_trigger, json=data, timeout=60.0)

    output_parts = [
        f"Cloud Function Invocation Result for {user_google_email}:",
        f"Function: {function_name}",
        f"URL: {https_trigger}",
        f"Status Code: {response.status_code}",
        "",
    ]

    try:
        result_json = response.json()
        output_parts.append("Response:")
        output_parts.append(json.dumps(result_json, indent=2))
    except Exception:
        output_parts.append("Response:")
        output_parts.append(response.text[:1000])

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("invoke_function", service_type="cloudfunctions")
@require_google_service("cloudfunctions", "cloudfunctions_execute")
async def invoke_function(
    service,
    user_google_email: str,
    function_name: str,
    project_id: Optional[str] = None,
    region: str = "us-central1",
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Invokes a Cloud Function via HTTP trigger.

    Args:
        user_google_email (str): The user's Google email address. Required.
        function_name (str): The function name. Required.
        project_id (Optional[str]): The project ID. Required if function_name is short name.
        region (str): The region. Defaults to "us-central1".
        data (Optional[Dict[str, Any]]): Data to pass to the function as JSON.

    Returns:
        str: Response from the Cloud Function.
    """
    logger.info(
        f"[invoke_function] Invoked. Email: '{user_google_email}', Function: {function_name}"
    )
    return await invoke_function_impl(
        service, user_google_email, function_name, project_id, region, data
    )


async def get_function_logs_impl(
    service,
    user_google_email: str,
    function_name: str,
    project_id: Optional[str] = None,
    region: str = "us-central1",
    max_entries: int = 20,
) -> str:
    """Implementation for getting function logs."""
    if project_id and not function_name.startswith("projects/"):
        full_name = (
            f"projects/{project_id}/locations/{region}/functions/{function_name}"
        )
    else:
        full_name = function_name

    import google.cloud.logging as cloud_logging

    logging_client = cloud_logging.Client(project=project_id)

    filter_str = f'resource.type="cloud_function" AND resource.labels.function_name="{function_name}"'

    if project_id:
        filter_str += f' AND resource.labels.project_id="{project_id}"'

    entries = list(
        logging_client.list_entries(filter_=filter_str, max_results=max_entries)
    )

    if not entries:
        return f"No log entries found for function '{function_name}' for {user_google_email}."

    output_parts = [
        f"Recent logs for function '{function_name}' ({len(entries)} entries):",
        "",
    ]

    for i, entry in enumerate(entries, 1):
        timestamp = entry.timestamp.isoformat() if entry.timestamp else "Unknown"
        severity = entry.severity or "DEFAULT"
        payload = entry.payload

        output_parts.append(f"Entry {i}:")
        output_parts.append(f"  Time: {timestamp}")
        output_parts.append(f"  Severity: {severity}")

        if isinstance(payload, str):
            output_parts.append(f"  Message: {payload[:300]}")
        elif isinstance(payload, dict):
            msg = payload.get("message", str(payload))
            output_parts.append(f"  Message: {msg[:300]}")

        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors(
    "get_function_logs", is_read_only=True, service_type="cloudfunctions"
)
@require_google_service("cloudfunctions", "cloudfunctions_read")
async def get_function_logs(
    service,
    user_google_email: str,
    function_name: str,
    project_id: Optional[str] = None,
    region: str = "us-central1",
    max_entries: int = 20,
) -> str:
    """
    Gets recent log entries for a Cloud Function.

    Args:
        user_google_email (str): The user's Google email address. Required.
        function_name (str): The function name. Required.
        project_id (Optional[str]): The project ID. Required if function_name is short name.
        region (str): The region. Defaults to "us-central1".
        max_entries (int): Maximum log entries to return. Defaults to 20.

    Returns:
        str: Recent log entries.
    """
    logger.info(
        f"[get_function_logs] Invoked. Email: '{user_google_email}', Function: {function_name}"
    )
    return await get_function_logs_impl(
        service, user_google_email, function_name, project_id, region, max_entries
    )
