import requests
from utils.config import load_config

config = load_config()
BASE_URL = config["travelata"]["base_url"]

def get_cheapest_tours(country_id: int, city_id: int, params: dict):
    query = {
        "countries[]": country_id,
        "departureCity": city_id,
        "nightRange[from]": params.get("duration_days", 7) - 1,
        "nightRange[to]": params.get("duration_days", 7) + 1,
        "touristGroup[adults]": params.get("adults", 2),
        "touristGroup[kids]": params.get("kids", 0),
        "touristGroup[infants]": 0,
        "checkInDateRange[from]": "2024-07-01",
        "checkInDateRange[to]": "2024-07-31"
    }
    resp = requests.get(f"{BASE_URL}/statistic/cheapestTours", params=query)
    if resp.status_code == 200:
        return resp.json().get("data", [])
    return []