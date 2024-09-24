#!/bin/bash

# Get CPU architecture
CPU=$(dpkg --print-architecture)

# Fetch the latest release tag from GitHub API
LATEST_TAG=$(curl -s https://api.github.com/repos/walrusone/iptvboss-release/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

# Define the download URL based on the latest tag
URL="https://github.com/walrusone/iptvboss-release/releases/download/${LATEST_TAG}/iptvboss_${LATEST_TAG}_${CPU}.deb"

# Download the latest version of iptvboss
wget -O /tmp/iptvboss_latest.deb $URL

# Install the downloaded package
sudo apt install -y /tmp/iptvboss_latest.deb

# Clean up the downloaded package
rm /tmp/iptvboss_latest.deb

