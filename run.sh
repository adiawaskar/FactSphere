#!/bin/bash

# --- 1. Environment Setup (Mac/Linux) ---

# Check for and create/activate Python Virtual Environment (venv)
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating and installing dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Activating existing virtual environment..."
    source venv/bin/activate
fi

# --- 2. Configuration Check ---
if [ ! -f ".env" ]; then
    echo "WARNING: .env file is missing. Please create it before proceeding."
fi

# --- 3. Start Backend in a new iTerm/Terminal window ---
echo "Starting Backend in a new window..."

# This command uses osascript to open a new terminal window (Terminal or iTerm)
# and execute the backend startup commands inside it.
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'/backend\" && source ../venv/bin/activate && python direct_api.py"'

# --- 4. Start Frontend in a new iTerm/Terminal window ---
echo "Starting Frontend in a new window..."

osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'/frontend\" && npm install && npm run dev"'

echo "Frontend and Backend startup scripts sent to new windows."