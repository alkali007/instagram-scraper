# Use Python 3.12 slim (lightweight)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Chrome needs these)
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip sudo procps \
    && rm -rf /var/lib/apt/lists/*

# Copy the installer scripts
COPY etc/ /app/etc/

# Make Chrome installer executable
RUN chmod +x /app/etc/install_chrome.sh

# Install Chrome
RUN /app/etc/install_chrome.sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chromedriver (your step 3)
RUN python3 /app/etc/install_driver.py

# Copy app source code
COPY src/ /app/src/
COPY config/ /app/config/
COPY data/ /app/data/
COPY ss/ /app/ss/

# Default command (can be overridden)
ENTRYPOINT ["python3", "-m", "src.main"]
