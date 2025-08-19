#!/bin/bash
#
# Copyright 2025 torerodev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -eo pipefail

# default configuration
DEFAULT_UI_PORT=8001
DEFAULT_API_URL="http://localhost:8000"
DEFAULT_REFRESH_INTERVAL=30
DEFAULT_LOG_FILE="/tmp/torero-ui.log"
DEFAULT_PID_FILE="/tmp/torero-ui.pid"

# environment variables
UI_PORT="${TORERO_UI_PORT:-$DEFAULT_UI_PORT}"
API_URL="${TORERO_API_BASE_URL:-$DEFAULT_API_URL}"
REFRESH_INTERVAL="${DASHBOARD_REFRESH_INTERVAL:-$DEFAULT_REFRESH_INTERVAL}"
LOG_FILE="${TORERO_UI_LOG_FILE:-$DEFAULT_LOG_FILE}"
PID_FILE="${TORERO_UI_PID_FILE:-$DEFAULT_PID_FILE}"
DEBUG="${DEBUG:-False}"

# script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

usage() {
    echo "Usage: $0 {start|stop|restart|status|logs}"
    echo ""
    echo "Environment variables:"
    echo "  TORERO_UI_PORT              UI server port (default: $DEFAULT_UI_PORT)"
    echo "  TORERO_API_BASE_URL         torero-api base URL (default: $DEFAULT_API_URL)"
    echo "  DASHBOARD_REFRESH_INTERVAL  dashboard refresh interval in seconds (default: $DEFAULT_REFRESH_INTERVAL)"
    echo "  TORERO_UI_LOG_FILE          log file path (default: $DEFAULT_LOG_FILE)"
    echo "  TORERO_UI_PID_FILE          PID file path (default: $DEFAULT_PID_FILE)"
    echo "  DEBUG                       enable debug mode (default: False)"
    exit 1
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

start_ui() {
    if is_running; then
        echo "torero-ui is already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    echo "starting torero-ui on port $UI_PORT..."
    
    # set environment variables for django
    export TORERO_API_BASE_URL="$API_URL"
    export DASHBOARD_REFRESH_INTERVAL="$REFRESH_INTERVAL"
    export DEBUG="$DEBUG"
    export DJANGO_SETTINGS_MODULE="torero_ui.settings"
    
    # ensure database is set up
    if ! python -m torero_ui.manage migrate --check >/dev/null 2>&1; then
        echo "setting up database..."
        python -m torero_ui.manage migrate
    fi
    
    # start server in background
    nohup python -m torero_ui.manage runserver "0.0.0.0:$UI_PORT" \
        --noreload \
        > "$LOG_FILE" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        echo "torero-ui started successfully (PID: $pid)"
        echo "dashboard available at: http://localhost:$UI_PORT"
        return 0
    else
        echo "failed to start torero-ui"
        return 1
    fi
}

stop_ui() {
    if ! is_running; then
        echo "torero-ui is not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    echo "stopping torero-ui (PID: $pid)..."
    
    kill "$pid"
    
    # wait for graceful shutdown
    local timeout=10
    while [ $timeout -gt 0 ] && kill -0 "$pid" 2>/dev/null; do
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if kill -0 "$pid" 2>/dev/null; then
        echo "forcing termination..."
        kill -9 "$pid"
    fi
    
    rm -f "$PID_FILE"
    echo "torero-ui stopped"
}

status_ui() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "torero-ui is running (PID: $pid)"
        echo "dashboard URL: http://localhost:$UI_PORT"
        echo "log file: $LOG_FILE"
        return 0
    else
        echo "torero-ui is not running"
        return 1
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "log file not found: $LOG_FILE"
        return 1
    fi
}

# main
case "${1:-}" in
    start)
        start_ui
        ;;
    stop)
        stop_ui
        ;;
    restart)
        stop_ui
        start_ui
        ;;
    status)
        status_ui
        ;;
    logs)
        show_logs
        ;;
    *)
        usage
        ;;
esac