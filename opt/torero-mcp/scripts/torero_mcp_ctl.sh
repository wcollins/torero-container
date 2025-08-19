#!/bin/bash
# torero-mcp daemon control script
set -e

# Default config
TORERO_MCP_HOST=${TORERO_MCP_HOST:-"127.0.0.1"}
TORERO_MCP_PORT=${TORERO_MCP_PORT:-"8080"}
TORERO_MCP_PID_FILE=${TORERO_MCP_PID_FILE:-"/tmp/torero-mcp.pid"}
TORERO_MCP_LOG_FILE=${TORERO_MCP_LOG_FILE:-"/tmp/torero-mcp.log"}
TORERO_MCP_CONFIG=${TORERO_MCP_CONFIG:-""}

# Script directory and torero-mcp binary
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Try to find torero-mcp binary
if command -v torero-mcp >/dev/null 2>&1; then
    TORERO_MCP_BIN="torero-mcp"
elif [ -f "$PROJECT_DIR/.venv/bin/torero-mcp" ]; then
    TORERO_MCP_BIN="$PROJECT_DIR/.venv/bin/torero-mcp"
elif [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    TORERO_MCP_BIN="$PROJECT_DIR/.venv/bin/python -m torero_mcp.cli"
else
    TORERO_MCP_BIN="python -m torero_mcp.cli"
fi

usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|follow-logs}"
    echo ""
    echo "Commands:"
    echo "  start        Start the torero-mcp daemon"
    echo "  stop         Stop the torero-mcp daemon"
    echo "  restart      Restart the torero-mcp daemon"
    echo "  status       Check daemon status"
    echo "  logs         View daemon logs"
    echo "  follow-logs  Follow daemon logs in real-time"
    echo ""
    echo "Environment Variables:"
    echo "  TORERO_MCP_HOST        MCP server host (default: 127.0.0.1)"
    echo "  TORERO_MCP_PORT        MCP server port (default: 8080)"
    echo "  TORERO_MCP_PID_FILE    PID file location (default: /tmp/torero-mcp.pid)"
    echo "  TORERO_MCP_LOG_FILE    Log file location (default: /tmp/torero-mcp.log)"
    echo "  TORERO_MCP_CONFIG      Configuration file path"
    exit 1
}

start_daemon() {
    echo "Starting torero-mcp daemon..."
    
    # Build command args
    CMD_ARGS=(
        "run"
        "--daemon"
        "--host" "$TORERO_MCP_HOST"
        "--port" "$TORERO_MCP_PORT"
        "--pid-file" "$TORERO_MCP_PID_FILE"
        "--log-file" "$TORERO_MCP_LOG_FILE"
    )
    
    # Add config if specified
    if [ -n "$TORERO_MCP_CONFIG" ] && [ -f "$TORERO_MCP_CONFIG" ]; then
        CMD_ARGS+=("--config" "$TORERO_MCP_CONFIG")
    fi
    
    # Execute command
    if [[ "$TORERO_MCP_BIN" == *"python -m"* ]]; then

        # Handle python module execution
        eval "$TORERO_MCP_BIN" "${CMD_ARGS[@]}"
    else

        # Handle direct binary execution
        $TORERO_MCP_BIN "${CMD_ARGS[@]}"
    fi
    
    echo "torero-mcp daemon started"
}

stop_daemon() {
    echo "Stopping torero-mcp daemon..."
    $TORERO_MCP_BIN stop --pid-file "$TORERO_MCP_PID_FILE"
}

restart_daemon() {
    echo "Restarting torero-mcp daemon..."
    
    # Build restart command args
    CMD_ARGS=(
        "restart"
        "--pid-file" "$TORERO_MCP_PID_FILE"
        "--log-file" "$TORERO_MCP_LOG_FILE"
    )
    
    # Add config if specified
    if [ -n "$TORERO_MCP_CONFIG" ] && [ -f "$TORERO_MCP_CONFIG" ]; then
        CMD_ARGS+=("--config" "$TORERO_MCP_CONFIG")
    fi
    
    # Execute command
    if [[ "$TORERO_MCP_BIN" == *"python -m"* ]]; then

        # Handle python module execution
        eval "$TORERO_MCP_BIN" "${CMD_ARGS[@]}"
    else

        # Handle direct binary execution
        $TORERO_MCP_BIN "${CMD_ARGS[@]}"
    fi
}

check_status() {
    $TORERO_MCP_BIN status --pid-file "$TORERO_MCP_PID_FILE"
}

view_logs() {
    $TORERO_MCP_BIN logs --log-file "$TORERO_MCP_LOG_FILE"
}

follow_logs() {
    $TORERO_MCP_BIN follow-logs --log-file "$TORERO_MCP_LOG_FILE"
}

# Main command handling
case "${1:-}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    follow-logs)
        follow_logs
        ;;
    *)
        usage
        ;;
esac