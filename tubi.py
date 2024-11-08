# === User Options ===
# Modify these settings before running the script
COUNTRIES = ['US']  # List of country codes to fetch data from, e.g., ['US', 'CA']
MAX_RETRIES = 10  # Maximum number of retries per country

# === Import Statements ===
import requests
from bs4 import BeautifulSoup
import json
import re
import xml.etree.ElementTree as ET
import os
from urllib.parse import unquote, urlparse, urlunparse
from datetime import datetime
import unicodedata
import argparse
import logging
import ssl
import urllib3

# === SSL and Logging Configurations ===
# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# === Argument Parser for Command Line Options ===
parser = argparse.ArgumentParser(description='Scrape Tubi TV data.')
parser.add_argument('--countries', type=str, nargs='+', default=COUNTRIES, help='List of country codes.')
args = parser.parse_args()
countries = args.countries

# === Function Definitions ===

def get_proxies(country_code):
    url = f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country={country_code}&ssl=all&anonymity=elite"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        proxy_list = response.text.splitlines()
        return [f"socks4://{proxy}" for proxy in proxy_list]
    else:
        logging.warning(f"Failed to fetch proxies for {country_code}. Status code: {response.status_code}")
        return []

def fetch_channel_list(proxy):
    url = "https://tubitv.com/live"
    try:
        response = requests.get(url, proxies={"http": proxy, "https": proxy}, verify=False, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            logging.warning(f"Failed to fetch data from {url} using proxy {proxy}. Status code: {response.status_code}")
            return []

        html_content = response.content.decode('utf-8', errors='replace').replace('�', 'ñ')
        soup = BeautifulSoup(html_content, "html.parser")

        script_tags = soup.find_all("script")
        target_script = None
        for script in script_tags:
            if script.string and script.string.strip().startswith("window.__data"):
                target_script = script.string
                break

        if not target_script:
            logging.error("Error: Could not locate the JSON-like data in the page.")
            return []

        start_index = target_script.find("{")
        end_index = target_script.rfind("}") + 1
        json_string = target_script[start_index:end_index]

        json_string = json_string.encode('utf-8', errors='replace').decode('utf-8')
        json_string = json_string.replace('undefined', 'null')
        json_string = re.sub(r'new Date\("([^\"]*)"\)', r'"\1"', json_string)

        data = json.loads(json_string)
        logging.info("Successfully decoded JSON data!")
        return data
    except requests.RequestException as e:
        logging.error(f"Error fetching data using proxy {proxy}: {e}")
        return []

def create_group_mapping(json_data):
    group_mapping = {}
    json_data = [json_data] if not isinstance(json_data, list) else json_data
    for item in json_data:
        content_ids_by_container = item.get('epg', {}).get('contentIdsByContainer', {})
        for container_list in content_ids_by_container.values():
            for category in container_list:
                group_name = category.get('name', 'Other')
                for content_id in category.get('contents', []):
                    group_mapping[str(content_id)] = group_name
    return group_mapping

def fetch_epg_data(channel_list):
    epg_data = []
    group_size = 150
    grouped_ids = [channel_list[i:i + group_size] for i in range(0, len(channel_list), group_size)]
    for group in grouped_ids:
        url = "https://tubitv.com/oz/epg/programming"
        params = {"content_id": ','.join(map(str, group))}
        try:
            response = requests.get(url, params=params, verify=False, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch EPG data for group {group}. Status code: {response.status_code}")
                continue
            epg_json = response.json()
            epg_data.extend(epg_json.get('rows', []))
        except requests.RequestException as e:
            logging.error(f"Error fetching EPG data using proxy: {e}")
    return epg_data

def save_file(content, filename):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, filename)
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logging.info(f"File saved successfully: {file_path}")
    except Exception as e:
        logging.error(f"Failed to save file {file_path}: {e}")

def save_epg_to_file(tree, filename):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, filename)
    try:
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        logging.info(f"EPG XML file saved successfully: {file_path}")
    except Exception as e:
        logging.error(f"Failed to save EPG XML file {file_path}: {e}")

def main():
    for country in countries:
        proxies = get_proxies(country)
        if not proxies:
            logger.warning(f"No proxies found for country {country}. Skipping...")
            continue

        data_fetched = False
        retries = 0
        for proxy in proxies:
            if retries >= MAX_RETRIES:
                logger.error(f"Reached maximum retry limit for country {country}")
                break

            logger.info(f"Trying proxy {proxy} for country {country}...")
            json_data = fetch_channel_list(proxy)
            if json_data:
                channel_list = extract_channel_list(json_data)
                epg_data = fetch_epg_data(channel_list)
                group_mapping = create_group_mapping(json_data)
                m3u_playlist = create_m3u_playlist(epg_data, group_mapping, country.lower())
                epg_tree = create_epg_xml(epg_data)
                save_file(m3u_playlist, f"tubi_playlist_{country.lower()}.m3u")
                save_epg_to_file(epg_tree, f"tubi_epg_{country.lower()}.xml")
                data_fetched = True
                break
            else:
                retries += 1

        if not data_fetched:
            logger.error(f"Failed to fetch data for country {country} after trying all proxies.")

def extract_channel_list(json_data):
    channel_list = []
    json_data = [json_data] if not isinstance(json_data, list) else json_data
    for item in json_data:
        content_ids_by_container = item.get('epg', {}).get('contentIdsByContainer', {})
        for container_list in content_ids_by_container.values():
            for category in container_list:
                channel_list.extend(category.get('contents', []))
    return channel_list

def create_m3u_playlist(epg_data, group_mapping, country):
    sorted_epg_data = sorted(epg_data, key=lambda x: x.get('title', '').lower())
    playlist = f"#EXTM3U url-tvg=\"https://github.com/dtankdempse/tubi-m3u/raw/refs/heads/main/tubi_epg_{country}.xml\"\n"
    seen_urls = set()

    for elem in sorted_epg_data:
        channel_name = elem.get('title', 'Unknown Channel').encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        stream_url = unquote(elem['video_resources'][0]['manifest']['url']) if elem.get('video_resources') else ''
        clean_url = clean_stream_url(stream_url)
        tvg_id = str(elem.get('content_id', ''))
        logo_url = elem.get('images', {}).get('thumbnail', [None])[0]
        group_title = group_mapping.get(tvg_id, 'Other').encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        if clean_url and clean_url not in seen_urls:
            playlist += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo_url}" group-title="{group_title}",{channel_name}\n{clean_url}\n'
            seen_urls.add(clean_url)
    return playlist

def clean_stream_url(url):
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))

def create_epg_xml(epg_data):
    root = ET.Element("tv")
    for station in epg_data:
        channel = ET.SubElement(root, "channel", id=str(station.get("content_id")))
        display_name = ET.SubElement(channel, "display-name")
        display_name.text = station.get("title", "Unknown Title")

        thumbnails = station.get("images", {}).get("thumbnail", [])
        icon_src = thumbnails[0] if thumbnails else None
        if icon_src:
            ET.SubElement(channel, "icon", src=icon_src)

        for program in station.get('programs', []):
            programme = ET.SubElement(root, "programme", channel=str(station.get("content_id")))
            start_time = convert_to_xmltv_format(program.get("start_time", ""))
            stop_time = convert_to_xmltv_format(program.get("end_time", ""))
            programme.set("start", start_time)
            programme.set("stop", stop_time)
            title = ET.SubElement(programme, "title")
            title.text = program.get("title", "")
            if program.get("description"):
                desc = ET.SubElement(programme, "desc")
                desc.text = program.get("description", "")
    return ET.ElementTree(root)

def convert_to_xmltv_format(iso_time):
    try:
        dt = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y%m%d%H%M%S +0000")
    except ValueError:
        return iso_time

# Run main if script is executed directly
if __name__ == "__main__":
    main()
