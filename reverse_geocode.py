from pprint import pprint

import requests


def print_user_location(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'limit': 1,
        'format': 'json',
    }

    r = requests.get("https://nominatim.openstreetmap.org/reverse", params)
    r.raise_for_status()  # will raise an exception for HTTp status code != 200
    data = r.json()
    return data["address"].get("town") or data["display_name"]
