# Base image: Python 3.9 on a slim Debian distribution
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
# - libgl1-mesa-glx, libglib2.0-0: Often needed for OpenCV (even headless) and image processing libraries
# - libgomp1: For OpenMP, which PyTorch can use for parallelization on CPU
RUN apt-get update && apt-get install -y \
  libgl1-mesa-glx \
  libglib2.0-0 \
  libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# Install Python libraries using pip
# ultralytics: The official YOLOv8 package, it will pull in PyTorch and other dependencies.
# opencv-python-headless: For OpenCV functionalities without GUI requirements (often a dependency).
# Pillow: A general-purpose image manipulation library.
RUN pip install --no-cache-dir ultralytics opencv-python-headless Pillow

# Copy your Python script and the dog image into the /app directory in the container
COPY detect_objects.py .
COPY dog.jpeg .
# IMPORTANT: Ensure 'dog.jpeg' is present in the same directory as this Dockerfile
# when you run 'docker build'.

# Command to execute your Python script when the container starts
CMD ["python", "./detect_objects.py"]
