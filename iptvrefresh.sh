#!/bin/bash

# Change to the correct directory
cd /var/www/IPTVBoss || { echo "Failed to change directory"; exit 1; }



# Execute IPTVBOSS without GUI and capture output to avoid interfering with HTTP headers
iptvboss -nogui > /home/sftech13/logs/iptv_refresh.log 2>&1

# Output Content-Type header
echo "Content-Type: text/html"
echo

# Notify that the Python script is running
echo "Running Python script to update XMLTV file icons"

# Check if running with root privileges
if [ "$(id -u)" -eq 0 ]; then
    # If running as root, run Python script normally
    /usr/bin/python3 '/home/sftech13/scripts/icon_epg/icon.py' > /dev/null 2>&1
else
    # If not running as root, run the Python script directly
    python3 '/home/sftech13/scripts/icon_epg/icon.py' > /dev/null 2>&1
fi

# Add a 10-second delay
sleep 5

# Notify that the Python script is running
echo "EMBY Guide Refresh command sent to server."

# Emby Server configuration
EMBY_SERVER_URL="http://plex.webhop.me:8096"
EMBY_API_KEY="5248dd4481514c56b8a8059a015ec03d"
EMBY_SCHEDULED_TASK_ID="9492d30c70f7f1bec3757c9d0a4feb45"
EMBY_GUIDE_REFRESH_URL="$EMBY_SERVER_URL/emby/ScheduledTasks/Running/$EMBY_SCHEDULED_TASK_ID?api_key=$EMBY_API_KEY"

# Refresh TV guide data, capturing output
curl -X POST "$EMBY_GUIDE_REFRESH_URL" > /dev/null 2>&1

# Check for success
if [ $? -eq 0 ]; then
  echo "IPTV BOSS, EPG Icon additions, and Emby Live TV guide refresh initiated successfully."
else
  echo "IPTV BOSS, EPG Icon additions and Emby Live TV guide refresh failed."
  exit 1
fi

# Output HTML that triggers a redirect
cat <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=/thank-you">
    <title>Redirecting...</title>
</head>
<body>
    <p>If you are not redirected automatically, follow this <a href="/thank-you">link</a>.</p>
</body>
</html>
EOF

