import cv2
from flask import Flask, Response
from ultralytics import YOLO
import requests
import io
import json
import time
import face_recognition  # For facial recognition
import os  # For loading known faces
import numpy as np  # For face_distance

app = Flask(__name__)

# --- Configuration ---
NTFY_TOPIC = "open_gate_notif"
NTFY_ENABLE = False  # True to enable ntfy.sh, False to disable
WEBHOOK_URL = "http://localhost:5678/webhook/2aea4060-7603-4974-9a61-5584a137a895"  # Make sure this is your n8n webhook
YOLO_MODEL_PATH = "yolo11x.pt"  # Ensure this model exists
VIDEO_SOURCE = "rtsp://192.168.1.114:8554/videostream"
PERSON_CLASS_NAME = "person"
NOTIFICATION_COOLDOWN_SECONDS = 10  # Rate limit for notifications
NOTIF_VISION_ANNOTATED = (
    False  # False for raw frame in notification, True for annotated
)
KNOWN_FACES_DIR = "known_faces"  # Directory for known face images
FACE_RECOGNITION_TOLERANCE = 0.6  # Lower is stricter (0.4-0.6 typical)
ENABLE_FACE_RECOGNITION = True  # Master switch for face recognition feature
# --- End Configuration ---

# --- Global state variables for face recognition ---
known_face_encodings = []
known_face_names = []
# --- End Global state variables for face recognition ---

# --- Global state variables for notifications ---
notified_person_identities = (
    set()
)  # Stores (track_id, name_or_unknown_id) tuples for notified persons
last_notification_time = 0  # Timestamp of the last notification sent
# --- End Global state variables for notifications ---

try:
    model = YOLO(YOLO_MODEL_PATH)
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    exit()

try:
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        raise ValueError(f"Could not open video stream: {VIDEO_SOURCE}")
except Exception as e:
    print(f"Error opening video capture: {e}")
    exit()


def load_known_faces():
    global known_face_encodings, known_face_names
    print(f"Loading known faces from {KNOWN_FACES_DIR}...")
    if not os.path.exists(KNOWN_FACES_DIR):
        print(
            f"Warning: Known faces directory '{KNOWN_FACES_DIR}' not found. Face recognition will not identify known people."
        )
        return

    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(KNOWN_FACES_DIR, filename)
            name = os.path.splitext(filename)[0]
            try:
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(name)
                    print(f"  Loaded face for {name}")
                else:
                    print(f"  Warning: No face found in {filename}")
            except Exception as e:
                print(f"  Error loading face from {filename}: {e}")
    print(f"Known faces loaded: {len(known_face_names)} person(s).")


def send_ntfy_notification(message_payload):
    if not NTFY_ENABLE:
        print(f"Ntfy notifications are disabled. Message not sent: {message_payload}")
        return
    try:
        response = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message_payload.encode(encoding="utf-8"),
            headers={"Title": "Object Detection Alert"},
        )
        response.raise_for_status()
        print(f"Ntfy notification sent: {message_payload}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending ntfy notification: {e}")


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
        files_to_send["image_file"] = ("detection_image.jpg", image_bytes, "image/jpeg")

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


def gen_frames():
    global notified_person_identities, last_notification_time, cap, known_face_encodings, known_face_names

    while True:
        success, raw_frame = cap.read()
        if not success:
            print("Failed to grab frame from video stream. Attempting to reconnect...")
            cap.release()
            new_cap = cv2.VideoCapture(VIDEO_SOURCE)
            if new_cap.isOpened():
                cap = new_cap
                print("Successfully reconnected to video stream.")
                notified_person_identities.clear()  # Reset state on reconnect
                last_notification_time = 0
                continue
            else:
                print("Failed to reconnect to video stream. Breaking loop.")
                break

        frame_to_process_yolo = raw_frame.copy()
        yolo_results = model.track(frame_to_process_yolo, persist=True, verbose=False)

        # Start with YOLO's annotated frame for the stream. Face annotations will be added to this.
        final_annotated_frame_for_stream = yolo_results[0].plot()

        current_detected_object_names = set()  # All objects detected by YOLO
        persons_in_frame_details = (
            []
        )  # List of (track_id, recognized_name_str, yolo_bbox)

        if yolo_results[0].boxes is not None and yolo_results[0].boxes.id is not None:
            tracked_ids = yolo_results[0].boxes.id.int().cpu().tolist()
            yolo_bboxes = yolo_results[0].boxes.xyxy.cpu().numpy()
            class_indices = yolo_results[0].boxes.cls.int().cpu().tolist()
            class_names_map = yolo_results[0].names

            for i, track_id in enumerate(tracked_ids):
                cls_index = class_indices[i]
                class_name = class_names_map.get(cls_index, "unknown_object")
                current_detected_object_names.add(class_name)
                yolo_box = yolo_bboxes[i]

                if class_name == PERSON_CLASS_NAME:
                    recognized_name_for_track_id_str = (
                        f"PersonID_{track_id}"  # Default name
                    )

                    if (
                        ENABLE_FACE_RECOGNITION and known_face_encodings
                    ):  # Only if enabled and known faces exist
                        x1, y1, x2, y2 = map(int, yolo_box)
                        # Ensure crop dimensions are valid
                        if x1 < x2 and y1 < y2:
                            person_crop_rgb = cv2.cvtColor(
                                raw_frame[y1:y2, x1:x2], cv2.COLOR_BGR2RGB
                            )

                            # Find faces in the person crop
                            # Using model='hog' (default) for speed. 'cnn' is more accurate but much slower.
                            face_locations_in_crop = face_recognition.face_locations(
                                person_crop_rgb, model="hog"
                            )
                            face_encodings_in_crop = face_recognition.face_encodings(
                                person_crop_rgb, face_locations_in_crop
                            )

                            if (
                                face_encodings_in_crop
                            ):  # If any face is found in the crop
                                # For simplicity, using the first detected face in the crop
                                current_face_encoding = face_encodings_in_crop[0]
                                current_face_location_in_crop = face_locations_in_crop[
                                    0
                                ]

                                matches = face_recognition.compare_faces(
                                    known_face_encodings,
                                    current_face_encoding,
                                    tolerance=FACE_RECOGNITION_TOLERANCE,
                                )
                                face_distances = face_recognition.face_distance(
                                    known_face_encodings, current_face_encoding
                                )

                                best_match_index = np.argmin(face_distances)
                                if matches[best_match_index]:
                                    recognized_name_for_track_id_str = known_face_names[
                                        best_match_index
                                    ]
                                    print(
                                        f"  Recognized: {recognized_name_for_track_id_str} (Track ID: {track_id})"
                                    )

                                # Annotate face on the stream frame
                                top_f, right_f, bottom_f, left_f = (
                                    current_face_location_in_crop
                                )
                                # Adjust coordinates from crop to full raw_frame
                                top_f += y1
                                right_f += x1
                                bottom_f += y1
                                left_f += x1
                                cv2.rectangle(
                                    final_annotated_frame_for_stream,
                                    (left_f, top_f),
                                    (right_f, bottom_f),
                                    (0, 0, 255),
                                    1,
                                )  # Red box for face
                                cv2.putText(
                                    final_annotated_frame_for_stream,
                                    recognized_name_for_track_id_str,
                                    (left_f + 3, top_f - 6),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    (255, 0, 0),
                                    1,
                                    cv2.LINE_AA,
                                )

                    persons_in_frame_details.append(
                        (track_id, recognized_name_for_track_id_str, yolo_box)
                    )

        # --- Notification Logic ---
        newly_identified_for_notification_flag = False
        identities_for_current_notification_payload = (
            set()
        )  # Names/IDs for this notification burst

        for track_id, name, _ in persons_in_frame_details:
            identity_key = (
                track_id,
                name,
            )  # (e.g., (123, "Alice") or (124, "PersonID_124"))
            if identity_key not in notified_person_identities:
                newly_identified_for_notification_flag = True
                identities_for_current_notification_payload.add(name)

        current_time = time.time()
        if newly_identified_for_notification_flag and (
            current_time - last_notification_time > NOTIFICATION_COOLDOWN_SECONDS
        ):
            print(
                f"New person identities for notification: {identities_for_current_notification_payload}. Cooldown passed."
            )

            all_yolo_detected_items_str_list = sorted(
                list(current_detected_object_names)
            )
            recognized_persons_str_list = sorted(
                list(identities_for_current_notification_payload)
            )

            ntfy_message = f"ALERT: Detection! Objects: [{', '.join(all_yolo_detected_items_str_list)}]."
            if recognized_persons_str_list:
                ntfy_message += (
                    f" Identified: [{', '.join(recognized_persons_str_list)}]."
                )

            send_ntfy_notification(ntfy_message)

            image_for_notification_bytes = None
            # Use raw_frame or annotated_frame based on config for the notification image
            frame_to_send_in_notification = (
                raw_frame
                if not NOTIF_VISION_ANNOTATED
                else final_annotated_frame_for_stream
            )

            try:
                is_success_encode, buffer_encode = cv2.imencode(
                    ".jpg", frame_to_send_in_notification
                )
                if is_success_encode:
                    image_for_notification_bytes = io.BytesIO(buffer_encode).getvalue()
                else:
                    print("Warning: Failed to encode frame for notification webhook.")
            except Exception as e:
                print(f"Error encoding frame for notification webhook: {e}")

            if image_for_notification_bytes:
                send_webhook_request(
                    all_yolo_detected_items_str_list,
                    image_for_notification_bytes,
                    recognized_names_set=identities_for_current_notification_payload,
                )

            # Update notified_person_identities with those processed in this notification burst
            for track_id, name, _ in persons_in_frame_details:
                if name in identities_for_current_notification_payload:
                    notified_person_identities.add((track_id, name))
            last_notification_time = current_time

        elif newly_identified_for_notification_flag:
            print(
                f"New person identities identified, but notification cooldown active: {identities_for_current_notification_payload}"
            )

        # Video stream output (always fully annotated)
        try:
            _, stream_buffer = cv2.imencode(".jpg", final_annotated_frame_for_stream)
            if stream_buffer is None:
                print(
                    "Warning: cv2.imencode returned None for an annotated frame (stream)."
                )
                continue
            frame_bytes_for_stream = stream_buffer.tobytes()
        except Exception as e:
            print(f"Error encoding frame for stream: {e}")
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes_for_stream + b"\r\n"
        )


@app.route("/detection")
def detection_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    load_known_faces()  # Load known faces at startup

    print(f"Flask app running. Open your browser to http://0.0.0.0:9000/detection")
    if NTFY_ENABLE:
        print(f"Ntfy notifications WILL BE SENT to https://ntfy.sh/{NTFY_TOPIC}")
    else:
        print(f"Ntfy notifications ARE DISABLED.")
    print(
        f"Webhook (Telegram) notifications vision annotated: {NOTIF_VISION_ANNOTATED}"
    )
    print(f"Face Recognition Enabled: {ENABLE_FACE_RECOGNITION}")
    if ENABLE_FACE_RECOGNITION:
        print(f"Face Recognition Tolerance: {FACE_RECOGNITION_TOLERANCE}")
        print(f"Known Faces Directory: '{KNOWN_FACES_DIR}/'")
    print(f"Notification cooldown: {NOTIFICATION_COOLDOWN_SECONDS} seconds.")
    print(f"Webhook POST requests will be sent to {WEBHOOK_URL}")
    app.run(host="0.0.0.0", port=9000, debug=False)
