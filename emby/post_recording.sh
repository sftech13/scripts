#!/bin/bash

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$log_file"
}

# Set input directory, log file, and Comskip INI path
input_directory="/media/Recordings/"
log_file="$HOME/logs/post_recording_log.log"
comskip_ini="$HOME/IPTV/Comskip/comskip.ini"

# Log script starting
log_message "Script starting at $(date)"

# Loop through all .ts files in the input directory
find "$input_directory" -type f -name "*.ts" -print0 | while IFS= read -r -d '' input_file; do
    # Generate output file name based on the input file (keeping the original name)
    output_file="${input_file%.*}.mkv"
    temp_file="${input_file%.*}_temp.ts"
    subtitle_file="${input_file%.*}.srt"

    # Print debug information
    log_message "Processing $input_file"
    log_message "Output: $output_file"
    log_message "Temp: $temp_file"
    log_message "Subtitle: $subtitle_file"

    # Run FFmpeg to convert the file, extract subtitles, retain metadata, and format audio to Dolby AC-3
    ffmpeg -i "$input_file" -c:v libx264 -c:a ac3 -strict experimental \
           -b:a 384k -scodec mov_text -map_metadata 0 "$output_file" -y

    # Run Comskip
    comskip --ini="$comskip_ini" "$output_file"

    # Extract subtitles
    ffmpeg -i "$input_file" -map 0:s:0 "$subtitle_file"

    # Remove the source file
    rm -f "$input_file"

    # Rest of your script remains unchanged...
done

# Log script ending
log_message "Script Ending at $(date)"

