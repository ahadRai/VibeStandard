#!/bin/bash
# Initialize Let's Encrypt certificates for VibeStandard
# IMPORTANT: Run this BEFORE starting docker compose (port 80 must be free)
# Usage: ./certbot-init.sh yourdomain.com your@email.com

set -e

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: ./certbot-init.sh <domain> <email>"
    echo "Example: ./certbot-init.sh vibestandard.com admin@vibestandard.com"
    echo ""
    echo "IMPORTANT: Stop all containers first: docker compose down"
    exit 1
fi

echo "Obtaining SSL certificate for $DOMAIN..."
echo "Make sure port 80 is free (docker compose down) and DNS points to this server."

# Create required directories
mkdir -p certbot/conf certbot/www

# Obtain certificate using standalone mode (needs port 80 free)
docker run --rm \
    -p 80:80 \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --standalone \
    --preferred-challenges http \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive

echo ""
echo "Certificate obtained successfully."
echo ""
echo "Now update your .env file:"
echo "  DOMAIN=$DOMAIN"
echo "  VITE_API_URL=https://$DOMAIN/api"
echo "  CORS_ORIGINS=https://$DOMAIN"
echo ""
echo "Then start the stack:"
echo "  docker compose build --no-cache"
echo "  docker compose up -d"
