#!/bin/bash

# Function to check and kill processes on specific ports
kill_process_on_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ -n "$pid" ]; then
        echo "Found process using port $port (PID: $pid). Terminating..."
        kill -9 $pid
        echo "Process on port $port terminated."
    else
        echo "No process found on port $port."
    fi
}

# Close any existing processes on the required ports
echo "Checking for existing processes on required ports..."
kill_process_on_port 8000  # API Auth service
kill_process_on_port 8001  # MCP service
kill_process_on_port 8080  # Frontend (Vite default)

# Wait a moment for processes to fully terminate
sleep 1

# Create log directory if it doesn't exist
mkdir -p logs

# Start services in separate terminals with output logging
# Run MCP service
echo "Starting MCP service..."
python run_mcp.py > logs/mcp.log 2>&1 &
MCP_PID=$!

# Run API Auth service
echo "Starting API Auth service..."
python run_api_auth.py > logs/api_auth.log 2>&1 &
API_AUTH_PID=$!

# Run Processing service with explicit path and error handling
echo "Starting Processing service..."
python run_processing.py > logs/processing.log 2>&1 &
PROCESSING_PID=$!

# Check if processing service started successfully
sleep 2
if ! ps -p $PROCESSING_PID > /dev/null; then
    echo "WARNING: Processing service failed to start. Check logs/processing.log for details."
    cat logs/processing.log
else
    echo "Processing service started with PID $PROCESSING_PID"
fi

# Run frontend
echo "Starting frontend..."
(cd freight-copilot && npm run dev > ../logs/frontend.log 2>&1) &
FRONTEND_PID=$!

# Run Telegram bot
echo "Starting Telegram bot..."
python telegram_integration/bot.py > logs/bot.log 2>&1 &
BOT_PID=$!

echo "All services are running!"
echo "MCP service: PID $MCP_PID (logs in logs/mcp.log)"
echo "API Auth service: PID $API_AUTH_PID (logs in logs/api_auth.log)"
echo "Processing service: PID $PROCESSING_PID (logs in logs/processing.log)"
echo "Frontend: PID $FRONTEND_PID (logs in logs/frontend.log)"
echo "Telegram bot: PID $BOT_PID (logs in logs/bot.log)"

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $MCP_PID $API_AUTH_PID $PROCESSING_PID $FRONTEND_PID $BOT_PID 2>/dev/null
    exit 0
}

# Register the cleanup function for SIGINT (Ctrl+C)
trap cleanup SIGINT

# Keep the script running and periodically check if services are still running
echo "Press Ctrl+C to stop all services"
while true; do
    # Check if any service has died
    for service_pid in $MCP_PID $API_AUTH_PID $PROCESSING_PID $FRONTEND_PID $BOT_PID; do
        if ! ps -p $service_pid > /dev/null; then
            service_name=""
            log_file=""
            if [ "$service_pid" = "$MCP_PID" ]; then
                service_name="MCP service"
                log_file="logs/mcp.log"
            elif [ "$service_pid" = "$API_AUTH_PID" ]; then
                service_name="API Auth service"
                log_file="logs/api_auth.log"
            elif [ "$service_pid" = "$PROCESSING_PID" ]; then
                service_name="Processing service"
                log_file="logs/processing.log"
            elif [ "$service_pid" = "$FRONTEND_PID" ]; then
                service_name="Frontend"
                log_file="logs/frontend.log"
            elif [ "$service_pid" = "$BOT_PID" ]; then
                service_name="Telegram bot"
                log_file="logs/bot.log"
            fi
            echo "WARNING: $service_name (PID $service_pid) has stopped. Check $log_file for details."
        fi
    done
    sleep 10
done