"""
Google Maps/Places MCP Tools

This module provides MCP tools for interacting with Google Maps/Places API.
Note: This uses the Places API which requires an API key, not OAuth.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors, UserInputError
from core.server import server

logger = logging.getLogger(__name__)


async def search_places_impl(
    service,
    user_google_email: str,
    query: str,
    location: Optional[str] = None,
    radius: int = 5000,
    max_results: int = 10,
) -> str:
    """Implementation for searching places."""
    params = {
        "query": query,
        "maxResults": max_results,
    }

    if location:
        params["locationBias"] = f"circle:{radius}@{location}"
    else:
        params["textQuery"] = query

    places = await asyncio.to_thread(service.places().searchText(body=params).execute)

    results = places.get("places", [])
    if not results:
        return f"No places found for query '{query}'."

    output_parts = [
        f"Found {len(results)} place(s) for '{query}':",
        "",
    ]

    for i, place in enumerate(results, 1):
        name = place.get("displayName", {}).get("text", "Unknown")
        place_id = place.get("id", "")
        address = place.get("formattedAddress", "")
        location = place.get("location", {})
        lat = location.get("latitude", "")
        lng = location.get("longitude", "")

        rating = place.get("rating", "")
        user_ratings = place.get("userRatingCount", "")

        output_parts.append(f"{i}. {name}")
        output_parts.append(f"   Place ID: {place_id}")
        if address:
            output_parts.append(f"   Address: {address}")
        if lat and lng:
            output_parts.append(f"   Location: {lat}, {lng}")
        if rating:
            output_parts.append(f"   Rating: {rating}/5 ({user_ratings} reviews)")

        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("search_places", is_read_only=True, service_type="maps")
@require_google_service("maps", "maps")
async def search_places(
    service,
    user_google_email: str,
    query: str,
    location: Optional[str] = None,
    radius: int = 5000,
    max_results: int = 10,
) -> str:
    """
    Searches for places using Google Places API.

    Args:
        user_google_email (str): The user's Google email address. Required.
        query (str): The search query string. Required.
        location (Optional[str]): The latitude/longitude around which to search (e.g., "37.7749,-122.4194").
            If not provided, uses the query text alone.
        radius (int): The search radius in meters. Defaults to 5000.
        max_results (int): Maximum number of results. Defaults to 10.

    Returns:
        str: Formatted list of search results.
    """
    logger.info(
        f"[search_places] Invoked. Email: '{user_google_email}', Query: '{query}', "
        f"Location: {location}, Radius: {radius}"
    )
    return await search_places_impl(
        service, user_google_email, query, location, radius, max_results
    )


async def get_place_details_impl(
    service,
    user_google_email: str,
    place_id: str,
) -> str:
    """Implementation for getting place details."""
    place = await asyncio.to_thread(
        service.places().get(name=f"places/{place_id}").execute
    )

    name = place.get("displayName", {}).get("text", "Unknown")
    address = place.get("formattedAddress", "")
    location = place.get("location", {})
    lat = location.get("latitude", "")
    lng = location.get("longitude", "")

    rating = place.get("rating", "")
    user_ratings = place.get("userRatingCount", "")
    price_level = place.get("priceLevel", "")

    website = place.get("websiteUri", "")
    phone = place.get("nationalPhoneNumber", "")

    hours = place.get("regularOpeningHours", {})
    weekday = hours.get("weekdayDescription", [])

    reviews = place.get("reviews", [])

    output_parts = [
        f"Place Details for {user_google_email}:",
        f"Name: {name}",
        f"Place ID: {place_id}",
    ]

    if address:
        output_parts.append(f"Address: {address}")

    if lat and lng:
        output_parts.append(f"Location: {lat}, {lng}")

    if rating:
        output_parts.append(f"Rating: {rating}/5 ({user_ratings} reviews)")

    if price_level:
        price_symbols = {
            "PRICE_LEVEL_UNSPECIFIED": "?",
            "FREE": "$0",
            "INEXPENSIVE": "$",
            "MODERATE": "$$",
            "EXPENSIVE": "$$$",
            "ULTRA_EXPENSIVE": "$$$$",
        }
        output_parts.append(
            f"Price Level: {price_symbols.get(price_level, price_level)}"
        )

    if website:
        output_parts.append(f"Website: {website}")

    if phone:
        output_parts.append(f"Phone: {phone}")

    if weekday:
        output_parts.append("")
        output_parts.append("Hours:")
        for day in weekday[:7]:
            output_parts.append(f"  {day}")

    if reviews:
        output_parts.append("")
        output_parts.append(f"Recent Reviews ({len(reviews)}):")
        for j, review in enumerate(reviews[:3], 1):
            author = review.get("author", {}).get("displayName", "Anonymous")
            rating_review = review.get("rating", "")
            text = review.get("text", {}).get("text", "")
            output_parts.append(f"  {j}. {author} - {rating_review}/5")
            if text:
                output_parts.append(f"     {text[:150]}...")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("get_place_details", is_read_only=True, service_type="maps")
@require_google_service("maps", "maps")
async def get_place_details(
    service,
    user_google_email: str,
    place_id: str,
) -> str:
    """
    Gets detailed information about a specific place.

    Args:
        user_google_email (str): The user's Google email address. Required.
        place_id (str): The Google Places ID. Required.

    Returns:
        str: Full details of the place.
    """
    logger.info(
        f"[get_place_details] Invoked. Email: '{user_google_email}', Place ID: {place_id}"
    )
    return await get_place_details_impl(service, user_google_email, place_id)


async def geocode_address_impl(
    service,
    user_google_email: str,
    address: str,
) -> str:
    """Implementation for geocoding an address."""
    result = await asyncio.to_thread(service.geocode().get(address=address).execute)

    results = result.get("results", [])
    if not results:
        return f"No geocoding results found for address '{address}'."

    location = results[0]
    formatted_address = location.get("formatted_address", "")
    geometry = location.get("geometry", {})
    location_coords = geometry.get("location", {})
    lat = location_coords.get("lat", "")
    lng = location_coords.get("lng", "")

    place_id = location.get("place_id", "")
    types = location.get("types", [])

    output_parts = [
        f"Geocoding Result for {user_google_email}:",
        f"Address: {formatted_address}",
        f"Location: {lat}, {lng}",
        f"Place ID: {place_id}",
        f"Types: {', '.join(types)}",
    ]

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("geocode_address", is_read_only=True, service_type="maps")
@require_google_service("maps", "maps")
async def geocode_address(
    service,
    user_google_email: str,
    address: str,
) -> str:
    """
    Converts an address to latitude/longitude coordinates.

    Args:
        user_google_email (str): The user's Google email address. Required.
        address (str): The address to geocode. Required.

    Returns:
        str: Geocoded location information.
    """
    logger.info(
        f"[geocode_address] Invoked. Email: '{user_google_email}', Address: '{address}'"
    )
    return await geocode_address_impl(service, user_google_email, address)


async def reverse_geocode_impl(
    service,
    user_google_email: str,
    latitude: float,
    longitude: float,
) -> str:
    """Implementation for reverse geocoding."""
    result = await asyncio.to_thread(
        service.geocode()
        .get(
            address=f"{latitude},{longitude}",
            language="en",
        )
        .execute
    )

    results = result.get("results", [])
    if not results:
        return f"No reverse geocoding results found for {latitude}, {longitude}."

    location = results[0]
    formatted_address = location.get("formatted_address", "")
    place_id = location.get("place_id", "")
    types = location.get("types", [])

    output_parts = [
        f"Reverse Geocoding Result for {user_google_email}:",
        f"Coordinates: {latitude}, {longitude}",
        f"Address: {formatted_address}",
        f"Place ID: {place_id}",
        f"Types: {', '.join(types)}",
    ]

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("reverse_geocode", is_read_only=True, service_type="maps")
@require_google_service("maps", "maps")
async def reverse_geocode(
    service,
    user_google_email: str,
    latitude: float,
    longitude: float,
) -> str:
    """
    Converts latitude/longitude coordinates to an address.

    Args:
        user_google_email (str): The user's Google email address. Required.
        latitude (float): The latitude coordinate. Required.
        longitude (float): The longitude coordinate. Required.

    Returns:
        str: Reverse geocoded address information.
    """
    logger.info(
        f"[reverse_geocode] Invoked. Email: '{user_google_email}', "
        f"Location: {latitude}, {longitude}"
    )
    return await reverse_geocode_impl(service, user_google_email, latitude, longitude)


async def find_nearby_places_impl(
    service,
    user_google_email: str,
    latitude: float,
    longitude: float,
    radius: int = 1000,
    place_type: Optional[str] = None,
    max_results: int = 10,
) -> str:
    """Implementation for finding nearby places."""
    params = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius,
            }
        },
        "maxResults": max_results,
    }

    if place_type:
        params["includedType"] = place_type

    places = await asyncio.to_thread(service.places().searchNearby(body=params).execute)

    results = places.get("places", [])
    if not results:
        return f"No nearby places found at {latitude}, {longitude}."

    output_parts = [
        f"Nearby Places for {user_google_email}:",
        f"Location: {latitude}, {longitude}",
        f"Radius: {radius}m",
        f"Type: {place_type or 'all'}",
        f"Found: {len(results)} places",
        "",
    ]

    for i, place in enumerate(results, 1):
        name = place.get("displayName", {}).get("text", "Unknown")
        place_id = place.get("id", "")
        address = place.get("formattedAddress", "")

        distance = place.get("distanceMeters", "")

        rating = place.get("rating", "")
        user_ratings = place.get("userRatingCount", "")

        output_parts.append(f"{i}. {name}")
        output_parts.append(f"   Place ID: {place_id}")
        if address:
            output_parts.append(f"   Address: {address}")
        if distance:
            output_parts.append(f"   Distance: {distance}m")
        if rating:
            output_parts.append(f"   Rating: {rating}/5 ({user_ratings} reviews)")

        output_parts.append("")

    return "\n".join(output_parts)


@server.tool()
@handle_http_errors("find_nearby_places", is_read_only=True, service_type="maps")
@require_google_service("maps", "maps")
async def find_nearby_places(
    service,
    user_google_email: str,
    latitude: float,
    longitude: float,
    radius: int = 1000,
    place_type: Optional[str] = None,
    max_results: int = 10,
) -> str:
    """
    Finds nearby places based on location and optional type.

    Args:
        user_google_email (str): The user's Google email address. Required.
        latitude (float): The latitude coordinate. Required.
        longitude (float): The longitude coordinate. Required.
        radius (int): Search radius in meters. Defaults to 1000.
        place_type (Optional[str]): Type of places to search for (e.g., "restaurant", "cafe",
            "gas_station", "atm", "hospital", "park", "hotel"). If not provided, returns all.
        max_results (int): Maximum number of results. Defaults to 10.

    Returns:
        str: List of nearby places.
    """
    logger.info(
        f"[find_nearby_places] Invoked. Email: '{user_google_email}', "
        f"Location: {latitude},{longitude}, Radius: {radius}, Type: {place_type}"
    )
    return await find_nearby_places_impl(
        service, user_google_email, latitude, longitude, radius, place_type, max_results
    )
