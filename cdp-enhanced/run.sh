#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Run scraper if no data exists
if [ ! "$(ls -A data)" ]; then
    echo "No data found. Running scraper..."
    python scraper.py
fi

# Run indexer if no index exists
if [ ! -d "data/index" ]; then
    echo "No index found. Running indexer..."
    python indexer.py
fi

# Run the application
echo "Starting application..."
python app.py
