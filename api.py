import httpx
import json


async def get_airfield_id(airfield_name, debug=False):
    search_url = "https://api.weglide.org/v1/search"
    search_payload = {
        "search_items": [{"key": "name", "value": airfield_name}],
        "documents": ["airport"],
    }
    if debug:
        print(f"DEBUG: Calling {search_url} with payload: {json.dumps(search_payload)}")
    async with httpx.AsyncClient() as client:
        response = await client.post(search_url, json=search_payload)
    if debug:
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response body: {response.text}")
    if response.status_code == 200:
        results = response.json()
        if results and len(results) > 0:
            return results[0]["id"]
    return None


async def list_flights(airfield_id, skip=0, limit=100, debug=False):
    flights_url = f"https://api.weglide.org/v1/flight?airport_id_in={airfield_id}&skip={skip}&limit={limit}"
    if debug:
        print(f"DEBUG: Calling {flights_url}")
    async with httpx.AsyncClient() as client:
        response = await client.get(flights_url)
    if debug:
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response body: {response.text}")
    if response.status_code == 200:
        return response.json()
    return None
