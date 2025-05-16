#!/bin/bash

# Define URLs for the files to download
MEDIAMTX_URL="https://github.com/bluenviron/mediamtx/releases/download/v1.12.2/mediamtx_v1.12.2_linux_arm64.tar.gz"
YML_URL="https://github.com/OpenGate-RB3/OpenGate-RB3/blob/main/board-configs/mediamtx.yml?raw=true"
START_AUDIO_URL="https://raw.githubusercontent.com/OpenGate-RB3/OpenGate-RB3/refs/heads/main/board-configs/start_audio.bash"
START_VIDEO_URL="https://raw.githubusercontent.com/OpenGate-RB3/OpenGate-RB3/refs/heads/main/board-configs/start_video.bash"

# Define paths
DOWNLOAD_DIR="/tmp"
INSTALL_DIR="/usr/local/bin"
TAR_FILE="$DOWNLOAD_DIR/mediamtx_v1.12.2_linux_arm64.tar.gz"
YML_FILE="$DOWNLOAD_DIR/mediamtx.yml"
START_AUDIO_FILE="$DOWNLOAD_DIR/start_audio.bash"
START_VIDEO_FILE="$DOWNLOAD_DIR/start_video.bash"
EXTRACT_DIR="$DOWNLOAD_DIR"

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
rm $DOWNLOAD_DIR/LICENSE $DOWNLOAD_DIR/mediamtx_v1.12.2_linux_arm64.tar.gz

# Download the mediamtx.yml file
echo "Downloading mediamtx.yml..."
wget $YML_URL -O $YML_FILE

# Download the start_audio.bash file
echo "Downloading start_audio.bash..."
wget $START_AUDIO_URL -O $START_AUDIO_FILE

# Download the start_video.bash file
echo "Downloading start_video.bash..."
wget $START_VIDEO_URL -O $START_VIDEO_FILE

# Get the IP address of the system
ipaddr=$(hostname -i | awk '{print $1}')

# Use sed to replace ${IPHOSTNAME} with the system's IP address in all the downloaded files
echo "Replacing IPHOSTNAME in files..."

sed -i "s|\${IPHOSTNAME}|$ipaddr|g" $YML_FILE
sed -i "s|\${IPHOSTNAME}|$ipaddr|g" $START_AUDIO_FILE
sed -i "s|\${IPHOSTNAME}|$ipaddr|g" $START_VIDEO_FILE

# Move the files to /usr/local/bin/
echo "Moving files to /usr/local/etc..."
mv $YML_FILE /usr/local/etc/
echo "Moving files to /usr/local/bin..."
mv $START_AUDIO_FILE $INSTALL_DIR/
mv $START_VIDEO_FILE $INSTALL_DIR/

chmod +x /usr/local/bin/*.bash

# Script complete
echo "Installation complete."
