echo "Starting video pipeline"

gst-launch-1.0 -e \
	qtiqmmfsrc name=qmmf ! video/x-raw,format=NV12,width=1920,height=1080,framerate=30/1 ! \
	tee name=t ! \
	queue ! v4l2h264enc ! mpegtsmux ! udpsink host=${IPHOSTNAME} port=5004 \
	t. ! \
	queue ! videorate ! video/x-raw,framerate=5/1 ! \
	capsfilter caps=video/x-raw,framerate=5/1 ! v4l2h264enc ! mpegtsmux ! udpsink host=${IPHOSTNAME} port=5006
