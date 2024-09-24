import requests
import json
import xml.etree.ElementTree as ET
import os
import sqlite3
from datetime import datetime, timedelta
import signal
import sys

# Variables for editing
LOG_FILE_PATH = '/home/sftech13/logs/24-7_xmltv_generator.log'  # Update this path as needed

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Function to log messages
def log_message(message):
    with open(LOG_FILE_PATH, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# Load API info from JSON file
def load_api_key():
    api_info_path = os.path.join(script_dir, 'api_info.json')
    try:
        with open(api_info_path, 'r') as api_file:
            api_data = json.load(api_file)
            return api_data['tmdb_api_key']
    except Exception as e:
        log_message(f"Error loading API key: {str(e)}")
        sys.exit(1)

# Database setup
db_path = os.path.join(script_dir, 'cache.db')

def create_cache_table():
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    name TEXT PRIMARY KEY,
                    type TEXT,
                    data TEXT
                )
            ''')
            conn.commit()
    except Exception as e:
        log_message(f"Error creating cache table: {str(e)}")

def load_cache(name, type):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data FROM cache WHERE name = ? AND type = ?', (name, type))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
    except Exception as e:
        log_message(f"Error loading cache for {name} of type {type}: {str(e)}")
    return None

def save_cache(name, type, data):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cache (name, type, data)
                VALUES (?, ?, ?)
            ''', (name, type, json.dumps(data)))
            conn.commit()
    except Exception as e:
        log_message(f"Error saving cache for {name} of type {type}: {str(e)}")

def delete_cache():
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache')
            conn.commit()
        log_message("Cache deleted successfully.")
    except Exception as e:
        log_message(f"Error deleting cache: {str(e)}")

def delete_cache_item(name, type):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache WHERE name = ? AND type = ?', (name, type))
            conn.commit()
        log_message(f"Deleted cache item {name} of type {type}.")
    except Exception as e:
        log_message(f"Error deleting cache item {name} of type {type}: {str(e)}")

def list_cache_items():
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, type FROM cache')
            return cursor.fetchall()
    except Exception as e:
        log_message(f"Error listing cache items: {str(e)}")
        return []

def get_tmdb_info(name, type="tv"):
    search_url = f"https://api.themoviedb.org/3/search/{type}?api_key={TMDB_API_KEY}&query={requests.utils.quote(name)}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        if not data['results']:
            log_message(f"No results found for {name}")
            return None
        return data['results']
    except Exception as e:
        log_message(f"Error fetching TMDB info for {name}: {str(e)}")
        return None

def get_tmdb_collection(name):
    search_url = f"https://api.themoviedb.org/3/search/collection?api_key={TMDB_API_KEY}&query={requests.utils.quote(name)}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        if not data['results']:
            log_message(f"No collection found for {name}")
            return None
        return data['results']
    except Exception as e:
        log_message(f"Error fetching TMDB collection info for {name}: {str(e)}")
        return None

def get_collection_details(collection_id):
    details_url = f"https://api.themoviedb.org/3/collection/{collection_id}?api_key={TMDB_API_KEY}"
    try:
        response = requests.get(details_url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        log_message(f"Error fetching collection details for ID {collection_id}: {str(e)}")
        return None

def select_item(items, json_title, type="tv"):
    key = 'title' if type == "movie" else 'name'
    for item in items:
        try:
            title = item[key]
            description = item.get('overview', 'No description available.')
            poster_path = item.get('poster_path', '')
            poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else 'No image available.'
            return {
                "json_title": json_title,
                "title": title,
                "description": description,
                "logo": poster
            }
        except KeyError as e:
            log_message(f"Failed to fetch complete info for {json_title}: {str(e)}")
    log_message(f"No acceptable items found for {json_title}")
    return None

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def capitalize_title(title):
    exceptions = {'and', 'or', 'nor', 'but', 'a', 'an', 'the', 'as', 'at', 'by', 'for', 'in', 'of', 'on', 'per', 'to', 'vs'}
    words = title.split()
    capitalized_words = [word.capitalize() if i == 0 or word.lower() not in exceptions else word.lower()
                         for i, word in enumerate(words)]
    return ' '.join(capitalized_words)

def create_xmltv(items, filename, slot_duration_hours=1):
    root = ET.Element("tv", attrib={"source-info-name": "SFTech EPG Generator"})
    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    for item in items:
        channel_id = item["json_title"].replace(" ", "_").lower()
        channel = ET.SubElement(root, "channel", id=channel_id)
        ET.SubElement(channel, "display-name").text = capitalize_title(item["json_title"])
        if item.get("logo") and item["logo"] != 'No image available.':
            ET.SubElement(channel, "icon", src=item["logo"])
        num_slots = 48 // slot_duration_hours
        for slot in range(num_slots):
            start_time = (start_date + timedelta(hours=slot * slot_duration_hours)).strftime('%Y%m%d%H0000 +0000')
            stop_time = (start_date + timedelta(hours=(slot + 1) * slot_duration_hours)).strftime('%Y%m%d%H0000 +0000')
            programme = ET.SubElement(root, "programme", start=start_time, stop=stop_time, channel=channel_id)
            ET.SubElement(programme, "title", lang="en").text = capitalize_title(item["json_title"])
            ET.SubElement(programme, "desc", lang="en").text = item["description"]
            ET.SubElement(programme, "category", lang="en").text = "Series" if slot_duration_hours == 1 else "Movie"
            if item.get("logo") and item["logo"] != 'No image available.':
                ET.SubElement(programme, "icon", src=item["logo"])
    indent(root)
    tree = ET.ElementTree(root)
    xmltv_path = os.path.join(script_dir, filename)
    try:
        tree.write(xmltv_path, encoding="UTF-8", xml_declaration=True)
        log_message(f"XMLTV file created successfully at {xmltv_path}")
    except Exception as e:
        log_message(f"Error creating XMLTV file: {str(e)}")

def fetch_and_create_xmltv(json_path, filename, type="tv", slot_duration_hours=1):
    json_file_path = os.path.join(script_dir, json_path)
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            names = data["shows"] if type == "tv" else data["movies"]
    except Exception as e:
        log_message(f"Error loading JSON file {json_path}: {str(e)}")
        return

    info_list = []
    for name in names:
        cached_info = load_cache(name, type)
        if not cached_info:
            collections = get_tmdb_collection(name) if type == "movie" else None
            if collections:
                log_message(f"Select the correct collection for {name}.")
                # Implement user selection logic
            if not load_cache(name, type):
                items = get_tmdb_info(name, type=type)
                if items:
                    log_message(f"Results found for {name}.")
                    # Implement user selection logic
        else:
            info_list.append(cached_info)

    create_xmltv(info_list, filename, slot_duration_hours)

def timed_input(prompt, timeout):
    if not sys.stdin.isatty():
        log_message("Running in non-interactive mode, selecting option 3")
        return '3'
    print(prompt, end='', flush=True)
    inputs = ''
    def alarm_handler(signum, frame):
        raise TimeoutError
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)
    try:
        inputs = input()
        signal.alarm(0)
    except TimeoutError:
        log_message("Timeout reached. Default action taken.")
        inputs = '3'
    return inputs.strip().lower()

def delete_specific_cache_item():
    items = list_cache_items()
    if not items:
        log_message("No items in cache.")
        return
    print("Cached items:")
    for idx, (name, type) in enumerate(items, 1):
        print(f"{idx}. {name} ({type})")
    user_choice = input("Enter the number of the item to delete or 'skip' to skip: ").strip().lower()
    if user_choice and user_choice != 'skip':
        try:
            selected_index = int(user_choice) - 1
            if 0 <= selected_index < len(items):
                name, type = items[selected_index]
                delete_cache_item(name, type)
            else:
                log_message("Invalid number. Please try again.")
        except ValueError:
            log_message("Invalid input. Please enter a number or 'skip'.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_choice = sys.argv[1]
    else:
        user_choice = timed_input("Enter 1 for TV shows, 2 for movies, 3 for both, 4 to delete cache, or 5 to delete specific item from cache (default: both): ", timeout=4)

    TMDB_API_KEY = load_api_key()
    create_cache_table()

    if user_choice == "1":
        fetch_and_create_xmltv('tv_shows.json', 'tv.xml', type="tv", slot_duration_hours=1)
    elif user_choice == "2":
        fetch_and_create_xmltv('movies.json', 'movies.xml', type="movie", slot_duration_hours=2)
    elif user_choice == "3":
        fetch_and_create_xmltv('tv_shows.json', 'tv.xml', type="tv", slot_duration_hours=1)
        fetch_and_create_xmltv('movies.json', 'movies.xml', type="movie", slot_duration_hours=2)
    elif user_choice == "4":
        delete_cache()
    elif user_choice == "5":
        delete_specific_cache_item()
    else:
        fetch_and_create_xmltv('tv_shows.json', 'tv.xml', type="tv", slot_duration_hours=1)
        fetch_and_create_xmltv('movies.json', 'movies.xml', type="movie", slot_duration_hours=2)

    log_message(f'User choice: {user_choice}')

