# Dockerfile for Enhanced Trading Bot (Pro Signal Logic v2)
# Version: 2.0
# This version includes price action, candlestick, and indicator confirmation logic

FROM python:3.12-slim

LABEL bot.version="2.0"
LABEL bot.description="Enhanced with Pro Signal Logic (v2): Price Action + Indicator Confirmation"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory with proper permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m -u 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('https://api.telegram.org')" || exit 1

# Command to run the application
CMD ["python", "main.py"]