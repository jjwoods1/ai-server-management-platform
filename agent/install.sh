#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
GITHUB_REPO="jjwoods1/ai-server-management-platform"
INSTALL_PATH="/opt/ai_agent"
SERVICE_NAME="ai_agent_service"
VENV_PATH="$INSTALL_PATH/.venv"

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
print_info "Starting agent installation..."

# 1. Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
  print_error "This script must be run as root. Please use 'sudo'."
fi

# 2. Install dependencies: git, python3, and venv
print_info "Installing required packages (git, python3, python3-venv)..."
apt-get update
apt-get install -y git python3 python3-venv

# 3. Clean up any old installations
print_info "Cleaning up previous installations..."
systemctl stop $SERVICE_NAME.service || true
rm -rf "$INSTALL_PATH"
rm -f "/etc/systemd/system/$SERVICE_NAME.service"

# 4. Clone the source code from GitHub
print_info "Cloning the agent source code from GitHub..."
git clone "https://github.com/$GITHUB_REPO.git" "$INSTALL_PATH"

# 5. Create and activate a Python virtual environment
print_info "Creating Python virtual environment at $VENV_PATH..."
python3 -m venv "$VENV_PATH"

# 6. Install Python dependencies into the virtual environment
print_info "Installing agent dependencies..."
"$VENV_PATH/bin/pip" install -r "$INSTALL_PATH/agent/requirements.txt"

# 7. Create and enable the systemd service
print_info "Creating systemd service..."
cat << EOF > /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=AI Server Management Agent
After=network.target

[Service]
Type=simple
User=root
# We run the main.py script using the python from our virtual environment
ExecStart=$VENV_PATH/bin/python $INSTALL_PATH/agent/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 8. Start the service
print_info "Starting the agent service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service
systemctl start $SERVICE_NAME.service

print_success "Agent installation complete! The agent is now running in the background."
