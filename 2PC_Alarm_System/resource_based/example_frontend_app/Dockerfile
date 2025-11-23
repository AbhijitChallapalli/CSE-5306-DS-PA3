# Use an official Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY flask/ .

# Command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=8081"]
