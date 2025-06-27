
import httpx
import json
import argparse
from rich.console import Console
from rich.table import Table

def get_airfield_id(airfield_name, debug=False):
    search_url = "https://api.weglide.org/v1/search"
    search_payload = {
        "search_items": [{"key": "name", "value": airfield_name}],
        "documents": ["airport"]
    }
    if debug:
        print(f"DEBUG: Calling {search_url} with payload: {json.dumps(search_payload)}")
    response = httpx.post(search_url, json=search_payload)
    if debug:
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response body: {response.text}")
    if response.status_code == 200:
        results = response.json()
        if results and len(results) > 0:
            return results[0]['id']
    return None

def list_flights(airfield_id, skip=0, limit=100, debug=False):
    flights_url = f"https://api.weglide.org/v1/flight?airport_id_in={airfield_id}&skip={skip}&limit={limit}"
    if debug:
        print(f"DEBUG: Calling {flights_url}")
    response = httpx.get(flights_url)
    if debug:
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response body: {response.text}")
    if response.status_code == 200:
        return response.json()
    return None

if __name__ == "__main__":
    console = Console()

    parser = argparse.ArgumentParser(description="List flights from a specified airfield.")
    parser.add_argument("airfield_name", type=str, help="Name of the airfield to search for.")
    parser.add_argument("--percentile", type=int, default=100, help="Percentile of distances to show (e.g., 50 for median, 100 for max).")
    parser.add_argument("--debug", action="store_true", help="Enable debug output for API calls.")
    args = parser.parse_args()

    airfield_name = args.airfield_name
    percentile_value = args.percentile
    debug_mode = args.debug
    airfield_id = get_airfield_id(airfield_name, debug=debug_mode)
    if airfield_id:
        console.print(f"Found airfield ID for '[bold green]{airfield_name}[/bold green]': {airfield_id}")
        all_flights = []
        skip = 0
        limit = 100
        while True:
            flights = list_flights(airfield_id, skip=skip, limit=limit, debug=debug_mode)
            if flights:
                all_flights.extend(flights)
                skip += limit
            else:
                break
        
        if all_flights:
            table = Table(show_header=True, header_style="bold magenta")
            
            # Define month names for table headers
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            table.add_column("Year", style="dim", width=6)
            for month_name in month_names:
                table.add_column(month_name, justify="right")

            yearly_monthly_distances = {}

            for flight in all_flights:
                takeoff_time_str = flight.get('takeoff_time')
                if takeoff_time_str and takeoff_time_str != 'N/A':
                    year = takeoff_time_str[:4]  # "YYYY-MM-DDTHH:MM:SSZ" -> "YYYY"
                    month_num = int(takeoff_time_str[5:7])  # "YYYY-MM-DDTHH:MM:SSZ" -> MM
                    distance = flight.get('contest', {}).get('distance')

                    if distance is not None:
                        if year not in yearly_monthly_distances:
                            yearly_monthly_distances[year] = {}
                        
                        if month_num not in yearly_monthly_distances[year]:
                            yearly_monthly_distances[year][month_num] = []
                        yearly_monthly_distances[year][month_num].append(distance)
            
            # Sort years chronologically
            sorted_years = sorted(yearly_monthly_distances.keys())

            def calculate_percentile(data, percentile):
                if not data:
                    return "N/A"
                sorted_data = sorted(data)
                k = (len(sorted_data) - 1) * percentile / 100
                f = int(k)
                c = k - f
                if f + 1 < len(sorted_data):
                    return int(sorted_data[f] + (sorted_data[f+1] - sorted_data[f]) * c)
                else:
                    return int(sorted_data[f])

            # Determine min and max distances for color scaling based on the chosen percentile
            all_percentile_distances = []
            for year_data in yearly_monthly_distances.values():
                for month_data in year_data.values():
                    percentile_dist = calculate_percentile(month_data, percentile_value)
                    if percentile_dist != "N/A":
                        all_percentile_distances.append(percentile_dist)

            min_distance = min(all_percentile_distances) if all_percentile_distances else 0
            max_distance = max(all_percentile_distances) if all_percentile_distances else 0

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
                    distances_for_month = yearly_monthly_distances[year].get(month_num, [])
                    percentile_dist = calculate_percentile(distances_for_month, percentile_value)
                    colored_distance = f"[{get_distance_color(percentile_dist)}]{percentile_dist}[/]"
                    row_data.append(colored_distance)
                table.add_row(*row_data)
            
            console.print(table)
        else:
            console.print("Could not retrieve flights.")
    else:
        console.print(f"Could not find airfield ID for '[bold red]{airfield_name}[/bold red]'.")
