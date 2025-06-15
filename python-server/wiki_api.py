import requests
import time
import config

BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"

def fetch(endpoint, timestamp=None):
    url = f"{BASE_URL}{endpoint}"
    params = {"timestamp": timestamp} if timestamp else {}
    response = requests.get(url, headers=config.WIKI_REQUEST_HEADERS, params=params)
    response.raise_for_status()
    j = response.json()

    now = time.time()

    match endpoint:
        case "/5m" | "/1h":
            return {
                "data": {int(k): v for k, v in j["data"].items()},
                "fetched_at": now,
                "data_timestamp": j.get("timestamp")
            }
        case "/latest":
            return {
                "data": {int(k): v for k, v in j["data"].items()},
                "fetched_at": now,
                "data_timestamp": None
            }
        case "/mapping":
            return {
                "data": {d['id']: d for d in j},
                "fetched_at": now,
                "data_timestamp": None
            }
