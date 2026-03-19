"""
Google Cloud Storage MCP Tools

This module provides MCP tools for interacting with Google Cloud Storage API.
"""

import logging
import asyncio
import io
import base64
from typing import List, Optional, Dict, Any

from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


def _format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


async def list_buckets_impl(
    service,
    user_google_email: str,
    project_id: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """Implementation for listing buckets."""
    params = {"maxResults": max_results}
    if project_id:
        params["project"] = project_id

    buckets = await asyncio.to_thread(service.buckets().list(**params).execute)

    items = buckets.get("items", [])
    if not items:
        return f"No buckets found for {user_google_email}."

    output_parts = [
        f"Found {len(items)} bucket(s) for {user_google_email}:",
        "",
    ]

    for bucket in items:
        name = bucket.get("name", "Unknown")
        location = bucket.get("location", "Unknown")
        storage_class = bucket.get("storageClass", "Unknown")
        created = bucket.get("timeCreated", "")
        updated = bucket.get("updated", "")

        output_parts.append(f"- {name}")
        output_parts.append(f"  Location: {location}")
        output_parts.append(f"  Storage Class: {storage_class}")
        if created:
            output_parts.append(f"  Created: {created}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_buckets", is_read_only=True, service_type="storage")
@require_google_service("storage", "storage_read")
async def list_buckets(
    service,
    user_google_email: str,
    project_id: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """
    Lists buckets in a Google Cloud Storage project.

    Args:
        user_google_email (str): The user's Google email address. Required.
        project_id (Optional[str]): The project ID. If not provided, lists all accessible buckets.
        max_results (int): Maximum number of buckets to return. Defaults to 50.

    Returns:
        str: Formatted list of buckets.
    """
    logger.info(
        f"[list_buckets] Invoked. Email: '{user_google_email}', Project: {project_id}"
    )
    return await list_buckets_impl(service, user_google_email, project_id, max_results)


async def get_bucket_impl(
    service,
    user_google_email: str,
    bucket_name: str,
) -> str:
    """Implementation for getting bucket details."""
    bucket = await asyncio.to_thread(service.buckets().get(bucket=bucket_name).execute)

    name = bucket.get("name", "Unknown")
    location = bucket.get("location", "Unknown")
    storage_class = bucket.get("storageClass", "Unknown")
    created = bucket.get("timeCreated", "")
    updated = bucket.get("updated", "")

    versioning = bucket.get("versioning", {}).get("enabled", False)
    logging = bucket.get("logging", {}).get("logBucket", "")
    lifecycle = bucket.get("lifecycle", {}).get("rule", [])

    cors = bucket.get("cors", [])

    output_parts = [
        f"Bucket Details for {user_google_email}:",
        f"Name: {name}",
        f"Location: {location}",
        f"Storage Class: {storage_class}",
        f"Created: {created}",
        f"Updated: {updated}",
        "",
        f"Versioning: {'Enabled' if versioning else 'Disabled'}",
        f"Logging Bucket: {logging if logging else 'None'}",
    ]

    if lifecycle:
        output_parts.append(f"Lifecycle Rules: {len(lifecycle)} rule(s)")

    if cors:
        output_parts.append(f"CORS: {len(cors)} configuration(s)")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_bucket", is_read_only=True, service_type="storage")
@require_google_service("storage", "storage_read")
async def get_bucket(
    service,
    user_google_email: str,
    bucket_name: str,
) -> str:
    """
    Gets metadata for a specific bucket.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name of the bucket. Required.

    Returns:
        str: Full metadata of the bucket.
    """
    logger.info(
        f"[get_bucket] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}"
    )
    return await get_bucket_impl(service, user_google_email, bucket_name)


async def create_bucket_impl(
    service,
    user_google_email: str,
    bucket_name: str,
    location: str = "US",
    storage_class: str = "STANDARD",
    project_id: Optional[str] = None,
) -> str:
    """Implementation for creating a bucket."""
    if not project_id:
        raise UserInputError("project_id is required to create a bucket.")

    bucket_data = {
        "name": bucket_name,
        "location": location,
        "storageClass": storage_class,
    }

    created_bucket = await asyncio.to_thread(
        service.buckets().insert(project=project_id, body=bucket_data).execute
    )

    name = created_bucket.get("name", bucket_name)
    created = created_bucket.get("timeCreated", "")

    text_output = (
        f"Successfully created bucket for {user_google_email}:\n"
        f"Name: {name}\n"
        f"Location: {location}\n"
        f"Storage Class: {storage_class}\n"
        f"Created: {created}"
    )

    logger.info(f"Successfully created bucket: {bucket_name}")
    return text_output


@server.tool()
@handle_http_errors("create_bucket", service_type="storage")
@require_google_service("storage", "storage_write")
async def create_bucket(
    service,
    user_google_email: str,
    bucket_name: str,
    location: str = "US",
    storage_class: str = "STANDARD",
    project_id: Optional[str] = None,
) -> str:
    """
    Creates a new bucket in Google Cloud Storage.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name for the new bucket. Must be globally unique. Required.
        location (str): The location for the bucket. Defaults to "US".
        storage_class (str): Default storage class. Defaults to "STANDARD".
        project_id (Optional[str]): The project ID. Required for new buckets.

    Returns:
        str: Confirmation message with bucket details.
    """
    logger.info(
        f"[create_bucket] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}"
    )
    return await create_bucket_impl(
        service, user_google_email, bucket_name, location, storage_class, project_id
    )


async def delete_bucket_impl(
    service,
    user_google_email: str,
    bucket_name: str,
) -> str:
    """Implementation for deleting a bucket."""
    await asyncio.to_thread(service.buckets().delete(bucket=bucket_name).execute)

    text_output = (
        f"Successfully deleted bucket '{bucket_name}' for {user_google_email}."
    )

    logger.info(f"Successfully deleted bucket: {bucket_name}")
    return text_output


@server.tool()
@handle_http_errors("delete_bucket", service_type="storage")
@require_google_service("storage", "storage_write")
async def delete_bucket(
    service,
    user_google_email: str,
    bucket_name: str,
) -> str:
    """
    Deletes a bucket from Google Cloud Storage.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name of the bucket to delete. Required.

    Returns:
        str: Confirmation message of the deletion.
    """
    logger.info(
        f"[delete_bucket] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}"
    )
    return await delete_bucket_impl(service, user_google_email, bucket_name)


async def list_objects_impl(
    service,
    user_google_email: str,
    bucket_name: str,
    prefix: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """Implementation for listing objects."""
    params = {
        "bucket": bucket_name,
        "maxResults": max_results,
    }
    if prefix:
        params["prefix"] = prefix

    objects = await asyncio.to_thread(service.objects().list(**params).execute)

    items = objects.get("items", [])
    if not items:
        return f"No objects found in bucket '{bucket_name}' for {user_google_email}."

    output_parts = [
        f"Found {len(items)} object(s) in bucket '{bucket_name}' for {user_google_email}:",
        "",
    ]

    for obj in items:
        name = obj.get("name", "Unknown")
        size = obj.get("size", "0")
        content_type = obj.get("contentType", "Unknown")
        updated = obj.get("updated", "")

        size_str = _format_size(int(size)) if size.isdigit() else size

        output_parts.append(f"- {name}")
        output_parts.append(f"  Size: {size_str}")
        output_parts.append(f"  Type: {content_type}")
        output_parts.append(f"  Updated: {updated}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_objects", is_read_only=True, service_type="storage")
@require_google_service("storage", "storage_read")
async def list_objects(
    service,
    user_google_email: str,
    bucket_name: str,
    prefix: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """
    Lists objects in a bucket.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name of the bucket. Required.
        prefix (Optional[str]): Prefix to filter objects.
        max_results (int): Maximum number of objects to return. Defaults to 50.

    Returns:
        str: Formatted list of objects.
    """
    logger.info(
        f"[list_objects] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}, Prefix: {prefix}"
    )
    return await list_objects_impl(
        service, user_google_email, bucket_name, prefix, max_results
    )


async def get_object_impl(
    service,
    user_google_email: str,
    bucket_name: str,
    object_name: str,
) -> str:
    """Implementation for getting object details."""
    obj = await asyncio.to_thread(
        service.objects().get(bucket=bucket_name, object=object_name).execute
    )

    name = obj.get("name", "Unknown")
    size = obj.get("size", "0")
    content_type = obj.get("contentType", "Unknown")
    created = obj.get("timeCreated", "")
    updated = obj.get("updated", "")
    md5_hash = obj.get("md5Hash", "")
    cache_control = obj.get("cacheControl", "")
    content_disposition = obj.get("contentDisposition", "")
    metadata = obj.get("metadata", {})

    size_str = _format_size(int(size)) if size.isdigit() else size

    output_parts = [
        f"Object Details for {user_google_email}:",
        f"Name: {name}",
        f"Bucket: {bucket_name}",
        f"Size: {size_str}",
        f"Content Type: {content_type}",
        f"Created: {created}",
        f"Updated: {updated}",
    ]

    if md5_hash:
        output_parts.append(f"MD5 Hash: {md5_hash}")
    if cache_control:
        output_parts.append(f"Cache Control: {cache_control}")
    if content_disposition:
        output_parts.append(f"Content Disposition: {content_disposition}")
    if metadata:
        output_parts.append("")
        output_parts.append("Custom Metadata:")
        for key, value in metadata.items():
            output_parts.append(f"  {key}: {value}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_object", is_read_only=True, service_type="storage")
@require_google_service("storage", "storage_read")
async def get_object(
    service,
    user_google_email: str,
    bucket_name: str,
    object_name: str,
) -> str:
    """
    Gets metadata for a specific object.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name of the bucket. Required.
        object_name (str): The name of the object. Required.

    Returns:
        str: Full metadata of the object.
    """
    logger.info(
        f"[get_object] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}, Object: {object_name}"
    )
    return await get_object_impl(service, user_google_email, bucket_name, object_name)


async def upload_object_impl(
    service,
    user_google_email: str,
    bucket_name: str,
    object_name: str,
    content: str,
    content_type: str = "text/plain",
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Implementation for uploading an object."""
    content_bytes = content.encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(content_bytes), mimetype=content_type)

    body = {
        "name": object_name,
        "contentType": content_type,
    }
    if metadata:
        body["metadata"] = metadata

    uploaded = await asyncio.to_thread(
        service.objects()
        .insert(
            bucket=bucket_name,
            body=body,
            media_body=media,
        )
        .execute
    )

    name = uploaded.get("name", object_name)
    size = uploaded.get("size", "0")
    created = uploaded.get("timeCreated", "")

    size_str = _format_size(int(size)) if size.isdigit() else size

    text_output = (
        f"Successfully uploaded object for {user_google_email}:\n"
        f"Bucket: {bucket_name}\n"
        f"Object: {name}\n"
        f"Size: {size_str}\n"
        f"Created: {created}"
    )

    logger.info(f"Successfully uploaded object: {object_name}")
    return text_output


@server.tool()
@handle_http_errors("upload_object", service_type="storage")
@require_google_service("storage", "storage_write")
async def upload_object(
    service,
    user_google_email: str,
    bucket_name: str,
    object_name: str,
    content: str,
    content_type: str = "text/plain",
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """
    Uploads an object to a bucket.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name of the bucket. Required.
        object_name (str): The name for the object. Required.
        content (str): The content to upload (as string). Required.
        content_type (str): The MIME type. Defaults to "text/plain".
        metadata (Optional[Dict[str, str]]): Custom metadata key-value pairs.

    Returns:
        str: Confirmation message with object details.
    """
    logger.info(
        f"[upload_object] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}, Object: {object_name}"
    )
    return await upload_object_impl(
        service,
        user_google_email,
        bucket_name,
        object_name,
        content,
        content_type,
        metadata,
    )


async def delete_object_impl(
    service,
    user_google_email: str,
    bucket_name: str,
    object_name: str,
) -> str:
    """Implementation for deleting an object."""
    await asyncio.to_thread(
        service.objects().delete(bucket=bucket_name, object=object_name).execute
    )

    text_output = f"Successfully deleted object '{object_name}' from bucket '{bucket_name}' for {user_google_email}."

    logger.info(f"Successfully deleted object: {object_name}")
    return text_output


@server.tool()
@handle_http_errors("delete_object", service_type="storage")
@require_google_service("storage", "storage_write")
async def delete_object(
    service,
    user_google_email: str,
    bucket_name: str,
    object_name: str,
) -> str:
    """
    Deletes an object from a bucket.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name of the bucket. Required.
        object_name (str): The name of the object to delete. Required.

    Returns:
        str: Confirmation message of the deletion.
    """
    logger.info(
        f"[delete_object] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}, Object: {object_name}"
    )
    return await delete_object_impl(
        service, user_google_email, bucket_name, object_name
    )


async def get_bucket_acl_impl(
    service,
    user_google_email: str,
    bucket_name: str,
) -> str:
    """Implementation for getting bucket ACL."""
    acl = await asyncio.to_thread(
        service.bucketAccessControls().list(bucket=bucket_name).execute
    )

    items = acl.get("items", [])
    if not items:
        return f"No ACL entries found for bucket '{bucket_name}'."

    output_parts = [
        f"ACL for bucket '{bucket_name}':",
        "",
    ]

    for entry in items:
        entity = entry.get("entity", "Unknown")
        role = entry.get("role", "Unknown")
        email = entry.get("email", "")
        domain = entry.get("domain", "")

        output_parts.append(f"- {entity}")
        output_parts.append(f"  Role: {role}")
        if email:
            output_parts.append(f"  Email: {email}")
        if domain:
            output_parts.append(f"  Domain: {domain}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_bucket_acl", is_read_only=True, service_type="storage")
@require_google_service("storage", "storage_read")
async def get_bucket_acl(
    service,
    user_google_email: str,
    bucket_name: str,
) -> str:
    """
    Gets the ACL for a bucket.

    Args:
        user_google_email (str): The user's Google email address. Required.
        bucket_name (str): The name of the bucket. Required.

    Returns:
        str: Formatted ACL entries.
    """
    logger.info(
        f"[get_bucket_acl] Invoked. Email: '{user_google_email}', Bucket: {bucket_name}"
    )
    return await get_bucket_acl_impl(service, user_google_email, bucket_name)
