"""Lightweight geo helpers — no GIS dependency required.

The dataset is tiny (a couple hundred rows), so we happily compute haversine
distances in Python rather than reaching for PostGIS / SpatiaLite.
"""
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points, in kilometres."""
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))
