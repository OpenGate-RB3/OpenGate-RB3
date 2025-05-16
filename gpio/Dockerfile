# Use a lightweight Python base image compatible with ARM64 (which RB3 Gen2 is)
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the Python script into the container's /app directory
COPY monitor_button.py .

# Install python-periphery and requests
RUN pip install python-periphery requests

# Command to run when the container starts
CMD ["python", "./monitor_button.py"]
