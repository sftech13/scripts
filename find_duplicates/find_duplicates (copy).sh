#!/bin/bash

# Define the directory to search and output directory
search_dir="/mnt/Media"
output_dir="/home/user"

# Function to find and list duplicates
find_duplicates() {
  # Find all video files with the specified extensions and output them to a temporary file
  find "$search_dir" -type f \( -iname "*.mkv" -o -iname "*.mp4" -o -iname "*.avi" -o -iname "*.ts" \) > /tmp/all_videos.txt

  echo "Files found:"
  cat /tmp/all_videos.txt

  # Check if any video files were found
  if [ ! -s /tmp/all_videos.txt ]; then
    echo "No video files found in $search_dir."
    rm /tmp/all_videos.txt
    return
  fi

  # Extract filenames and count occurrences
  awk -F/ '{print $NF}' /tmp/all_videos.txt | sort | uniq -d > /tmp/duplicate_names.txt

  echo "Potential duplicate filenames:"
  cat /tmp/duplicate_names.txt

  # Check if any duplicate filenames were found
  if [ ! -s /tmp/duplicate_names.txt ]; then
    echo "No duplicate video files found in $search_dir."
    rm /tmp/all_videos.txt /tmp/duplicate_names.txt
    return
  fi

  # Collect full paths of duplicate files and output to a file
  {
    echo -e "Count\tName\tGroup"
    while IFS= read -r name; do
      files=$(awk -v filename="$name" -F/ '$NF == filename {print}' /tmp/all_videos.txt)
      count=$(echo "$files" | wc -l)
      paths=$(echo "$files" | tr '\n' ' ')
      echo -e "${count}\t${name}\t${paths}"
    done < /tmp/duplicate_names.txt
  } > "$output_dir/Duplicates.txt"

  # Clean up temporary files
  rm /tmp/all_videos.txt /tmp/duplicate_names.txt

  echo "Duplicate video files have been listed in $output_dir/Duplicates.txt"
}

# Check if the search directory exists
if [ ! -d "$search_dir" ]; then
  echo "Search directory $search_dir does not exist."
  exit 1
fi

# Check if the output directory exists
if [ ! -d "$output_dir" ]; then
  echo "Output directory $output_dir does not exist."
  exit 1
fi

# Run the duplicate finder
find_duplicates

