#!/bin/bash

# Set email for SSH key
EMAIL="sftech13@gmail.com"
KEY_PATH="/home/sftech13/.ssh/id_ed25519"

# Check if SSH key already exists
if [ -f "$KEY_PATH" ]; then
    echo "SSH key already exists at $KEY_PATH"
else
    # Generate a new SSH key
    ssh-keygen -t ed25519 -C "$EMAIL" -f "$KEY_PATH" -N ""
    echo "New SSH key generated at $KEY_PATH"
fi

# Start the SSH agent if it's not already running
if ! pgrep -u "$USER" ssh-agent > /dev/null; then
    eval "$(ssh-agent -s)"
    echo "SSH agent started"
fi

# Add the SSH key to the agent
ssh-add "$KEY_PATH"
echo "SSH key added to the agent"

# Display the SSH public key
echo "Copy the following SSH key and add it to your GitHub account:"
cat "$KEY_PATH.pub"

# Instructions to add the SSH key to GitHub
echo -e "\nTo add your SSH key to GitHub, follow these steps:"
echo "1. Copy the SSH key above."
echo "2. Go to https://github.com/settings/ssh/new"
echo "3. Click 'New SSH key', enter a title (e.g., 'Ubuntu 22.04'), and paste the key."
echo "4. Click 'Add SSH key'."

# Test SSH connection to GitHub
echo -e "\nTesting SSH connection to GitHub..."
ssh -T git@github.com

