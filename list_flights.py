
import httpx
import json
from rich.console import Console
from rich.table import Table

def get_airfield_id(airfield_name):
    search_url = "https://api.weglide.org/v1/search"
    search_payload = {
        "search_items": [{"key": "name", "value": airfield_name}],
        "documents": ["airport"]
    }
    response = httpx.post(search_url, json=search_payload)
    if response.status_code == 200:
        results = response.json()
        if results and len(results) > 0:
            return results[0]['id']
    return None

def list_flights(airfield_id, skip=0, limit=100):
    flights_url = f"https://api.weglide.org/v1/flight?airport_id_in={airfield_id}&skip={skip}&limit={limit}"
    response = httpx.get(flights_url)
    if response.status_code == 200:
        return response.json()
    return None

if __name__ == "__main__":
    console = Console()
    airfield_name = "Unterwössen"
    airfield_id = get_airfield_id(airfield_name)
    if airfield_id:
        console.print(f"Found airfield ID for '[bold green]{airfield_name}[/bold green]': {airfield_id}")
        all_flights = []
        skip = 0
        limit = 100
        while True:
            flights = list_flights(airfield_id, skip=skip, limit=limit)
            if flights:
                all_flights.extend(flights)
                skip += limit
            else:
                break
        
        if all_flights:
            console.print("[bold blue]All flights from Unterwössen:[/bold blue]") 
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Date", style="dim", width=12)
            table.add_column("Aircraft")
            table.add_column("Distance (km)", justify="right")

            for flight in all_flights:
                date = flight.get('takeoff_time', 'N/A').split('T')[0]
                aircraft = flight.get('aircraft', {}).get('name', 'N/A')
                distance = flight.get('contest', {}).get('distance', 'N/A')
                table.add_row(date, aircraft, str(distance))
            
            console.print(table)
        else:
            console.print("Could not retrieve flights.")
    else:
        console.print(f"Could not find airfield ID for '[bold red]{airfield_name}[/bold red]'.")
