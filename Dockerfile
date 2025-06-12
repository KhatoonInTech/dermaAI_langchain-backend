FROM python:3.11-slim

# Install system dependencies for PDF processing and image handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        build-essential \
        python3-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set PORT environment variable for GCloud Run
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Start command (write JSON string from env var to file, then run app)
CMD sh -c "uvicorn app:app --host 0.0.0.0 --port $PORT"
