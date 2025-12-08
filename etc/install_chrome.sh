#!/bin/bash

set -e  # Stop on error

echo "=== Updating system ==="
sudo apt -y update
sudo apt install -y wget curl unzip

echo "=== Installing U2F dependencies ==="
wget http://archive.ubuntu.com/ubuntu/pool/main/libu/libu2f-host/libu2f-udev_1.1.4-1_all.deb
sudo dpkg -i libu2f-udev_1.1.4-1_all.deb

echo "=== Installing Google Chrome ==="
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt --fix-broken install -y

echo "=== Detecting Chrome version ==="
CHROME_VERSION=$(google-chrome --version | sed -E 's/.* ([0-9]+)\..*/\1/')
echo "Detected Chrome major version: $CHROME_VERSION"

echo "=== Installation completed ==="
