@echo off
REM TrueSender - starts both services for local demo/presentation.
REM Run this from the project root: start-all.bat

echo === Starting TrueSender (Python ML service + Java backend) ===

echo Starting Python ML service on port 8000...
cd ml-service
start cmd /k "venv\Scripts\activate.bat && uvicorn main:app --port 8000"
cd ..

echo Waiting for Python service to start...
timeout /t 5 /nobreak

echo Starting Java backend on port 8080...
cd backend
mvn spring-boot:run
