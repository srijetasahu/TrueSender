#!/bin/bash
# TrueSender - starts both services for local demo/presentation.
# Run this from the project root: ./start-all.sh

echo "=== Starting TrueSender (Python ML service + Java backend) ==="

# 1. Start Python ML service in the background
echo "Starting Python ML service on port 8000..."
cd ml-service
source venv/bin/activate 2>/dev/null || echo "(no venv found, using system python)"
uvicorn main:app --port 8000 &
ML_PID=$!
cd ..

# Give Python a few seconds to start up and load the model
sleep 3

# 2. Start Java Spring Boot backend in the foreground
echo "Starting Java backend on port 8080..."
cd backend
mvn spring-boot:run

# When Java is stopped (Ctrl+C), also stop the Python service
kill $ML_PID
