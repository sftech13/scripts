import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import timedelta
from dateutil import parser
import pytz
import logging

# Define paths for log and output files
LOG_FILE_PATH = '/home/sftech13/logs/ncaaf_epg.log'
EPG_FILE_PATH = '/home/sftech13/scripts/ncaaf/ncaaf_epg.xml'

# Set up logging
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# CollegeFootballData API details
API_KEY = 'Sn/+CuiNS04Mbfui1uBg9+IFSwPPfdiev7J9/OtjckUUhhsp/HUw617SZqssAaZu'
API_BASE_URL = 'https://api.collegefootballdata.com'
GAMES_ENDPOINT = '/games'

# Function to fetch games data
def fetch_games(year=2024, season_type='regular', week=1):
    url = f"{API_BASE_URL}{GAMES_ENDPOINT}"
    params = {
        'year': year,
        'seasonType': season_type,
        'week': week
    }
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        logging.info("Successfully fetched games data")
        logging.debug(f"Games data fetched: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching games data from CollegeFootballData API: {e}")
        return None

# Function to convert start time to the correct format
def convert_to_correct_format(start_time_str):
    try:
        start_time = parser.isoparse(start_time_str)  # Correctly parse ISO 8601 formatted date strings
    except ValueError:
        logging.error(f"Time format is incorrect: {start_time_str}; skipping this game.")
        return None

    # Convert to desired timezone (local time)
    target_timezone = pytz.timezone("America/Los_Angeles")  # Change to your desired timezone
    local_time = start_time.astimezone(target_timezone)
    
    # Format to yyyy-mm-dd hh:mm:ss
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

# Function to generate XMLTV format EPG
def generate_epg(games):
    root = ET.Element("tv")

    if not games:  # Check if games data is empty
        logging.warning("No games data to process.")
        return

    for game in games:
        home_team = game.get('home_team', 'Unknown Team')
        away_team = game.get('away_team', 'Unknown Team')
        game_title = f"{home_team} vs {away_team}"

        # Use the game title as the channel name
        channel_name = game_title

        # Correctly formatted timestamps
        start_time_str = game.get('start_date', '')
        start_time = convert_to_correct_format(start_time_str)

        # Skip this game if the start time could not be processed
        if start_time is None:
            continue

        end_time = (parser.isoparse(start_time_str) + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

        description = f"Scheduled game between {home_team} and {away_team}"

        # Add channel element if not already added
        if channel_name not in [elem.get('id') for elem in root.findall('channel')]:
            channel = ET.SubElement(root, "channel", id=channel_name)
            ET.SubElement(channel, "display-name").text = channel_name

        # Create programme element with formatted timestamps
        programme = ET.SubElement(root, "programme", start=start_time, stop=end_time, channel=channel_name)
        ET.SubElement(programme, "title").text = game_title
        ET.SubElement(programme, "desc").text = description

    # Write to an XML file with pretty-printing
    try:
        with open(EPG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(minidom.parseString(ET.tostring(root)).toprettyxml(indent="  "))
        logging.info(f"EPG generated successfully and saved to {EPG_FILE_PATH}")
    except Exception as e:
        logging.error(f"Error writing EPG to file: {e}")

# Main function
def main():
    # Fetch games data for week 1 of the 2024 season
    games = fetch_games(year=2024, season_type='regular', week=1)

    if games:
        generate_epg(games)
    else:
        logging.warning("No data returned from API.")

if __name__ == "__main__":
    main()

