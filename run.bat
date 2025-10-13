IF NOT EXIST venv (
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) ELSE (
    REM On Windows
    call venv\Scripts\activate
)

IF NOT EXIST .env (
    echo WARNING: .env file is missing. Please create it before proceeding.
)

REM Open a new terminal for backend
start cmd.exe /k "cd backend && python direct_api.py"

REM Open a new terminal for frontend
start cmd.exe /k "cd frontend && npm install && npm run dev"