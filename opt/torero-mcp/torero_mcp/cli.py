"""Command-line interface for torero MCP server."""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .config import Config, load_config, setup_logging
from .server import ToreroMCPServer

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """torero MCP Server CLI."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Override logging level"
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable_http"]),
    envvar="TORERO_MCP_TRANSPORT_TYPE",
    help="Transport type (overrides config)"
)
@click.option(
    "--host",
    envvar="TORERO_MCP_TRANSPORT_HOST",
    help="Host for SSE/HTTP transport (overrides config)"
)
@click.option(
    "--port",
    type=int,
    envvar="TORERO_MCP_TRANSPORT_PORT",
    help="Port for SSE/HTTP transport (overrides config)"
)
@click.option(
    "--sse-path",
    envvar="TORERO_MCP_TRANSPORT_PATH",
    help="SSE endpoint path (overrides config)"
)
@click.option(
    "--daemon",
    is_flag=True,
    help="Run as daemon in background"
)
@click.option(
    "--pid-file",
    type=click.Path(path_type=Path),
    envvar="TORERO_MCP_PID_FILE",
    default="/tmp/torero-mcp.pid",
    help="PID file location for daemon mode"
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path), 
    envvar="TORERO_MCP_LOG_FILE",
    help="Log file location for daemon mode"
)
def run(
    config: Optional[Path] = None,
    log_level: Optional[str] = None,
    transport: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    sse_path: Optional[str] = None,
    daemon: bool = False,
    pid_file: Optional[Path] = None,
    log_file: Optional[Path] = None,
) -> None:
    """
    Run the torero MCP Server.
    
    A Model Context Protocol server for torero API integration.
    Provides AI assistants with access to torero services, decorators,
    repositories, and secrets.
    """
    try:
        # Load configuration
        app_config = load_config(config)
        
        # Override with CLI args
        if log_level:
            app_config.logging.level = log_level
        
        # Override transport settings
        if transport:
            app_config.mcp.transport.type = transport
        if host:
            app_config.mcp.transport.host = host
        if port:
            app_config.mcp.transport.port = port
        if sse_path:
            app_config.mcp.transport.path = sse_path
        
        # Override logging with log file if specified
        if log_file:
            app_config.logging.file = str(log_file)
        
        # Handle daemon mode
        if daemon:
            _daemonize(pid_file, log_file, app_config)
        else:
            _run_server(app_config)
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Failed to start server")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _daemonize(pid_file: Optional[Path], log_file: Optional[Path], app_config: Config) -> None:
    """Daemonize the process."""

    # Is it already running?
    if pid_file and pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())

            # Check process
            os.kill(old_pid, 0)
            click.echo(f"Error: torero-mcp daemon already running with PID {old_pid}")
            sys.exit(1)
        except (OSError, ValueError):

            # Not running, remove stale PID file
            pid_file.unlink(missing_ok=True)
    
    # First fork
    if os.fork() > 0:
        sys.exit(0)
    
    # Decouple from parent env
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    # Second fork
    if os.fork() > 0:
        sys.exit(0)
    
    # Write PID file
    if pid_file:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Close standard descriptors; redirect to /dev/null
    with open(os.devnull, 'r') as devnull_r:
        os.dup2(devnull_r.fileno(), sys.stdin.fileno())
    
    with open(os.devnull, 'w') as devnull_w:
        os.dup2(devnull_w.fileno(), sys.stdout.fileno())
        os.dup2(devnull_w.fileno(), sys.stderr.fileno())
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        if pid_file and pid_file.exists():
            pid_file.unlink(missing_ok=True)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run server
    _run_server(app_config)


def _run_server(app_config: Config) -> None:
    """Run the MCP server with the given configuration."""

    # Setup logging
    setup_logging(app_config.logging)
    
    logger.info(f"Starting torero MCP server v{__version__}")
    logger.info(f"Configuration loaded from: {app_config}")
    logger.debug(f"Log level: {app_config.logging.level}")
    logger.debug(f"Transport type: {app_config.mcp.transport.type}")
    if app_config.mcp.transport.type in ["sse", "streamable_http"]:
        logger.debug(f"Server address: {app_config.mcp.transport.host}:{app_config.mcp.transport.port}")
    
    # Test connection first
    async def test_connection():
        server = ToreroMCPServer(app_config)
        await server.test_connection()
        await server.close()
    
    # Run connection test
    asyncio.run(test_connection())
    
    # Create and run server (FastMCP handles the event loop)
    server = ToreroMCPServer(app_config)
    server.run()


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="config.yaml",
    help="Output configuration file path"
)
def init_config(output: Path) -> None:
    """Generate a sample configuration file."""
    
    config_content = """# torero MCP Server Configuration

executor:
  # CLI command timeout in seconds
  timeout: 30
  
  # torero command path (default: torero)
  torero_command: "torero"
  
logging:
  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: "INFO"
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Optional: Log to file
  # file: "torero-mcp.log"

# Optional: MCP server settings
mcp:
  # Server name
  name: "torero"
  
  # Server version
  version: "0.1.0"
  
  # Transport configuration
  transport:
    # Transport type: stdio (default), sse, or streamable_http
    type: "stdio"
    
    # Settings for SSE/HTTP transport (ignored for stdio)
    host: "127.0.0.1"
    port: 8000
    
    # SSE-specific settings
    path: "/sse"
"""
    
    if output.exists():
        if not click.confirm(f"Configuration file {output} already exists. Overwrite?"):
            click.echo("Aborted.")
            return
    
    output.write_text(config_content)
    click.echo(f"Configuration file created: {output}")
    click.echo("Edit the file to customize your settings.")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file"
)
def test_connection(
    config: Optional[Path] = None,
) -> None:
    """Test connection to torero CLI."""
    
    async def _test() -> None:
        from .executor import ToreroExecutor
        
        # Load config
        app_config = load_config(config)
        
        # Setup basic logging
        logging.basicConfig(level=logging.INFO)
        
        click.echo("Testing torero CLI connection...")
        
        try:
            executor = ToreroExecutor(timeout=app_config.executor.timeout)
            
            # Test version command
            version = await executor.execute_command(["version"], parse_json=False)
            click.echo("✓ Connection successful!")
            click.echo(f"torero version: {version}")
            
            # Test listing services
            try:
                services = await executor.get_services()
                click.echo(f"✓ CLI functional - found {len(services)} service(s)")
            except Exception as e:
                click.echo(f"⚠ CLI connection OK but listing services failed: {e}")
                    
        except Exception as e:
            click.echo(f"✗ Connection failed: {e}")
            sys.exit(1)
    
    asyncio.run(_test())


@cli.command()
def version() -> None:
    """Show version information."""

    click.echo(f"torero-mcp {__version__}")

@cli.command()
@click.option(
    "--pid-file",
    type=click.Path(path_type=Path),
    envvar="TORERO_MCP_PID_FILE", 
    default="/tmp/torero-mcp.pid",
    help="PID file location"
)
def stop(pid_file: Path) -> None:
    """Stop the daemon."""

    if not pid_file.exists():
        click.echo("Error: torero-mcp daemon is not running")
        sys.exit(1)
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM to gracefully stop the daemon
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to exit
        for _ in range(30):  # Wait up to 30 seconds
            try:
                os.kill(pid, 0)  # Check if process still exists
                time.sleep(1)
            except OSError:
                # Process no longer exists
                break
        else:

            # Force kill if it didn't stop gracefully
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        
        # Remove PID file
        pid_file.unlink(missing_ok=True)
        click.echo(f"torero-mcp daemon stopped (PID {pid})")
        
    except (OSError, ValueError) as e:
        click.echo(f"Error stopping daemon: {e}")

        # Clean up stale PID file
        pid_file.unlink(missing_ok=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--pid-file", 
    type=click.Path(path_type=Path),
    envvar="TORERO_MCP_PID_FILE",
    default="/tmp/torero-mcp.pid",
    help="PID file location"
)
def status(pid_file: Path) -> None:
    """Check daemon status."""

    if not pid_file.exists():
        click.echo("torero-mcp daemon is not running")
        sys.exit(1)
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is still running
        os.kill(pid, 0)
        click.echo(f"torero-mcp daemon is running (PID {pid})")
        
    except (OSError, ValueError):
        click.echo("torero-mcp daemon is not running (stale PID file)")
        pid_file.unlink(missing_ok=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    envvar="TORERO_MCP_LOG_FILE",
    help="Log file location"
)
@click.option(
    "--lines",
    "-n",
    type=int,
    default=50,
    help="Number of lines to show"
)
def logs(log_file: Optional[Path], lines: int) -> None:
    """View daemon logs."""

    if not log_file:
        click.echo("Error: No log file specified. Use --log-file or set TORERO_MCP_LOG_FILE")
        sys.exit(1)
    
    if not log_file.exists():
        click.echo(f"Error: Log file {log_file} does not exist")
        sys.exit(1)
    
    try:

        # Use tail to show last N lines
        result = subprocess.run(['tail', f'-{lines}', str(log_file)], 
                              capture_output=True, text=True)
        click.echo(result.stdout)
    except Exception as e:
        click.echo(f"Error reading log file: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--log-file",
    type=click.Path(path_type=Path), 
    envvar="TORERO_MCP_LOG_FILE",
    help="Log file location"
)
def follow_logs(log_file: Optional[Path]) -> None:
    """Follow daemon logs in real-time."""

    if not log_file:
        click.echo("Error: No log file specified. Use --log-file or set TORERO_MCP_LOG_FILE")
        sys.exit(1)
    
    if not log_file.exists():
        click.echo(f"Error: Log file {log_file} does not exist")
        sys.exit(1)
    
    try:
        # Use tail -f to follow logs
        subprocess.run(['tail', '-f', str(log_file)])
    except KeyboardInterrupt:
        click.echo("\nStopped following logs")
    except Exception as e:
        click.echo(f"Error following log file: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file"
)
@click.option(
    "--pid-file",
    type=click.Path(path_type=Path),
    envvar="TORERO_MCP_PID_FILE",
    default="/tmp/torero-mcp.pid", 
    help="PID file location"
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    envvar="TORERO_MCP_LOG_FILE",
    help="Log file location for daemon mode"
)
@click.pass_context
def restart(ctx, config: Optional[Path], pid_file: Path, log_file: Optional[Path]) -> None:
    """Restart the daemon."""

    # Stop if running
    if pid_file.exists():
        ctx.invoke(stop, pid_file=pid_file)
    
    # Start with daemon mode
    run_args = ['--daemon', '--pid-file', str(pid_file)]
    if config:
        run_args.extend(['--config', str(config)])
    if log_file:
        run_args.extend(['--log-file', str(log_file)])
    
    # Use subprocess to start daemon
    result = subprocess.run([sys.executable, '-m', 'torero_mcp.cli', 'run'] + run_args)
    if result.returncode == 0:
        click.echo("torero-mcp daemon restarted")
    else:
        click.echo("Error restarting daemon")
        sys.exit(1)


# Main function
def main() -> None:
    """Main entry point."""

    # If no args provided, show help
    if len(sys.argv) == 1:
        ctx = cli.make_context('torero-mcp', ['--help'])
        click.echo(cli.get_help(ctx))
        return
        
    # If called with old-style args, convert to new style
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-') and sys.argv[1] not in ['run', 'test-connection', 'init-config', 'version']:

        # Run server
        sys.argv.insert(1, 'run')
    elif len(sys.argv) > 1 and sys.argv[1].startswith('--'):

        # Old style flags, add 'run' command
        sys.argv.insert(1, 'run')
    
    cli()


if __name__ == "__main__":
    main()