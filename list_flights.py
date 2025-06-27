
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
            
            # Define month names for table headers
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            table.add_column("Year", style="dim", width=6)
            for month_name in month_names:
                table.add_column(month_name, justify="right")

            yearly_monthly_max_distance = {}

            for flight in all_flights:
                takeoff_time_str = flight.get('takeoff_time')
                if takeoff_time_str and takeoff_time_str != 'N/A':
                    year = takeoff_time_str[:4]  # "YYYY-MM-DDTHH:MM:SSZ" -> "YYYY"
                    month_num = int(takeoff_time_str[5:7])  # "YYYY-MM-DDTHH:MM:SSZ" -> MM
                    distance = flight.get('contest', {}).get('distance')

                    if distance is not None:
                        if year not in yearly_monthly_max_distance:
                            yearly_monthly_max_distance[year] = {}
                        
                        if month_num not in yearly_monthly_max_distance[year] or distance > yearly_monthly_max_distance[year][month_num]:
                            yearly_monthly_max_distance[year][month_num] = distance
            
            # Sort years chronologically
            sorted_years = sorted(yearly_monthly_max_distance.keys())

            # Determine min and max distances for color scaling
            all_distances = [dist for year_data in yearly_monthly_max_distance.values() for dist in year_data.values()]
            min_distance = min(all_distances) if all_distances else 0
            max_distance = max(all_distances) if all_distances else 0

            def get_distance_color(distance):
                if distance == "N/A":
                    return "dim"
                
                distance = int(distance)
                if max_distance == min_distance:
                    return "white"
                
                # Simple linear scaling for color intensity
                # You can adjust these thresholds and colors as needed
                range_size = max_distance - min_distance
                if range_size == 0:
                    return "white"

                normalized_distance = (distance - min_distance) / range_size

                if normalized_distance < 0.33:
                    return "red"
                elif normalized_distance < 0.66:
                    return "yellow"
                else:
                    return "green"

            for year in sorted_years:
                row_data = [year]
                for month_num in range(1, 13):
                    distance = yearly_monthly_max_distance[year].get(month_num, "N/A")
                    colored_distance = f"[{get_distance_color(distance)}]{distance}[/]"
                    row_data.append(colored_distance)
                table.add_row(*row_data)
            
            console.print(table)
        else:
            console.print("Could not retrieve flights.")
    else:
        console.print(f"Could not find airfield ID for '[bold red]{airfield_name}[/bold red]'.")
