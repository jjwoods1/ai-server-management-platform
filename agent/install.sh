#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# THIS IS THE CORRECTED LINE:
GITHUB_REPO="jjwoods1/ai-server-management-platform"
AGENT_NAME="ai_agent"
INSTALL_DIR="/usr/local/bin"
SERVICE_NAME="ai_agent_service"

# --- Helper Functions ---
function print_info() {
    echo -e "\e[34m[INFO]\e[0m $1"
}

function print_success() {
    echo -e "\e[32m[SUCCESS]\e[0m $1"
}

function print_error() {
    echo -e "\e[31m[ERROR]\e[0m $1"
    exit 1
}

# --- Installation Logic ---

# 1. Get Installation Token from command line argument
TOKEN=""
if [[ "$1" == "--token="* ]]; then
  TOKEN="${1#*=}"
fi

if [ -z "$TOKEN" ]; then
  print_error "Installation token is missing. Please use the command from your dashboard."
fi

print_info "Starting agent installation..."

# 2. Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
  print_error "This script must be run as root. Please use 'sudo'."
fi

# 3. Detect latest agent version from GitHub Releases
print_info "Fetching latest agent version..."
LATEST_TAG=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_TAG" ]; then
    print_error "Could not fetch the latest release tag from GitHub. Make sure a release has been published."
fi
print_info "Latest version is $LATEST_TAG"

# 4. Download the agent binary
DOWNLOAD_URL="https://github.com/$GITHUB_REPO/releases/download/$LATEST_TAG/$AGENT_NAME"
print_info "Downloading agent from $DOWNLOAD_URL..."
curl -L "$DOWNLOAD_URL" -o "$INSTALL_DIR/$AGENT_NAME"

# 5. Make the agent executable
print_info "Setting permissions..."
chmod +x "$INSTALL_DIR/$AGENT_NAME"

# 6. Create the agent configuration file
# This part is now handled by the agent itself, which reads the token from the service file.

# 7. Create and enable the systemd service to run the agent in the background
print_info "Creating systemd service..."
# The ExecStart line now passes the token directly to the agent process
cat << EOF > /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=AI Server Management Agent
After=network.target

[Service]
Type=simple
User=root
ExecStart=$INSTALL_DIR/$AGENT_NAME --token=$TOKEN
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 8. Start the service
print_info "Starting the agent service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service
systemctl start $SERVICE_NAME.service

print_success "Agent installation complete! The agent is now running in the background."
