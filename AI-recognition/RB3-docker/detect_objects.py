from ultralytics import YOLO
from PIL import Image  # Pillow can be used for more advanced image checks if needed
import os


def main():
    image_filename = "dog.jpeg"  # This image is copied from your build context

    # Verify the image exists (it should, as it's copied by Dockerfile)
    if not os.path.exists(image_filename):
        print(
            f"Error: Image file '{image_filename}' not found in the app directory inside the container."
        )
        print("Please ensure it was correctly copied during the Docker build.")
        return

    print(f"Loading YOLOv8 model (e.g., yolov8n.pt for nano version)...")
    # Load a pretrained YOLOv8n model (nano version, small and fast).
    # The Ultralytics library will automatically download the model weights
    # the first time this line is executed if they are not already cached.
    # This requires an internet connection from within the container during that first run.
    try:
        model = YOLO(
            "yolov8n.pt"
        )  # You can specify other models like yolov8s.pt, yolov8m.pt, etc.
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        print(
            "If this is the first run, the container needs internet access to download model weights."
        )
        print("If the error persists, check compatibility or network issues.")
        return

    print(f"Performing object detection on '{image_filename}'...")
    try:
        # Perform inference
        results = model(image_filename)
    except Exception as e:
        print(f"Error during model inference: {e}")
        return

    # Process and display results
    if not results:
        print("No results returned from the model.")
        return

    detection_found = False
    for i, result in enumerate(
        results
    ):  # results can be a list if multiple images were passed
        print(f"\n--- Results for image {i+1} ---")
        if (
            hasattr(result, "boxes")
            and result.boxes is not None
            and len(result.boxes) > 0
        ):
            detection_found = True
            boxes = result.boxes  # Access the Boxes object

            print(f"Found {len(boxes)} objects:")
            for j, box in enumerate(boxes):
                class_id = int(box.cls)
                class_name = model.names[
                    class_id
                ]  # model.names is a dict like {0: 'person', 1: 'bicycle', ...}
                confidence = float(box.conf)
                # Bounding box coordinates in xyxy format (x_min, y_min, x_max, y_max)
                bbox_coords = box.xyxy[0].tolist()

                print(f"  Object {j+1}:")
                print(f"    Class: {class_name} (ID: {class_id})")
                print(f"    Confidence: {confidence:.4f}")
                print(
                    f"    Bounding Box (xyxy): [{bbox_coords[0]:.2f}, {bbox_coords[1]:.2f}, {bbox_coords[2]:.2f}, {bbox_coords[3]:.2f}]"
                )
        else:
            print("  No objects detected in this image.")

    if not detection_found:
        print("\nNo objects were detected in the processed image(s).")

    # If you want to save the image with detections drawn on it:
    # Make sure the container has write permissions to /app or specify a different path.
    # output_filename = "dog_detection_result.jpg"
    # print(f"\nSaving detection results to '{output_filename}'...")
    # results[0].save(filename=output_filename) # Saves the first image result
    # print(f"Result image saved. You can retrieve it from the container if needed.")


if __name__ == "__main__":
    main()
