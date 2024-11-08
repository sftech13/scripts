import requests
import json

# User Options 'Plex', 'Roku', 'SamsungTVPlus', 'PlutoTV', 'PBS', 'PBSKids', 'Stirr', 'Tubi'
SERVICES = ['SamsungTVPlus', 'Tubi']

REGION = 'us'        # Region code, e.g., 'us', 'mx', 'all'
SORT = 'name'        # Sort criteria, 'name' or 'chno'

# Error handler
def handle_error(message):
    print(message)
    return f"Error: {message}"

# Fetch JSON data
def fetch_json(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return handle_error(f"Failed to fetch data: {e}")

# PlutoTV service handler
def handle_pluto(region, sort):
    PLUTO_URL = 'https://i.mjh.nz/PlutoTV/.channels.json'
    data = fetch_json(PLUTO_URL)
    if isinstance(data, str): return data  # If error message, return it

    output = f'#EXTM3U url-tvg="https://github.com/matthuisman/i.mjh.nz/raw/master/PlutoTV/{region}.xml.gz"\n'
    channels = {}

    if region == 'all':
        for region_key, region_data in data["regions"].items():
            for channel_key, channel in region_data["channels"].items():
                channels[f"{channel_key}-{region_key}"] = channel
    else:
        if region not in data["regions"]:
            return handle_error(f"Region '{region}' not found in Pluto data.")
        channels = data["regions"][region]["channels"]

    sorted_channels = sorted(channels.items(), key=lambda item: item[1].get(sort, "name"))
    for channel_id, channel in sorted_channels:
        output += f'#EXTINF:-1 channel-id="{channel_id}" tvg-id="{channel_id}" tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}", {channel["name"]}\n'
        output += f'https://jmp2.uk/plu-{channel_id.split("-")[0]}.m3u8\n'
    return output

# Plex service handler
def handle_plex(region, sort):
    PLEX_URL = 'https://i.mjh.nz/Plex/.channels.json'
    CHANNELS_JSON_URL = 'https://raw.githubusercontent.com/dtankdempse/free-iptv-channels/main/plex/channels.json'
    data = fetch_json(PLEX_URL)
    plex_channels = fetch_json(CHANNELS_JSON_URL)
    if isinstance(data, str): return data
    if isinstance(plex_channels, str): return plex_channels

    output = f'#EXTM3U url-tvg="https://github.com/matthuisman/i.mjh.nz/raw/master/Plex/{region}.xml.gz"\n'
    channels = {}

    if region == 'all':
        for region_key in data["regions"]:
            for channel_key, channel in data["channels"].items():
                if region_key in channel["regions"]:
                    channels[f"{channel_key}-{region_key}"] = channel
    else:
        if region not in data["regions"]:
            return handle_error(f"Region '{region}' not found in Plex data.")
        channels = {key: val for key, val in data["channels"].items() if region in val["regions"]}

    sorted_channels = sorted(channels.items(), key=lambda item: item[1].get(sort, "name"))
    for channel_id, channel in sorted_channels:
        output += f'#EXTINF:-1 channel-id="{channel_id}" tvg-id="{channel_id}" tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}", {channel["name"]}\n'
        output += f'https://jmp2.uk/plex-{channel_id.split("-")[0]}.m3u8\n'
    return output

# SamsungTVPlus service handler
def handle_samsungtvplus(region, sort):
    SAMSUNG_URL = 'https://i.mjh.nz/SamsungTVPlus/.channels.json'
    data = fetch_json(SAMSUNG_URL)
    if isinstance(data, str): return data

    output = f'#EXTM3U url-tvg="https://github.com/matthuisman/i.mjh.nz/raw/master/SamsungTVPlus/{region}.xml.gz"\n'
    channels = {}

    if region == 'all':
        for region_key in data["regions"]:
            for channel_key, channel in data["regions"][region_key]["channels"].items():
                channels[f"{channel_key}-{region_key}"] = channel
    else:
        if region not in data["regions"]:
            return handle_error(f"Region '{region}' not found in SamsungTVPlus data.")
        channels = data["regions"][region]["channels"]

    sorted_channels = sorted(channels.items(), key=lambda item: item[1].get(sort, "name"))
    for channel_id, channel in sorted_channels:
        output += f'#EXTINF:-1 channel-id="{channel_id}" tvg-id="{channel_id}" tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}", {channel["name"]}\n'
        output += f'https://jmp2.uk/sam-{channel_id.split("-")[0]}.m3u8\n'
    return output

# PBSKids service handler
def handle_pbskids():
    PBSKIDS_URL = 'https://i.mjh.nz/PBS/.kids_app.json'
    EPG_URL = 'https://github.com/matthuisman/i.mjh.nz/raw/master/PBS/kids_all.xml.gz'
    
    data = fetch_json(PBSKIDS_URL)
    if isinstance(data, str): return data  # If error message, return it

    output = f'#EXTM3U url-tvg="{EPG_URL}"\n'
    sorted_keys = sorted(data["channels"].keys(), key=lambda k: data["channels"][k]["name"].lower())
    for key in sorted_keys:
        channel = data["channels"][key]
        output += f'#EXTINF:-1 channel-id="pbskids-{key}" tvg-id="{key}" tvg-logo="{channel["logo"]}", {channel["name"]}\n'
        output += f'{channel["url"]}\n'
    return output

# Tubi service handler
def handle_tubi():
    TUBI_PLAYLIST_URL = 'https://github.com/dtankdempse/tubi-m3u/raw/refs/heads/main/tubi_playlist_us.m3u'
    TUBI_EPG_URL = 'https://raw.githubusercontent.com/dtankdempse/tubi-m3u/refs/heads/main/tubi_epg_us.xml'
    data = requests.get(TUBI_PLAYLIST_URL).text

    output = f'#EXTM3U url-tvg="{TUBI_EPG_URL}"\n'
    output += data
    return output

def generate_m3u(service, region, sort):
    if service.lower() == 'plutotv':
        return handle_pluto(region, sort)
    elif service.lower() == 'plex':
        return handle_plex(region, sort)
    elif service.lower() == 'samsungtvplus':
        return handle_samsungtvplus(region, sort)
    elif service.lower() == 'tubi':
        return handle_tubi()
    elif service.lower() == 'pbskids':
        return handle_pbskids()
    else:
        return handle_error("Unsupported service type")

# Generate and save M3U files for each service in SERVICES
for service in SERVICES:
    m3u_content = generate_m3u(service, REGION, SORT)
    output_file_path = f"{service}.m3u"  # Create a unique file for each service
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(m3u_content)
    print(f"M3U content for {service} saved to {output_file_path}")
