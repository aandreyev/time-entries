#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Create Virtual Environment ---
echo "Creating virtual environment..."
python3 -m venv venv

# --- Activate Virtual Environment ---
source venv/bin/activate
echo "Virtual environment activated."

# --- Install Dependencies ---
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo -e "\nSetup complete!"
echo "To run the application, make sure you are in the virtual environment."
echo "If your shell session ends, reactivate it with: source venv/bin/activate"
echo "Then run the script with: python main.py" 