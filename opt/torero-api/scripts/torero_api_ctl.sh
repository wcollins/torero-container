#!/bin/bash
#
# torero_api_ctl.sh - Control script for torero-api daemon
#
# Usage: torero_api_ctl.sh {start|stop|restart|status|logs}
#

# Default configuration
DEFAULT_PID_FILE="/tmp/torero-api.pid"
DEFAULT_LOG_FILE="/tmp/torero-api.log"
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"

# Allow overriding via environment variables
PID_FILE="${TORERO_API_PID_FILE:-$DEFAULT_PID_FILE}"
LOG_FILE="${TORERO_API_LOG_FILE:-$DEFAULT_LOG_FILE}"
HOST="${TORERO_API_HOST:-$DEFAULT_HOST}"
PORT="${TORERO_API_PORT:-$DEFAULT_PORT}"

# Add cool colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Get PID from file
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE" 2>/dev/null
    fi
}

# Check if process is running
is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "$pid"
        return 0
    else
        return 1
    fi
}

# Start daemon
start_daemon() {
    local pid=$(is_running)
    if [ $? -eq 0 ]; then
        print_status $YELLOW "torero-api is already running (PID: $pid)"
        return 1
    fi
    
    print_status $BLUE "Starting torero-api daemon..."
    print_status $BLUE "Host: $HOST"
    print_status $BLUE "Port: $PORT"
    print_status $BLUE "PID file: $PID_FILE"
    print_status $BLUE "Log file: $LOG_FILE"
    
    torero-api --daemon \
        --host "$HOST" \
        --port "$PORT" \
        --pid-file "$PID_FILE" \
        --log-file "$LOG_FILE"
    
    sleep 2
    local pid=$(is_running)
    if [ $? -eq 0 ]; then
        print_status $GREEN "torero-api started successfully (PID: $pid)"
        print_status $GREEN "API available at: http://$HOST:$PORT"
        return 0
    else
        print_status $RED "Failed to start torero-api"
        if [ -f "$LOG_FILE" ]; then
            print_status $RED "Check log file: $LOG_FILE"
            echo "Last 10 lines of log:"
            tail -n 10 "$LOG_FILE"
        fi
        return 1
    fi
}

# Stop daemon
stop_daemon() {
    local pid=$(is_running)
    if [ $? -ne 0 ]; then
        print_status $YELLOW "torero-api is not running"
        # Clean up stale PID file
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        return 1
    fi
    
    print_status $BLUE "Stopping torero-api daemon (PID: $pid)..."
    
    # Send SIGTERM
    kill -TERM "$pid" 2>/dev/null
    
    # Graceful shutdown
    local count=0
    while [ $count -lt 30 ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            print_status $GREEN "torero-api stopped successfully"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    print_status $YELLOW "Graceful shutdown failed, forcing termination..."
    kill -KILL "$pid" 2>/dev/null
    sleep 2
    
    if ! kill -0 "$pid" 2>/dev/null; then
        print_status $GREEN "torero-api terminated"
        rm -f "$PID_FILE"
        return 0
    else
        print_status $RED "Failed to stop torero-api"
        return 1
    fi
}

# Restart daemon
restart_daemon() {
    print_status $BLUE "Restarting torero-api daemon..."
    stop_daemon
    sleep 2
    start_daemon
}

# Daemon status
show_status() {
    local pid=$(is_running)
    if [ $? -eq 0 ]; then
        print_status $GREEN "torero-api is running (PID: $pid)"
        
        # Try to check API health
        if command -v curl >/dev/null 2>&1; then
            print_status $BLUE "Checking API health..."
            local health_response=$(curl -s "http://$HOST:$PORT/health" 2>/dev/null)
            if [ $? -eq 0 ]; then
                echo "API Health Response:"
                echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
            else
                print_status $YELLOW "API health check failed - service may be starting up"
            fi
        fi
        
        return 0
    else
        print_status $RED "torero-api is not running"

        # Check for stale PID file
        if [ -f "$PID_FILE" ]; then
            print_status $YELLOW "Stale PID file found: $PID_FILE"
        fi
        return 1
    fi
}

# Show logs
show_logs() {
    local lines=${1:-50}
    local follow=${2:-false}
    
    if [ ! -f "$LOG_FILE" ]; then
        print_status $RED "Log file not found: $LOG_FILE"
        return 1
    fi
    
    print_status $BLUE "Showing logs from: $LOG_FILE"
    echo "----------------------------------------"
    
    if [ "$follow" = "true" ]; then
        tail -f -n "$lines" "$LOG_FILE"
    else
        tail -n "$lines" "$LOG_FILE"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|follow-logs}"
    echo ""
    echo "Commands:"
    echo "  start       Start the torero-api daemon"
    echo "  stop        Stop the torero-api daemon"
    echo "  restart     Restart the torero-api daemon"
    echo "  status      Show daemon status"
    echo "  logs        Show recent log entries"
    echo "  follow-logs Follow log entries (like tail -f)"
    echo ""
    echo "Environment Variables:"
    echo "  TORERO_API_HOST      API host (default: $DEFAULT_HOST)"
    echo "  TORERO_API_PORT      API port (default: $DEFAULT_PORT)"
    echo "  TORERO_API_PID_FILE  PID file path (default: $DEFAULT_PID_FILE)"
    echo "  TORERO_API_LOG_FILE  Log file path (default: $DEFAULT_LOG_FILE)"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start daemon with defaults"
    echo "  TORERO_API_PORT=8080 $0 start  # Start on port 8080"
    echo "  $0 logs                     # Show last 50 log lines"
    echo "  $0 follow-logs              # Follow logs in real-time"
}

# Main logic
case "$1" in
    start)
        start_daemon
        exit $?
        ;;
    stop)
        stop_daemon
        exit $?
        ;;
    restart)
        restart_daemon
        exit $?
        ;;
    status)
        show_status
        exit $?
        ;;
    logs)
        show_logs 50 false
        exit $?
        ;;
    follow-logs)
        show_logs 50 true
        exit $?
        ;;
    *)
        show_usage
        exit 1
        ;;
esac