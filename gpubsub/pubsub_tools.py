"""
Google Cloud Pub/Sub MCP Tools

This module provides MCP tools for interacting with Google Cloud Pub/Sub API.
"""

import logging
import asyncio
import base64
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def list_topics_impl(
    service,
    user_google_email: str,
    project_id: str,
    max_results: int = 50,
) -> str:
    """Implementation for listing topics."""
    project_path = f"projects/{project_id}"

    topics = await asyncio.to_thread(
        service.projects()
        .topics()
        .list(project=project_path, maxResults=max_results)
        .execute
    )

    items = topics.get("topics", [])
    if not items:
        return f"No topics found in project '{project_id}' for {user_google_email}."

    output_parts = [
        f"Found {len(items)} topic(s) in project '{project_id}' for {user_google_email}:",
        "",
    ]

    for topic in items:
        name = topic.get("name", "")
        messages = topic.get("messageRetentionDuration", "")
        ack_deadline = topic.get("ackDeadlineSeconds", "")

        output_parts.append(
            f"- {name.replace('projects/' + project_id + '/topics/', '')}"
        )
        output_parts.append(f"  Full name: {name}")
        if messages:
            output_parts.append(f"  Message retention: {messages}")
        if ack_deadline:
            output_parts.append(f"  ACK deadline: {ack_deadline}s")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_topics", is_read_only=True, service_type="pubsub")
@require_google_service("pubsub", "pubsub_read")
async def list_topics(
    service,
    user_google_email: str,
    project_id: str,
    max_results: int = 50,
) -> str:
    """
    Lists topics in a Google Cloud Pub/Sub project.

    Args:
        user_google_email (str): The user's Google email address. Required.
        project_id (str): The project ID. Required.
        max_results (int): Maximum number of topics to return. Defaults to 50.

    Returns:
        str: Formatted list of topics.
    """
    logger.info(
        f"[list_topics] Invoked. Email: '{user_google_email}', Project: {project_id}"
    )
    return await list_topics_impl(service, user_google_email, project_id, max_results)


async def get_topic_impl(
    service,
    user_google_email: str,
    topic_name: str,
) -> str:
    """Implementation for getting topic details."""
    topic = await asyncio.to_thread(
        service.projects().topics().get(topic=topic_name).execute
    )

    name = topic.get("name", "")
    messages = topic.get("messageRetentionDuration", "")
    ack_deadline = topic.get("ackDeadlineSeconds", "")
    labels = topic.get("labels", {})
    kms_key = topic.get("kmsKeyName", "")
    region = topic.get("messageStoragePolicy", {}).get("allowedPersistenceRegions", [])

    output_parts = [
        f"Topic Details for {user_google_email}:",
        f"Name: {name}",
    ]

    if messages:
        output_parts.append(f"Message Retention: {messages}")
    if ack_deadline:
        output_parts.append(f"ACK Deadline: {ack_deadline}s")
    if labels:
        output_parts.append("Labels:")
        for key, value in labels.items():
            output_parts.append(f"  {key}: {value}")
    if kms_key:
        output_parts.append(f"KMS Key: {kms_key}")
    if region:
        output_parts.append(f"Allowed Regions: {', '.join(region)}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_topic", is_read_only=True, service_type="pubsub")
@require_google_service("pubsub", "pubsub_read")
async def get_topic(
    service,
    user_google_email: str,
    topic_name: str,
) -> str:
    """
    Gets details of a specific topic.

    Args:
        user_google_email (str): The user's Google email address. Required.
        topic_name (str): The topic name (projects/{project}/topics/{topic}). Required.

    Returns:
        str: Full details of the topic.
    """
    logger.info(
        f"[get_topic] Invoked. Email: '{user_google_email}', Topic: {topic_name}"
    )
    return await get_topic_impl(service, user_google_email, topic_name)


async def create_topic_impl(
    service,
    user_google_email: str,
    topic_name: str,
    project_id: Optional[str] = None,
    ack_deadline: int = 30,
    message_retention: Optional[str] = None,
) -> str:
    """Implementation for creating a topic."""
    if project_id and not topic_name.startswith("projects/"):
        full_topic_name = f"projects/{project_id}/topics/{topic_name}"
    else:
        full_topic_name = topic_name

    topic_body = {
        "ackDeadlineSeconds": ack_deadline,
    }

    if message_retention:
        topic_body["messageRetentionDuration"] = message_retention

    created = await asyncio.to_thread(
        service.projects()
        .topics()
        .create(body=topic_body, name=full_topic_name)
        .execute
    )

    name = created.get("name", full_topic_name)
    ack = created.get("ackDeadlineSeconds", ack_deadline)

    text_output = (
        f"Successfully created topic for {user_google_email}:\n"
        f"Name: {name}\n"
        f"ACK Deadline: {ack}s"
    )

    logger.info(f"Successfully created topic: {name}")
    return text_output


@server.tool()
@handle_http_errors("create_topic", service_type="pubsub")
@require_google_service("pubsub", "pubsub_write")
async def create_topic(
    service,
    user_google_email: str,
    topic_name: str,
    project_id: Optional[str] = None,
    ack_deadline: int = 30,
    message_retention: Optional[str] = None,
) -> str:
    """
    Creates a new Pub/Sub topic.

    Args:
        user_google_email (str): The user's Google email address. Required.
        topic_name (str): The name for the topic. If project_id provided, can be short name. Required.
        project_id (Optional[str]): The project ID. If not provided, topic_name must be full path.
        ack_deadline (int): ACK deadline in seconds. Defaults to 30.
        message_retention (Optional[str]): Message retention duration (e.g., "604800s").

    Returns:
        str: Confirmation message with topic details.
    """
    logger.info(
        f"[create_topic] Invoked. Email: '{user_google_email}', Topic: {topic_name}"
    )
    return await create_topic_impl(
        service,
        user_google_email,
        topic_name,
        project_id,
        ack_deadline,
        message_retention,
    )


async def delete_topic_impl(
    service,
    user_google_email: str,
    topic_name: str,
) -> str:
    """Implementation for deleting a topic."""
    await asyncio.to_thread(
        service.projects().topics().delete(topic=topic_name).execute
    )

    text_output = f"Successfully deleted topic '{topic_name}' for {user_google_email}."

    logger.info(f"Successfully deleted topic: {topic_name}")
    return text_output


@server.tool()
@handle_http_errors("delete_topic", service_type="pubsub")
@require_google_service("pubsub", "pubsub_write")
async def delete_topic(
    service,
    user_google_email: str,
    topic_name: str,
) -> str:
    """
    Deletes a Pub/Sub topic.

    Args:
        user_google_email (str): The user's Google email address. Required.
        topic_name (str): The topic name to delete. Required.

    Returns:
        str: Confirmation message of the deletion.
    """
    logger.info(
        f"[delete_topic] Invoked. Email: '{user_google_email}', Topic: {topic_name}"
    )
    return await delete_topic_impl(service, user_google_email, topic_name)


async def publish_message_impl(
    service,
    user_google_email: str,
    topic_name: str,
    messages: List[Dict[str, Any]],
) -> str:
    """Implementation for publishing messages."""
    if not messages:
        raise UserInputError("At least one message must be provided.")

    pub_messages = []
    for msg in messages:
        data = msg.get("data", "")
        if isinstance(data, str):
            data_bytes = base64.b64encode(data.encode("utf-8")).decode("utf-8")
        else:
            data_bytes = base64.b64encode(str(data).encode("utf-8")).decode("utf-8")

        pub_msg = {"data": data_bytes}

        attributes = msg.get("attributes", {})
        if attributes:
            pub_msg["attributes"] = attributes

        pub_messages.append(pub_msg)

    body = {"messages": pub_messages}

    result = await asyncio.to_thread(
        service.projects().topics().publish(topic=topic_name, body=body).execute
    )

    message_ids = result.get("messageIds", [])

    text_output = (
        f"Successfully published {len(message_ids)} message(s) to topic '{topic_name}' "
        f"for {user_google_email}. Message IDs: {', '.join(message_ids[:5])}"
        + (f" ... and {len(message_ids) - 5} more" if len(message_ids) > 5 else "")
    )

    logger.info(f"Successfully published {len(message_ids)} messages")
    return text_output


@server.tool()
@handle_http_errors("publish_message", service_type="pubsub")
@require_google_service("pubsub", "pubsub_write")
async def publish_message(
    service,
    user_google_email: str,
    topic_name: str,
    messages: List[Dict[str, Any]],
) -> str:
    """
    Publishes messages to a topic.

    Args:
        user_google_email (str): The user's Google email address. Required.
        topic_name (str): The topic name. Required.
        messages (List[Dict[str, Any]]): List of messages with 'data' and optional 'attributes'. Required.

    Returns:
        str: Confirmation with message IDs.
    """
    logger.info(
        f"[publish_message] Invoked. Email: '{user_google_email}', Topic: {topic_name}, "
        f"Count: {len(messages)}"
    )
    return await publish_message_impl(service, user_google_email, topic_name, messages)


async def list_subscriptions_impl(
    service,
    user_google_email: str,
    project_id: str,
    topic_name: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """Implementation for listing subscriptions."""
    if topic_name:
        result = await asyncio.to_thread(
            service.projects().topics().subscriptions().list(topic=topic_name).execute
        )
        subscriptions = result.get("subscription", [])
    else:
        result = await asyncio.to_thread(
            service.projects()
            .subscriptions()
            .list(project=f"projects/{project_id}", maxResults=max_results)
            .execute
        )
        subscriptions = result.get("subscriptions", [])

    if not subscriptions:
        return f"No subscriptions found for {user_google_email}."

    output_parts = [
        f"Found {len(subscriptions)} subscription(s) for {user_google_email}:",
        "",
    ]

    for sub in subscriptions:
        name = sub.get("name", "")
        topic = sub.get("topic", "")
        ack_deadline = sub.get("ackDeadlineSeconds", "")
        push_endpoint = sub.get("pushConfig", {}).get("pushEndpoint", "")
        retain_acked = sub.get("retainAckedMessages", False)

        output_parts.append(f"- {name}")
        output_parts.append(f"  Topic: {topic}")
        if ack_deadline:
            output_parts.append(f"  ACK Deadline: {ack_deadline}s")
        if push_endpoint:
            output_parts.append(f"  Push Endpoint: {push_endpoint}")
        output_parts.append(f"  Retain Acknowledged: {retain_acked}")
        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("list_subscriptions", is_read_only=True, service_type="pubsub")
@require_google_service("pubsub", "pubsub_read")
async def list_subscriptions(
    service,
    user_google_email: str,
    project_id: str,
    topic_name: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """
    Lists subscriptions in a project or for a topic.

    Args:
        user_google_email (str): The user's Google email address. Required.
        project_id (str): The project ID. Required.
        topic_name (Optional[str]): Filter by topic.
        max_results (int): Maximum number to return. Defaults to 50.

    Returns:
        str: Formatted list of subscriptions.
    """
    logger.info(
        f"[list_subscriptions] Invoked. Email: '{user_google_email}', Project: {project_id}"
    )
    return await list_subscriptions_impl(
        service, user_google_email, project_id, topic_name, max_results
    )


async def get_subscription_impl(
    service,
    user_google_email: str,
    subscription_name: str,
) -> str:
    """Implementation for getting subscription details."""
    sub = await asyncio.to_thread(
        service.projects().subscriptions().get(subscription=subscription_name).execute
    )

    name = sub.get("name", "")
    topic = sub.get("topic", "")
    ack_deadline = sub.get("ackDeadlineSeconds", "")
    retain_acked = sub.get("retainAckedMessages", False)
    expiration = sub.get("expirationPolicy", {}).get("ttl", "")
    push_endpoint = sub.get("pushConfig", {}).get("pushEndpoint", "")
    dead_letter = sub.get("deadLetterPolicy", {}).get("deadLetterTopic", "")

    output_parts = [
        f"Subscription Details for {user_google_email}:",
        f"Name: {name}",
        f"Topic: {topic}",
    ]

    if ack_deadline:
        output_parts.append(f"ACK Deadline: {ack_deadline}s")
    output_parts.append(f"Retain Acknowledged: {retain_acked}")
    if expiration:
        output_parts.append(f"Expiration Policy: {expiration}")
    if push_endpoint:
        output_parts.append(f"Push Endpoint: {push_endpoint}")
    if dead_letter:
        output_parts.append(f"Dead Letter Topic: {dead_letter}")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_subscription", is_read_only=True, service_type="pubsub")
@require_google_service("pubsub", "pubsub_read")
async def get_subscription(
    service,
    user_google_email: str,
    subscription_name: str,
) -> str:
    """
    Gets details of a specific subscription.

    Args:
        user_google_email (str): The user's Google email address. Required.
        subscription_name (str): The subscription name. Required.

    Returns:
        str: Full details of the subscription.
    """
    logger.info(
        f"[get_subscription] Invoked. Email: '{user_google_email}', Subscription: {subscription_name}"
    )
    return await get_subscription_impl(service, user_google_email, subscription_name)


async def create_subscription_impl(
    service,
    user_google_email: str,
    subscription_name: str,
    topic_name: str,
    ack_deadline: int = 30,
    push_endpoint: Optional[str] = None,
) -> str:
    """Implementation for creating a subscription."""
    sub_body = {
        "topic": topic_name,
        "ackDeadlineSeconds": ack_deadline,
    }

    if push_endpoint:
        sub_body["pushConfig"] = {"pushEndpoint": push_endpoint}

    created = await asyncio.to_thread(
        service.projects()
        .subscriptions()
        .create(body=sub_body, name=subscription_name)
        .execute
    )

    name = created.get("name", subscription_name)
    topic = created.get("topic", topic_name)
    ack = created.get("ackDeadlineSeconds", ack_deadline)

    text_output = (
        f"Successfully created subscription for {user_google_email}:\n"
        f"Name: {name}\n"
        f"Topic: {topic}\n"
        f"ACK Deadline: {ack}s"
    )

    logger.info(f"Successfully created subscription: {name}")
    return text_output


@server.tool()
@handle_http_errors("create_subscription", service_type="pubsub")
@require_google_service("pubsub", "pubsub_write")
async def create_subscription(
    service,
    user_google_email: str,
    subscription_name: str,
    topic_name: str,
    ack_deadline: int = 30,
    push_endpoint: Optional[str] = None,
) -> str:
    """
    Creates a new Pub/Sub subscription.

    Args:
        user_google_email (str): The user's Google email address. Required.
        subscription_name (str): The name for the subscription. Required.
        topic_name (str): The topic to subscribe to. Required.
        ack_deadline (int): ACK deadline in seconds. Defaults to 30.
        push_endpoint (Optional[str]): Push endpoint URL.

    Returns:
        str: Confirmation message with subscription details.
    """
    logger.info(
        f"[create_subscription] Invoked. Email: '{user_google_email}', "
        f"Subscription: {subscription_name}, Topic: {topic_name}"
    )
    return await create_subscription_impl(
        service,
        user_google_email,
        subscription_name,
        topic_name,
        ack_deadline,
        push_endpoint,
    )


async def delete_subscription_impl(
    service,
    user_google_email: str,
    subscription_name: str,
) -> str:
    """Implementation for deleting a subscription."""
    await asyncio.to_thread(
        service.projects()
        .subscriptions()
        .delete(subscription=subscription_name)
        .execute
    )

    text_output = f"Successfully deleted subscription '{subscription_name}' for {user_google_email}."

    logger.info(f"Successfully deleted subscription: {subscription_name}")
    return text_output


@server.tool()
@handle_http_errors("delete_subscription", service_type="pubsub")
@require_google_service("pubsub", "pubsub_write")
async def delete_subscription(
    service,
    user_google_email: str,
    subscription_name: str,
) -> str:
    """
    Deletes a Pub/Sub subscription.

    Args:
        user_google_email (str): The user's Google email address. Required.
        subscription_name (str): The subscription name to delete. Required.

    Returns:
        str: Confirmation message of the deletion.
    """
    logger.info(
        f"[delete_subscription] Invoked. Email: '{user_google_email}', Subscription: {subscription_name}"
    )
    return await delete_subscription_impl(service, user_google_email, subscription_name)


async def pull_messages_impl(
    service,
    user_google_email: str,
    subscription_name: str,
    max_messages: int = 10,
    ack_messages: bool = True,
) -> str:
    """Implementation for pulling messages."""
    body = {
        "maxMessages": max_messages,
        "returnImmediately": False,
    }

    result = await asyncio.to_thread(
        service.projects()
        .subscriptions()
        .pull(subscription=subscription_name, body=body)
        .execute
    )

    received_messages = result.get("receivedMessages", [])

    if not received_messages:
        return f"No messages available in subscription '{subscription_name}' for {user_google_email}."

    output_parts = [
        f"Pulled {len(received_messages)} message(s) from subscription '{subscription_name}' for {user_google_email}:",
        "",
    ]

    for i, msg_wrapper in enumerate(received_messages, 1):
        msg = msg_wrapper.get("message", {})
        ack_id = msg_wrapper.get("ackId", "")

        data = msg.get("data", "")
        if data:
            try:
                decoded = base64.b64decode(data).decode("utf-8")
            except Exception:
                decoded = f"<binary: {len(data)} bytes>"
        else:
            decoded = "(empty)"

        attributes = msg.get("attributes", {})
        message_id = msg.get("messageId", "")
        publish_time = msg.get("publishTime", "")

        output_parts.append(f"Message {i}:")
        output_parts.append(f"  ID: {message_id}")
        output_parts.append(f"  Published: {publish_time}")
        output_parts.append(
            f"  Data: {decoded[:200]}" + ("..." if len(decoded) > 200 else "")
        )
        if attributes:
            output_parts.append(f"  Attributes:")
            for key, value in attributes.items():
                output_parts.append(f"    {key}: {value}")
        output_parts.append("")

    if ack_messages and received_messages:
        ack_ids = [msg.get("ackId", "") for msg in received_messages]
        await asyncio.to_thread(
            service.projects()
            .subscriptions()
            .acknowledge(
                subscription=subscription_name,
                body={"ackIds": ack_ids},
            )
            .execute
        )
        output_parts.append(f"Acknowledged {len(received_messages)} message(s).")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("pull_messages", is_read_only=True, service_type="pubsub")
@require_google_service("pubsub", "pubsub_read")
async def pull_messages(
    service,
    user_google_email: str,
    subscription_name: str,
    max_messages: int = 10,
    ack_messages: bool = True,
) -> str:
    """
    Pulls messages from a subscription.

    Args:
        user_google_email (str): The user's Google email address. Required.
        subscription_name (str): The subscription name. Required.
        max_messages (int): Maximum messages to pull. Defaults to 10.
        ack_messages (bool): Whether to acknowledge messages after pulling. Defaults to True.

    Returns:
        str: Pulled messages.
    """
    logger.info(
        f"[pull_messages] Invoked. Email: '{user_google_email}', Subscription: {subscription_name}, "
        f"Max: {max_messages}"
    )
    return await pull_messages_impl(
        service, user_google_email, subscription_name, max_messages, ack_messages
    )
