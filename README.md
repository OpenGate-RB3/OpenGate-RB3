# OpenGate-RB3

## SETUP

1. Setup your Qualcomm RB3 vision board according to the [setup guide](https://docs.qualcomm.com/bundle/publicresource/topics/80-70017-253/getting_started.html)
2. Update the board to the latest version of Qualcomm Linux (tested for 1.4), according to [update guide](https://docs.qualcomm.com/bundle/publicresource/topics/80-70018-253/upgrade-rb3gen2-software.html)
3. Get the INSTALL script onto the board
   `wget https://raw.githubusercontent.com/OpenGate-RB3/OpenGate-RB3/refs/heads/main/INSTALL.bash`

4. Run the INSTALL script
   `./INSTALL.bash`

INSTALL script downloads and unpacks correct version of mediamtx multiplexer onto the board, as well as required scripts from this repository. Then puts files in correct paths, finds out your device IP, and updates the config files automatically.

If at some point you need to figure out active RB3 ip addr, use `hostname -i | awk '{print $1}'`

## STREAMING VIDEO AND AUDIO FROM THE BOARD

To start all the streams, download the RUN.bash script onto the board with `wget <RAW LINK HERE>` and run it with `./RUN.bash`

If you want to start an individual stream, here are commands you can use:

1. 30 FPS Camera Stream: `something`
2. 5 FPS Camera Stream (for AI): `something`
3. Audio stream: `gst-launch-1.0 -v pulsesrc volume=2.0 ! audioconvert ! audioresample ! lamemp3enc bitrate=128 cbr=true ! mpegaudioparse ! mpegtsmux ! udpsink host=${IPHOSTNAME} port=5005`

To see the 30FPS stream, use the link `http://<RB3 IP>:8888/videostream/`

To get the 5FPS stream, use `http://<RB3 IP>:8888/imagestream/`

To listen to audio stream on another device, `ffplay rtsp://<RB3 IP>:8554/audiostream` (also displays a spectrogram)

## STREAMING AUDIO TO BOARD SPEAKERS

To send an audio file to the board, you can use ffmpeg (replace RB3 IP addr):
`ffmpeg -re -i input.mp3 -acodec libmp3lame -ab 128k -ac 2 -f mpegts -pkt_size 188 udp://<RB3 IP>:9000`

To send an audio stream from any source on your host device to the board, use a slightly altered command:

```bash
ffmpeg -f pulse -i <AUDIO SOURCE ON HOST> \
  -acodec libmp3lame -b:a 128k -ac 2 \
  -f mpegts -mpegts_flags +system_b \
  -pkt_size 188 \
  udp://<RB3 IP>:9000
```

You can find audio sources on host with `pactl list short sources`, should look something like `alsa_output.usb-Blue_Microphones_Yeti_X_2229SG000DA8_888-000313110306-00.analog-stereo.monitor`

With correct setup, it should play audio live without delay, in good quality.

## YOLO OBJECT DETECTION

1. Clone the repo,
2. cd into AI-recognition,
3. install dependencies with `pip install -r requirements.txt`,
4. download YOLO pt file from YOLO website of appropriate model size,
5. run `python yolo7-face.py`

## FACE RECOGNITION

To add face recognition, add pictures of faces of people you want to be recognized into `AI-recognition/known_faces` directory. Each file should be named with how you want the person object to be named when recognized. png and jpeg are valid formats for the pictures.

## N8N AUTOMATIONS
