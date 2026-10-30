#!/bin/bash
# Starts both the Django production server and Cloudflare live tunnel in persistent background mode
cd "$(dirname "$0")"
source .venv/bin/activate

# Terminate any existing instances on port 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
pkill -f "cloudflared tunnel --url http://127.0.0.1:8001" 2>/dev/null || true

echo "Starting Django server on 0.0.0.0:8001..."
nohup python manage.py runserver 0.0.0.0:8001 > /dev/null 2>&1 &
sleep 2

echo "Starting Cloudflare live tunnel..."
nohup cloudflared tunnel --url http://127.0.0.1:8001 > tunnel.log 2>&1 &
sleep 4

TUNNEL_URL=$(grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' tunnel.log | head -n 1)
echo "-----------------------------------------------------"
echo " PollMaster is live and running!"
echo " Live URL: $TUNNEL_URL"
echo "-----------------------------------------------------"
