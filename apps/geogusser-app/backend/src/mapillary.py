"""
Thin wrapper around the Mapillary Graph API for finding a real, playable
360-degree panorama near a given coordinate.

Requires a free Mapillary access token (client token, looks like
"MLY|1234...") set as the MAPILLARY_ACCESS_TOKEN env var. Get one at
https://www.mapillary.com/dashboard/developers

If no token is set, or no coverage is found near a location, callers
should fall back to the static image in locations.py.
"""

import random
from typing import Optional, Tuple

import requests

GRAPH_URL = "https://graph.mapillary.com/images"
# Expanding search radius (degrees) around a target coordinate. Roughly
# 0.05 deg =~ 5.5km, 1.0 deg =~ 110km at the equator.
SEARCH_RADII = [0.05, 0.2, 0.5, 1.0]
REQUEST_TIMEOUT = 5


def find_nearby_image(lat: float, lng: float, token: str) -> Optional[Tuple[str, float, float]]:
    """
    Returns (image_id, actual_lat, actual_lng) for a real Mapillary photo
    near (lat, lng), or None if the API call fails or no coverage exists
    even at the widest search radius.
    """
    if not token:
        return None

    for radius in SEARCH_RADII:
        bbox = f"{lng - radius},{lat - radius},{lng + radius},{lat + radius}"
        params = {
            "access_token": token,
            "fields": "id,geometry",
            "bbox": bbox,
            "limit": 20,
        }
        try:
            resp = requests.get(GRAPH_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            results = resp.json().get("data", [])
        except (requests.RequestException, ValueError):
            continue

        if results:
            pick = random.choice(results)
            try:
                lng_actual, lat_actual = pick["geometry"]["coordinates"]
                return pick["id"], lat_actual, lng_actual
            except (KeyError, TypeError, ValueError):
                continue

    return None
