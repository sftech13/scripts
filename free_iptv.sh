#!/bin/bash

# Define the base URL
BASE_URL="https://script.google.com/macros/s/AKfycbxYK11-9OMrhMTDMvn54B8OigOaFzm65YWDP8lzX2XVI7i3Rkz-jsMsqGtRj6PqXDZq0Q/exec?region=us&service="

# Define the output directory
OUTPUT_DIR="/home/sftech13/IPTV/data"

# Logging directory
LOG_DIR="/home/sftech13/logs"

# Output file for the merged M3U
MERGED_OUTPUT="${OUTPUT_DIR}/free_iptv.m3u"

# Services to download (uncomment to enable)
# SERVICES=("Plex" "Roku" "SamsungTVPlus" "PlutoTV" "PBS" "PBSKids" "Stirr")

# Uncomment the services you want to download
SERVICES=(
    "Plex"
    "Roku"
    "SamsungTVPlus"
    "PlutoTV"
    # "PBS"
    # "PBSKids"
    "Stirr"
)

# Function to download M3U files
download_m3u_files() {
    for SERVICE in "${SERVICES[@]}"; do
        M3U_URL="${BASE_URL}${SERVICE}"
        OUTPUT_PATH="${OUTPUT_DIR}/${SERVICE}.m3u"
        LOG_FILE="${LOG_DIR}/${SERVICE}.log"

        # Use curl to download the file
        curl -L -o "$OUTPUT_PATH" "$M3U_URL"

        # Log the download status
        echo "$(date) - Downloaded M3U file for $SERVICE to $OUTPUT_PATH" >> "$LOG_FILE"
    done
}

# Function to merge M3U files into one
merge_m3u_files() {
    # Create or clear the merged output file
    > "$MERGED_OUTPUT"

    # Add a header for the merged M3U file
    echo "#EXTM3U" >> "$MERGED_OUTPUT"

    # Append the contents of each downloaded M3U file to the merged file
    for SERVICE in "${SERVICES[@]}"; do
        OUTPUT_PATH="${OUTPUT_DIR}/${SERVICE}.m3u"
        
        # Check if the file exists before merging
        if [ -f "$OUTPUT_PATH" ]; then
            # Skip the header line (#EXTM3U) from each file to avoid duplicates
            tail -n +2 "$OUTPUT_PATH" >> "$MERGED_OUTPUT"
        fi
    done

    echo "$(date) - Merged M3U files into $MERGED_OUTPUT"
}

# Function to delete M3U files after merging
delete_m3u_files() {
    for SERVICE in "${SERVICES[@]}"; do
        OUTPUT_PATH="${OUTPUT_DIR}/${SERVICE}.m3u"
        
        # Check if the file exists before deleting
        if [ -f "$OUTPUT_PATH" ]; then
            rm "$OUTPUT_PATH"
            echo "$(date) - Deleted M3U file $OUTPUT_PATH"
        fi
    done
}

# Main script execution
download_m3u_files
merge_m3u_files
delete_m3u_files

