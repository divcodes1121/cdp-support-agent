# Use Python 3.10 image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install Chrome and dependencies for Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libgconf-2-4 \
    libxi6 \
    libxss1 \
    libnss3 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional requirements for spaCy
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data/raw /app/data/processed

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Command to run
CMD ["python", "src/main.py", "serve"]