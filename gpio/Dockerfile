# Use a standard Python base image instead of Alpine for better OpenCV support
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for OpenCV and other packages
RUN apt-get update && apt-get install -y \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender-dev \
  libgomp1 \
  libglib2.0-0 \
  libgtk-3-0 \
  libavcodec-dev \
  libavformat-dev \
  libswscale-dev \
  libv4l-dev \
  libxvidcore-dev \
  libx264-dev \
  libjpeg-dev \
  libpng-dev \
  libtiff-dev \
  libatlas-base-dev \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy the Python script into the container's /app directory
COPY monitor_button.py .

# Install Python packages
RUN pip install --no-cache-dir \
  python-periphery \
  requests \
  opencv-python-headless \
  ultralytics \
  Pillow \
  numpy

# Command to run when the container starts
CMD ["python", "./monitor_button.py"]
