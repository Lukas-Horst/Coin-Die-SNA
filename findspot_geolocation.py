import os
import json
import requests
import re

CACHE_FILE = "Cache/location_cache_geojson.json"
CACHE_DIR = os.path.dirname(CACHE_FILE) # Extract the directory path "Cache"

# 1. Check and create the directory if it does not exist
if not os.path.exists(CACHE_DIR):
    # Create the directory recursively (including parent directories if necessary)
    os.makedirs(CACHE_DIR)
    print(f"Created cache directory: {CACHE_DIR}")

# 2. Handle file reading/initialization
cache = {}
if os.path.exists(CACHE_FILE):
    # If the file exists, load the cache
    with open(CACHE_FILE, "r") as f:
        # Use a try/except block to catch potential JSON decoding errors (e.g., if the file is empty)
        try:
            cache = json.load(f)
            print("Cache loaded successfully.")
        except json.JSONDecodeError:
            print("Error decoding JSON from cache file. Starting with an empty cache.")


def get_findspot_geojson(findspot):
    if findspot in cache:
        return cache[findspot]

    search_fs = findspot.replace("District", "")

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": search_fs,
        "format": "geojson"
    }
    headers = {
        "User-Agent": "coin-die-sna/0.1"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        res_data = response.json()
        cache[findspot] = res_data

        with open(CACHE_FILE, "w") as file:
            json.dump(cache, file)

        print(f"Fetched: Findspot {findspot}")
        return res_data
    else:
        print(f"Error: Findspot {findspot}: {response.status_code} {response.text}")
        return None


def get_findspot_coordinate(findspot):
    try:
        geojson = get_findspot_geojson(findspot)
        lat = geojson["features"][0]["geometry"]["coordinates"][1]
        lon = geojson["features"][0]["geometry"]["coordinates"][0]
        return (lat, lon)
    except IndexError:
        pass

    split_name = re.split(r"[ -]", findspot)
    for i in range(len(split_name)):
        findspot_alt = split_name[i]
        try:
            geojson = get_findspot_geojson(findspot_alt)
            lat = geojson["features"][0]["geometry"]["coordinates"][1]
            lon = geojson["features"][0]["geometry"]["coordinates"][0]
            # print("Found alternative:", findspot_alt, "| instead of:", findspot)
            return (lat, lon)
        except IndexError:
            pass

    # print("Not found:", findspot)
    return (0, 0)


def get_findspot_osmtypeid(findspot):
    try:
        geojson = get_findspot_geojson(findspot)
        osmtype = geojson["features"][0]["properties"]["osm_type"]
        osmid = geojson["features"][0]["properties"]["osm_id"]
        return osmtype + "/" + str(osmid)
    except IndexError:
        pass

    split_name = re.split(r"[ -]", findspot)
    for i in range(len(split_name)):
        findspot_alt = split_name[i]
        try:
            geojson = get_findspot_geojson(findspot_alt)
            osmtype = geojson["features"][0]["properties"]["osm_type"]
            osmid = geojson["features"][0]["properties"]["osm_id"]
            print("Found alternative:", findspot_alt, "| instead of:", findspot)
            return osmtype + "/" + str(osmid)
        except IndexError:
            pass

    print("Not found:", findspot)
    return ""


if __name__ == "__main__":
    latlon = get_findspot_coordinate("Manching")
    print(latlon)
