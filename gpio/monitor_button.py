import time
import os
import requests
import json
import cv2
import numpy as np
from periphery import GPIO
from ultralytics import YOLO
import io
from PIL import Image

# --- Configuration ---
GPIO_CHIP_DEVICE_ENV = os.environ.get("GPIO_CHIP_DEVICE", "/dev/gpiochip4")
GPIO_LINE_OFFSET_ENV = int(os.environ.get("GPIO_LINE_OFFSET", "36"))

# Video source configuration - default to RTSP
VIDEO_SOURCE = os.environ.get("VIDEO_SOURCE", "rtsp://192.168.1.114:8554/videostream")

# Webhook configuration
WEBHOOK_URL = "https://dolboeb.us/webhook/2aea4060-7603-4974-9a61-5584a137a895"

# Notification configuration
NTFY_TOPIC = "open_gate_notif"
NTFY_MESSAGE = "Button pressed 😀"
NO_HIGH_TIMEOUT = 2.0  # Seconds without detecting HIGH to consider button pressed


def send_webhook_request(
    detected_items_list, image_bytes=None, recognized_names_set=None
):
    payload_data = {
        "detected_items_json": json.dumps(detected_items_list),
        "recognized_persons_json": (
            json.dumps(list(recognized_names_set))
            if recognized_names_set
            else json.dumps([])
        ),
    }
    files_to_send = {}
    if image_bytes:
        files_to_send["image_file"] = (
            "detection_image.jpg",
            image_bytes,
            "image/jpeg",
        )

    try:
        if files_to_send:
            response = requests.post(
                WEBHOOK_URL, data=payload_data, files=files_to_send
            )
        else:
            response = requests.post(WEBHOOK_URL, data=payload_data)
        response.raise_for_status()
        print(f"Webhook POST request sent successfully to {WEBHOOK_URL}.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending webhook POST request: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response content: {e.response.content}")
    except Exception as e:
        print(f"An unexpected error occurred while sending webhook POST request: {e}")


def process_frame_and_detect(frame, model):
    """Process a frame and run object detection"""
    try:
        if frame is None:
            print("No frame available for processing")
            return [], None

        # Run YOLO detection
        results = model(frame, verbose=False)

        # Extract detection information
        detected_items = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = model.names[cls_id]

                    detected_items.append(
                        {
                            "class": class_name,
                            "confidence": confidence,
                            "class_id": cls_id,
                        }
                    )

        # Draw bounding boxes on the frame for the webhook image
        annotated_frame = results[0].plot() if results else frame

        # Convert to PIL Image and then to bytes
        pil_image = Image.fromarray(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format="JPEG", quality=85)
        image_bytes = img_buffer.getvalue()

        return detected_items, image_bytes

    except Exception as e:
        print(f"Error during frame processing and detection: {e}")
        return [], None


def send_ntfy_notification():
    """Send notification to ntfy"""
    try:
        response = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=NTFY_MESSAGE.encode(encoding="utf-8"),
            headers={"Title": "Gate Button Alert"},
        )
        if response.status_code == 200:
            print("Notification sent successfully.")
        else:
            print(
                f"Failed to send ntfy. Status: {response.status_code}, "
                f"Resp: {response.text}"
            )
    except requests.exceptions.RequestException as e:
        print(f"Error sending ntfy notification: {e}")


print(
    f"--- GPIO Monitor with Video Detection - 'No HIGH for {NO_HIGH_TIMEOUT}s' "
    f"Logic (in Docker) ---"
)
print(f"Using Chip: {GPIO_CHIP_DEVICE_ENV}, Line: {GPIO_LINE_OFFSET_ENV}")
print(f"Video Source: {VIDEO_SOURCE}")
print(f"Notification will be sent to: https://ntfy.sh/{NTFY_TOPIC}")
print(f"Webhook URL: {WEBHOOK_URL}")
print("Press Ctrl+C to exit.")

# Initialize video capture
cap = None
model = None
gpio_in = None
latest_frame = None

try:
    # Initialize video capture
    print("Initializing RTSP video capture...")
    cap = cv2.VideoCapture(VIDEO_SOURCE)

    # Configure for RTSP streaming
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer to reduce latency
    cap.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS

    if not cap.isOpened():
        print(f"Error: Could not open video source {VIDEO_SOURCE}")
        raise Exception("Video capture initialization failed")

    print("Video capture initialized successfully.")

    # Initialize YOLO model (smallest version)
    print("Loading YOLO model...")
    model = YOLO("yolov8n.pt")  # This will download the model if not present
    print("YOLO model loaded successfully.")

    # Initialize GPIO
    gpio_in = GPIO(GPIO_CHIP_DEVICE_ENV, GPIO_LINE_OFFSET_ENV, "in")
    initial_state_is_high = gpio_in.read()
    print(
        f"Successfully opened {GPIO_CHIP_DEVICE_ENV} line {GPIO_LINE_OFFSET_ENV}. "
        f"Initial raw state: {'HIGH' if initial_state_is_high else 'LOW'}"
    )

    # Initialize timing variables
    last_high_seen_time = time.monotonic()
    notification_sent_this_cycle = False

    if initial_state_is_high:
        last_high_seen_time = time.monotonic()
    else:
        last_high_seen_time = time.monotonic()

    print("Starting main loop - continuously reading frames...")

    while True:
        # Continuously read frames from the stream
        ret, frame = cap.read()
        if ret:
            latest_frame = frame
        else:
            print("Warning: Failed to read frame from stream")
            # Try to reconnect if we lose the stream
            time.sleep(1)
            continue

        # Check GPIO state
        current_pin_is_high = gpio_in.read()
        current_time = time.monotonic()

        if current_pin_is_high:
            last_high_seen_time = current_time
            if notification_sent_this_cycle:
                print("Pin went HIGH, re-arming notification.")
                notification_sent_this_cycle = False
        else:  # Pin is currently LOW
            if not notification_sent_this_cycle:
                time_since_last_high = current_time - last_high_seen_time
                if time_since_last_high >= NO_HIGH_TIMEOUT:
                    print(f"Button pressed. Processing latest frame...")

                    # Send ntfy notification
                    send_ntfy_notification()

                    # Process the latest frame and run detection
                    if latest_frame is not None:
                        print("Running object detection on latest frame...")
                        detected_items, image_bytes = process_frame_and_detect(
                            latest_frame, model
                        )

                        if detected_items:
                            print(f"Detected {len(detected_items)} objects:")
                            for item in detected_items:
                                print(
                                    f"  - {item['class']} "
                                    f"(confidence: {item['confidence']:.2f})"
                                )
                        else:
                            print("No objects detected.")

                        # Send webhook request
                        print("Sending webhook request...")
                        send_webhook_request(detected_items, image_bytes)
                    else:
                        print("No frame available for processing")

                    notification_sent_this_cycle = True

        # Small sleep to prevent excessive CPU usage while still maintaining responsiveness
        time.sleep(0.033)  # ~30 FPS frame reading rate

except Exception as e:
    print(f"\nError: {e}")
except KeyboardInterrupt:
    print("\nExiting script...")
finally:
    if cap:
        cap.release()
        print("Video capture released.")
    if gpio_in:
        gpio_in.close()
        print("GPIO closed.")
