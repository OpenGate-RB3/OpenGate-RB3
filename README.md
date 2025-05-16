# OpenGate-RB3

## SETUP

1. Setup your Qualcomm RB3 vision board according to the [setup guide](https://docs.qualcomm.com/bundle/publicresource/topics/80-70017-253/getting_started.html)
2. Update the board to the latest version of Qualcomm Linux (tested for 1.4), according to [update guide](https://docs.qualcomm.com/bundle/publicresource/topics/80-70018-253/upgrade-rb3gen2-software.html)
3. Get the INSTALL script onto the board
   `wget https://raw.githubusercontent.com/OpenGate-RB3/OpenGate-RB3/refs/heads/main/INSTALL.bash`

4. Run the INSTALL script
   `./INSTALL.bash`

INSTALL script downloads and unpacks correct version of mediamtx multiplexer onto the board, as well as required scripts from this repository. Then puts files in correct paths, finds out your device IP, and updates the config files automatically.

## STREAMING VIDEO AND AUDIO FROM THE BOARD

To start all the streams, download the RUN.bash script onto the board with `wget <RAW LINK HERE>` and run it with `./RUN.bash`

If you want to start an individual stream, here are commands you can use:

1. 30 FPS Camera Stream: `something`
2. 5 FPS Camera Stream (for AI): `something`
3. Audio stream: `gst-launch-1.0 -v pulsesrc volume=2.0 ! audioconvert ! audioresample ! lamemp3enc bitrate=128 cbr=true ! mpegaudioparse ! mpegtsmux ! udpsink host=${IPHOSTNAME} port=5005`

## STREAMING AUDIO TO BOARD SPEAKERS

## YOLO OBJECT DETECTION

## FACE RECOGNITION

## N8N AUTOMATIONS
