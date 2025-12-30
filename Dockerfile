FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for compilation of some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose ports (ADK=8001, WhatsApp=8000)
# Cloud Run only routes traffic to the port defined in PORT env var (default 8080)
# But our app hardcodes 8000. We will map Cloud Run PORT to 8000 in deployment command 
# or change app to listen on $PORT. 
# SIMPLER: Let's explicitly expose 8000 and tell Cloud Run to listen there.
EXPOSE 8000

# Run entrypoint script
CMD ["./entrypoint.sh"]
