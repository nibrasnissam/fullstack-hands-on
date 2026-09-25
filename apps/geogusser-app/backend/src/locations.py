"""
Curated pool of guessable locations for GeoGusser.

Each location has a real-world lat/lng and a publicly hosted street-level
photo (Wikimedia Commons). This stands in for a live Street-View-style
imagery provider so the game works out of the box with no API key.

Swap `image_url` for a Mapillary / Street View tile URL later if you wire
up a real imagery provider (see README for the extension point).
"""

LOCATIONS = [
    {
        "id": "paris-fr",
        "country": "France",
        "city": "Paris",
        "lat": 48.8584,
        "lng": 2.2945,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/85/Tour_Eiffel_Wikimedia_Commons.jpg",
    },
    {
        "id": "tokyo-jp",
        "country": "Japan",
        "city": "Tokyo",
        "lat": 35.6595,
        "lng": 139.7005,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Shibuya_Crossing_2023.jpg",
    },
    {
        "id": "nyc-us",
        "country": "United States",
        "city": "New York City",
        "lat": 40.7580,
        "lng": -73.9855,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/85/Times_Square%2C_NYC.jpg",
    },
    {
        "id": "sydney-au",
        "country": "Australia",
        "city": "Sydney",
        "lat": -33.8568,
        "lng": 151.2153,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/c9/Sydney_Opera_House_-_Dec_2008.jpg",
    },
    {
        "id": "rio-br",
        "country": "Brazil",
        "city": "Rio de Janeiro",
        "lat": -22.9519,
        "lng": -43.2105,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Copacabana_beach_Rio_de_Janeiro.jpg",
    },
    {
        "id": "capetown-za",
        "country": "South Africa",
        "city": "Cape Town",
        "lat": -33.9249,
        "lng": 18.4241,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ec/Cape_Town_viewed_from_Table_Mountain.jpg",
    },
    {
        "id": "rome-it",
        "country": "Italy",
        "city": "Rome",
        "lat": 41.8902,
        "lng": 12.4922,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/d/de/Colosseo_2020.jpg",
    },
    {
        "id": "moscow-ru",
        "country": "Russia",
        "city": "Moscow",
        "lat": 55.7539,
        "lng": 37.6208,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Moscow_July_2011-2a.jpg",
    },
    {
        "id": "cairo-eg",
        "country": "Egypt",
        "city": "Giza",
        "lat": 29.9773,
        "lng": 31.1325,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Kheops-Pyramid.jpg",
    },
    {
        "id": "mumbai-in",
        "country": "India",
        "city": "Mumbai",
        "lat": 18.9220,
        "lng": 72.8347,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/8a/Gateway_of_India_Mumbai.jpg",
    },
    {
        "id": "london-gb",
        "country": "United Kingdom",
        "city": "London",
        "lat": 51.5007,
        "lng": -0.1246,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/9/9d/London_Big_Ben_Phone_box.jpg",
    },
    {
        "id": "reykjavik-is",
        "country": "Iceland",
        "city": "Reykjavik",
        "lat": 64.1466,
        "lng": -21.9426,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/60/Hallgrimskirkja_2013.jpg",
    },
]
