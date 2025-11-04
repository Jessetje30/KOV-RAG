#!/bin/bash

# Script to fix Docker symlinks after reinstallation

echo "Fixing Docker symlinks..."
echo "You will be asked for your password."
echo ""

DOCKER_APP="/Applications/Docker.app/Contents/Resources/bin"

# Check if Docker Desktop is installed
if [ ! -d "$DOCKER_APP" ]; then
    echo "Error: Docker Desktop not found at /Applications/Docker.app"
    echo "Please install Docker Desktop first."
    exit 1
fi

# Remove old symlinks
echo "Removing old symlinks..."
sudo rm -f /usr/local/bin/docker
sudo rm -f /usr/local/bin/docker-compose
sudo rm -f /usr/local/bin/docker-credential-desktop
sudo rm -f /usr/local/bin/docker-credential-ecr-login
sudo rm -f /usr/local/bin/docker-credential-osxkeychain
sudo rm -f /usr/local/bin/docker-index
sudo rm -f /usr/local/bin/com.docker.cli
sudo rm -f /usr/local/bin/kubectl.docker
sudo rm -f /usr/local/bin/vpnkit

# Create new symlinks
echo "Creating new symlinks..."
sudo ln -s "$DOCKER_APP/docker" /usr/local/bin/docker
sudo ln -s "$DOCKER_APP/docker-compose" /usr/local/bin/docker-compose
sudo ln -s "$DOCKER_APP/docker-credential-desktop" /usr/local/bin/docker-credential-desktop
sudo ln -s "$DOCKER_APP/docker-credential-ecr-login" /usr/local/bin/docker-credential-ecr-login
sudo ln -s "$DOCKER_APP/docker-credential-osxkeychain" /usr/local/bin/docker-credential-osxkeychain
sudo ln -s "$DOCKER_APP/docker-index" /usr/local/bin/docker-index
sudo ln -s "$DOCKER_APP/com.docker.cli" /usr/local/bin/com.docker.cli

echo ""
echo "Done! Testing Docker..."
echo ""

# Test Docker
docker --version
docker compose version

echo ""
echo "✓ Docker is now accessible!"
echo ""
echo "Next steps:"
echo "1. Make sure Docker Desktop is running (check menu bar)"
echo "2. Run: ./start.sh"
