# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose port (Cloud Run sets this as an environment variable)
EXPOSE 8000

# Entrypoint for migrations and static files
ENTRYPOINT ["/app/entrypoint.sh"]
