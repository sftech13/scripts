import os
import xml.etree.ElementTree as ET
from PIL import Image, ImageFile
import requests
from io import BytesIO
import hashlib
import logging
import time

# Define paths
XMLTV_FILE = '/home/sftech13/IPTV/data/home.xml'
OUTPUT_DIR = '/home/sftech13/IPTV/data/icons'
LOG_DIR = '/home/sftech13/logs/'
LOG_FILE = os.path.join(LOG_DIR, 'icon_script.log')

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logging to overwrite the log file on each run
logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',  # 'w' mode to overwrite the log file each time
    level=logging.INFO,  # Use INFO level to reduce log size
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Ensures that partial images can still be processed
ImageFile.LOAD_TRUNCATED_IMAGES = True

def get_unique_filename(channel_id, directory):
    """Generate a unique filename based on the channel ID and save location."""
    filename = f"{hashlib.md5(channel_id.encode('utf-8')).hexdigest()}.png"
    return os.path.join(directory, filename)

def download_and_resize_icon(image_url, output_path, target_size=(500, 750), retries=3):
    """Download and resize the image to the target size while maintaining the aspect ratio, then save it with optional padding."""
    attempt = 0
    target_width, target_height = target_size
    while attempt < retries:
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                
                original_width, original_height = image.size
                aspect_ratio = original_height / original_width
                if original_width < original_height:
                    resized_height = target_height
                    resized_width = int(target_height / aspect_ratio)
                else:
                    resized_width = target_width
                    resized_height = int(target_width * aspect_ratio)
                
                image = image.resize((resized_width, resized_height), Image.ANTIALIAS)
                
                new_image = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
                offset_x = (target_width - resized_width) // 2
                offset_y = (target_height - resized_height) // 2
                new_image.paste(image, (offset_x, offset_y), image.convert("RGBA"))
                
                new_image.save(output_path)
                logging.info(f"Downloaded and resized icon from {image_url}")
                return output_path
            else:
                logging.error(f"Error downloading image: HTTP {response.status_code} for {image_url}")
                return None
        except Exception as e:
            attempt += 1
            if attempt >= retries:
                logging.error(f"Failed to download image from {image_url} after {retries} attempts.")
                return None

def copy_channel_icons_to_programmes(xmltv_file, output_dir, target_width=500, target_height=750):
    try:
        tree = ET.parse(xmltv_file)
        root = tree.getroot()
    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {xmltv_file}: {e}")
        return

    os.makedirs(output_dir, exist_ok=True)
    channel_icons = {}

    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        unique_filename = get_unique_filename(channel_id, output_dir)
        
        if os.path.exists(unique_filename):
            channel_icons[channel_id] = unique_filename
        else:
            icon = channel.find('icon')
            if icon is not None:
                icon_url = icon.attrib['src']
                resized_icon_path = download_and_resize_icon(icon_url, unique_filename, target_size=(target_width, target_height))
                if resized_icon_path:
                    channel_icons[channel_id] = resized_icon_path
                else:
                    logging.error(f"Failed to download or resize icon for channel {channel_id}")
            else:
                logging.warning(f"No icon element found in the original XML for channel {channel_id}")

    for programme in root.findall('programme'):
        icon = programme.find('icon')
        channel_ref = programme.get('channel')
        if icon is None and channel_ref in channel_icons:
            new_icon = ET.Element('icon')
            filename = os.path.basename(channel_icons[channel_ref])
            new_icon.set('src', f"https://plex.webhop.me/icons/{filename}")
            programme.append(new_icon)
            logging.info(f"Added new icon to programme for channel {channel_ref}")

    tree.write(xmltv_file, encoding='UTF-8', xml_declaration=True)
    logging.info(f"Updated XMLTV file saved at {xmltv_file}")

# Run the script
copy_channel_icons_to_programmes(XMLTV_FILE, OUTPUT_DIR)

