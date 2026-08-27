#!/bin/bash

# AdVisualizer Setup and Run Script

# 1. Environment Configuration
echo "Checking environment setup..."
if [ -f "set_env.sh" ]; then
    echo "Sourcing set_env.sh..."
    source set_env.sh
else
    echo "Error: set_env.sh not found. Please ensure it exists with required environment variables."
    exit 1
fi

# 2. Dependency Installation
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found."
    exit 1
fi

# 3. Running the Application
echo "Starting the application..."
if [ -f "app.py" ]; then
    python app.py
else
    echo "Error: app.py not found."
    exit 1
fi
