#!/bin/bash

# Define the password file path
PASSWORD_FILE="/home/sftech13/scripts/emby_ssl/key_password.txt"
EXPORT_PASSWORD_FILE="/home/sftech13/scripts/emby_ssl/export_password.txt"

# Run openssl command with password from file
if openssl pkcs12 -export -out /home/sftech13/scripts/emby_ssl/combined.pfx \
-inkey /etc/nginx/ssl/plex.webhop.me/key.pem \
-in /etc/nginx/ssl/plex.webhop.me/fullchain.pem \
-certfile /etc/nginx/ssl/plex.webhop.me/chain.pem \
-passin file:$PASSWORD_FILE -passout file:$EXPORT_PASSWORD_FILE; then
    echo "PFX file created successfully."
else
    echo "Failed to create PFX file." >&2
    exit 1
fi

# Set ownership and permissions
chown emby:emby /home/sftech13/scripts/emby_ssl/combined.pfx
chmod 644 /home/sftech13/scripts/emby_ssl/combined.pfx

echo "Ownership and permissions set."



#PFX Creation crontab
#0 0 1 1,3,5,7,9,11 * /home/sftech13/scripts/cert/cert.sh >> /home/sftech13/scripts/cert/cert.log 2>&1

#openssl pkcs12 -export -out /home/sftech13/scripts/cert/combined.pfx -inkey /etc/nginx/ssl/plex.webhop.me/key.pem -in /etc/nginx/ssl/plex.webhop.me/fullchain.pem -certfile /etc/nginx/ssl/plex.webhop.me/chain.pem -passin file:/home/sftech13/scripts/cert/key_password.txt

#this works from terminal
#sudo /home/sftech13/scripts/emby_ssl/cert.sh >> /home/sftech13/logs/emby_ssl.log 2>&1
