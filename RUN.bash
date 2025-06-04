#!/bin/bash

# start mediamtx server
nohup mediamtx >/dev/null 2>&1 &
MEDIAMTX_PID=$!

# Start the video and audio scripts in the background
nohup start_video.bash >/dev/null 2>&1 &
VIDEO_PID=$!

nohup start_audio.bash >/dev/null 2>&1 &
AUDIO_PID=$!



# Trap SIGINT (Ctrl-C) to kill the background processes
trap "kill $VIDEO_PID $AUDIO_PID $MEDIAMTX_PID" SIGINT

# Wait for the background processes to finish
wait $VIDEO_PID
wait $AUDIO_PID
wait $MEDIAMTX_PID
