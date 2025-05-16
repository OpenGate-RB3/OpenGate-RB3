echo "Starting audio stream"
gst-launch-1.0 -v pulsesrc volume=2.0 ! audioconvert ! audioresample ! lamemp3enc bitrate=128 cbr=true ! mpegaudioparse ! mpegtsmux ! udpsink host=${IPHOSTNAME} port=5005
