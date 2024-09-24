#!/bin/bash

# Usage example:
# ./script_name.sh /path/to/directory

# Check if a directory path is provided as an argument
if [ -z "$1" ]; then
    echo "Error: Directory path not provided."
    echo "Usage: $0 <directory_path>"
    exit 1
fi

directory_path="$1"

# Set permissions recursively for the directory
chmod -R u+rwX "$directory_path"
chmod -R g+rwX "$directory_path"
chmod -R o+rX "$directory_path"

# Set default ACLs
setfacl -R -d -m u::rwX "$directory_path"
setfacl -R -d -m g::rwX "$directory_path"
setfacl -R -d -m o::r-X "$directory_path"

echo "Permissions and default ACLs set successfully for $directory_path"

