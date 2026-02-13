#!/bin/bash
# Deployment script for Country Capital App

set -e  # Exit on any error

echo "========================================"
echo "Starting deployment at $(date)"
echo "========================================"

cd ~/Architecture

echo "1. Pulling latest code..."
git pull origin dev

echo "2. Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo "3. Restarting Flask..."
pkill -f "flask run" || true
sleep 2
nohup flask run --host=0.0.0.0 --port=5000 > flask.log 2>&1 &

echo "4. Waiting for app to start..."
sleep 3

echo "5. Health check..."
if curl -s http://localhost:5000 | grep -q "Country Capital"; then
    echo "✓ Deployment successful!"
    echo "  App is running at http://$(curl -s ifconfig.me):5000"
else
    echo "✗ Deployment failed - health check failed"
    exit 1
fi

echo "========================================"
echo "Deployment completed at $(date)"
echo "========================================"
