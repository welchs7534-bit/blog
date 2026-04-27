import os
import requests
from dotenv import load_dotenv

load_dotenv()
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


def fetch_image(keyword):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": keyword,
        "per_page": 1,
        "orientation": "landscape"
    }
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    response = requests.get(url, params=params, headers=headers, timeout=10)
    data = response.json()

    if data.get("results"):
        photo = data["results"][0]
        return {
            "url": photo["urls"]["regular"],
            "photographer": photo["user"]["name"],
            "photographer_link": photo["user"]["links"]["html"]
        }
    return None
