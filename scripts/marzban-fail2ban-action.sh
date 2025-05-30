#!/bin/bash

# Enhanced Marzban Fail2ban Action Script
# This script is called by Fail2ban to ban/unban users through the Marzban API

# Configuration
MARZBAN_API_URL="http://localhost:8000/api"
MARZBAN_API_TOKEN=""  # Set your admin API token here
LOG_FILE="/var/log/marzban/fail2ban-actions.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to extract username from log line
extract_username() {
    local log_line="$1"
    echo "$log_line" | grep -oP 'USER=\K[^\s]+'
}

# Function to call Marzban API
call_marzban_api() {
    local action="$1"
    local ip="$2"
    local username="$3"
    local reason="$4"
    
    local api_endpoint="$MARZBAN_API_URL/fail2ban/action"
    
    local json_data=$(cat <<EOF
{
    "action": "$action",
    "ip_address": "$ip",
    "username": "$username",
    "reason": "$reason",
    "duration": 3600
}
EOF
)
    
    local response=$(curl -s -X POST "$api_endpoint" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $MARZBAN_API_TOKEN" \
        -d "$json_data")
    
    if [ $? -eq 0 ]; then
        log_message "API call successful: $action $username from $ip"
        echo "$response"
    else
        log_message "API call failed: $action $username from $ip"
        return 1
    fi
}

# Main script logic
ACTION="$1"
IP="$2"
LOG_MATCHES="$3"

if [ -z "$ACTION" ] || [ -z "$IP" ] || [ -z "$LOG_MATCHES" ]; then
    log_message "Error: Missing required parameters"
    echo "Usage: $0 <ban|unban> <ip> <log_matches>"
    exit 1
fi

# Extract username from log matches
USERNAME=$(extract_username "$LOG_MATCHES")

if [ -z "$USERNAME" ]; then
    log_message "Error: Could not extract username from log matches: $LOG_MATCHES"
    exit 1
fi

# Determine reason based on action
if [ "$ACTION" = "ban" ]; then
    REASON="fail2ban_violation"
elif [ "$ACTION" = "unban" ]; then
    REASON="fail2ban_unban"
else
    log_message "Error: Invalid action: $ACTION"
    exit 1
fi

# Check if API token is configured
if [ -z "$MARZBAN_API_TOKEN" ]; then
    log_message "Error: MARZBAN_API_TOKEN not configured"
    exit 1
fi

# Call Marzban API
log_message "Processing $ACTION for user $USERNAME from IP $IP"
call_marzban_api "$ACTION" "$IP" "$USERNAME" "$REASON"

if [ $? -eq 0 ]; then
    log_message "Successfully processed $ACTION for user $USERNAME from IP $IP"
    exit 0
else
    log_message "Failed to process $ACTION for user $USERNAME from IP $IP"
    exit 1
fi
