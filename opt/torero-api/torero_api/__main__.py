"""
Command-line interface for torero-api

This module provides the command-line interface for starting and managing the torero API server.
It can be run directly with "python -m torero_api".
"""

import argparse
import logging
import sys
import os
import signal
import atexit
from pathlib import Path
from torero_api.server import start_server
from torero_api.core.torero_executor import check_torero_available, check_torero_version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("torero-api-cli")

def create_pid_file(pid_file):
    """Create PID file with current process ID"""
    try:
        pid_path = Path(pid_file)
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(os.getpid()))
        logger.info(f"PID file created: {pid_file}")
        
        # Register cleanup function
        atexit.register(lambda: cleanup_pid_file(pid_file))
        
    except Exception as e:
        logger.error(f"Failed to create PID file {pid_file}: {e}")
        sys.exit(1)

def cleanup_pid_file(pid_file):
    """Remove PID file on exit"""
    try:
        pid_path = Path(pid_file)
        if pid_path.exists():
            pid_path.unlink()
            logger.info(f"PID file removed: {pid_file}")
    except Exception as e:
        logger.error(f"Failed to remove PID file {pid_file}: {e}")

def setup_logging_for_daemon(log_file, log_level):
    """Setup logging for daemon mode"""
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        logger.info(f"Daemon logging initialized: {log_file}")
        
    except Exception as e:
        print(f"Failed to setup daemon logging: {e}")
        sys.exit(1)

def daemonize(pid_file, log_file, log_level):
    """
    Daemonize the current process using double fork.
    
    Args:
        pid_file: Path to store the process ID
        log_file: Path to redirect logs
        log_level: Log level for daemon
    """
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Parent process - exit
            sys.exit(0)
    except OSError as e:
        logger.error(f"First fork failed: {e}")
        sys.exit(1)

    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # First child - exit
            sys.exit(0)
    except OSError as e:
        logger.error(f"Second fork failed: {e}")
        sys.exit(1)

    # Now we're in the daemon process
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Redirect stdin, stdout, stderr to /dev/null or log file
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    # Setup logging before redirecting stdout/stderr
    setup_logging_for_daemon(log_file, log_level)
    
    # Redirect stdout and stderr to log file
    with open(log_file, 'a') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # Create PID file
    create_pid_file(pid_file)
    
    logger.info("Daemon process started successfully")

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name} ({signum}), shutting down gracefully...")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Ignore SIGHUP in daemon mode
    signal.signal(signal.SIGHUP, signal.SIG_IGN)

def check_daemon_running(pid_file):
    """Check if daemon is already running"""
    pid_path = Path(pid_file)
    
    if not pid_path.exists():
        return False, None
    
    try:
        pid = int(pid_path.read_text().strip())
        
        # Check if process exists
        os.kill(pid, 0)  # Send signal 0 to check if process exists
        return True, pid
        
    except (ValueError, ProcessLookupError, PermissionError):
        # PID file exists but process doesn't, clean up
        try:
            pid_path.unlink()
        except:
            pass
        return False, None

def main():
    """
    Main entry point for the torero API CLI.
    
    This function handles command-line arguments and starts the API server.
    """

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="torero API - RESTful API for torero service management",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add command-line arguments
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"], 
                        help="Log level to use")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (for development)")
    parser.add_argument("--version", action="store_true", help="Show version information and exit")
    parser.add_argument("--check", action="store_true", help="Check torero availability and exit")
    
    # Daemon options
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    parser.add_argument("--pid-file", default="/tmp/torero-api.pid", help="PID file for daemon mode")
    parser.add_argument("--log-file", default="/tmp/torero-api.log", help="Log file for daemon mode")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show version information if requested
    if args.version:
        from torero_api import __version__
        print(f"torero-api version: {__version__}")
        
        # Check torero version
        available, message = check_torero_available()
        if available:
            torero_version = check_torero_version()
            print(f"torero version: {torero_version}")
        else:
            print(f"torero: {message}")
        
        sys.exit(0)
    
    # Check torero availability if requested
    if args.check:
        available, message = check_torero_available()
        if available:
            print(f"torero: Available ({check_torero_version()})")
            sys.exit(0)
        else:
            print(f"torero: Not available - {message}")
            sys.exit(1)
    
    # Daemon mode validation
    if args.daemon:
        if args.reload:
            logger.error("Cannot use --reload with --daemon mode")
            sys.exit(1)
            
        # Check if daemon is already running
        is_running, existing_pid = check_daemon_running(args.pid_file)
        if is_running:
            logger.error(f"torero-api daemon is already running (PID: {existing_pid})")
            sys.exit(1)
        
        logger.info(f"Starting torero-api in daemon mode...")
        logger.info(f"PID file: {args.pid_file}")
        logger.info(f"Log file: {args.log_file}")
        logger.info(f"API will be available at: http://{args.host}:{args.port}")
        
        # Daemonize the process
        daemonize(args.pid_file, args.log_file, args.log_level)
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        
        logger.info(f"Daemon started successfully (PID: {os.getpid()})")
    
    # Check if torero is available before starting the server
    available, message = check_torero_available()
    if not available:
        logger.warning(f"torero not available: {message}")
        logger.warning("The API will start, but some functionality may not work correctly.")
    
    # Start the server
    try:
        logger.info(f"Starting torero API server on {args.host}:{args.port}")
        start_server(
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            reload=args.reload
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()