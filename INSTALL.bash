#!/bin/bash

# Define URLs for the files to download
MEDIAMTX_URL="https://github.com/bluenviron/mediamtx/releases/download/v1.12.2/mediamtx_v1.12.2_linux_arm64.tar.gz"
YML_URL="https://github.com/OpenGate-RB3/OpenGate-RB3/blob/main/board-configs/mediamtx.yml?raw=true"

# Define paths
DOWNLOAD_DIR="/tmp"
INSTALL_DIR="/usr/local/bin"
TAR_FILE="$DOWNLOAD_DIR/mediamtx_v1.12.2_linux_arm64.tar.gz"
YML_FILE="$DOWNLOAD_DIR/mediamtx.yml"
EXTRACT_DIR="$DOWNLOAD_DIR/mediamtx_v1.12.2_linux_arm64"

# Download mediamtx tar.gz file
echo "Downloading mediamtx tar file..."
wget $MEDIAMTX_URL -O $TAR_FILE

# Extract the tar file
echo "Extracting mediamtx tar file..."
tar -xzf $TAR_FILE -C $DOWNLOAD_DIR

# Move the 'mediamtx' binary into /usr/local/bin/
echo "Moving mediamtx binary to /usr/local/bin..."
mv "$EXTRACT_DIR/mediamtx" $INSTALL_DIR/

# Clean up extracted files
echo "Cleaning up..."
rm -rf $EXTRACT_DIR

# Download the mediamtx.yml file
echo "Downloading mediamtx.yml..."
wget $YML_URL -O $YML_FILE

# Move the mediamtx.yml file to /usr/local/bin/
echo "Moving mediamtx.yml to /usr/local/bin..."
mv $YML_FILE $INSTALL_DIR/

# Script complete
echo "Installation complete."
