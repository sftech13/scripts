#!/bin/bash

# Define the log file path
log_file="$HOME/logs/duplicates_log.txt"

# Define the directory to search and output directory
search_dir="/mnt/Media"
output_dir="$HOME"

# Function to calculate the quality score
calculate_quality_score() {
  local file=$1

  # Get video properties using ffprobe
  resolution=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$file")
  bitrate=$(ffprobe -v error -select_streams v:0 -show_entries format=bit_rate -of default=nokey=1:noprint_wrappers=1 "$file")
  duration=$(ffprobe -v error -select_streams v:0 -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 "$file")
  codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "$file")

  # Calculate resolution score (higher resolution, higher score)
  IFS='x' read -r width height <<< "$resolution"
  resolution_score=$((width * height / 1000))

  # Calculate bitrate score (higher bitrate, higher score)
  bitrate_score=$((bitrate / 100000))

  # Calculate duration score (longer duration, higher score)
  duration_score=$((duration / 60))

  # Calculate codec score (assign scores based on codec type)
  case $codec in
    h264) codec_score=10 ;;
    hevc) codec_score=15 ;;
    *) codec_score=5 ;;
  esac

  # Calculate total score
  total_score=$((resolution_score + bitrate_score + duration_score + codec_score))

  echo "$total_score"
}

# Function to find and list duplicates
find_duplicates() {
  # Find all video files with the specified extensions and output them to a temporary file
  find "$search_dir" -type f \( -iname "*.mkv" -o -iname "*.mp4" -o -iname "*.avi" -o -iname "*.ts" \) > /tmp/all_videos.txt

  echo "Files found:" >> "$log_file"
  cat /tmp/all_videos.txt >> "$log_file"

  # Check if any video files were found
  if [ ! -s /tmp/all_videos.txt ]; then
    echo "No video files found in $search_dir." >> "$log_file"
    rm /tmp/all_videos.txt
    return
  fi

  # Extract filenames and count occurrences
  awk -F/ '{print $NF}' /tmp/all_videos.txt | sort | uniq -d > /tmp/duplicate_names.txt

  echo "Potential duplicate filenames:" >> "$log_file"
  cat /tmp/duplicate_names.txt >> "$log_file"

  # Check if any duplicate filenames were found
  if [ ! -s /tmp/duplicate_names.txt ]; then
    echo "No duplicate video files found in $search_dir." >> "$log_file"
    rm /tmp/all_videos.txt /tmp/duplicate_names.txt
    return
  fi

  # Collect full paths of duplicate files and output to a file
  {
    echo -e "Count\tName\tGroup\tBestQuality\tBestQualityScore"
    while IFS= read -r name; do
      files=$(awk -v filename="$name" -F/ '$NF == filename {print}' /tmp/all_videos.txt)
      count=$(echo "$files" | wc -l)
      paths=$(echo "$files" | tr '\n' ' ')

      # Find the file with the best quality
      best_quality=""
      best_quality_score=0
      for file in $files; do
        quality_score=$(calculate_quality_score "$file")
        if [ "$quality_score" -gt "$best_quality_score" ]; then
          best_quality="$file"
          best_quality_score="$quality_score"
        fi
      done

      echo -e "${count}\t${name}\t${paths}\t${best_quality}\t${best_quality_score}"
    done < /tmp/duplicate_names.txt
  } > "$output_dir/Duplicates.txt"

  # Clean up temporary files
  rm /tmp/all_videos.txt /tmp/duplicate_names.txt

  echo "Duplicate video files have been listed in $output_dir/Duplicates.txt" >> "$log_file"
}

# Check if the search directory exists
if [ ! -d "$search_dir" ]; then
  echo "Search directory $search_dir does not exist." >> "$log_file"
  exit 1
fi

# Check if the output directory exists
if [ ! -d "$output_dir" ]; then
  echo "Output directory $output_dir does not exist." >> "$log_file"
  exit 1
fi

# Run the duplicate finder
find_duplicates >> "$log_file" 2>&1

