#!/bin/bash
# Check EC2 Instance Status
# Usage: ./check_status.sh

# Your instance ID (found from document_setup.sh)
INSTANCE_ID="i-079b2b1dacd655cf4"

echo "Checking EC2 instance: $INSTANCE_ID"
echo ""

# Get instance state
STATE=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text)

# Get public IP (might be empty if stopped)
IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

# Display status with color
if [ "$STATE" == "running" ]; then
    echo "✓ Status: RUNNING"
    echo "  Public IP: $IP"
    echo "  Flask URL: http://$IP:5000"
elif [ "$STATE" == "stopped" ]; then
    echo "✗ Status: STOPPED"
    echo "  No public IP (instance is off)"
else
    echo "? Status: $STATE"
fi
