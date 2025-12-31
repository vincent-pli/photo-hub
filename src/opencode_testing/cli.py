"""CLI interface for opencode-testing."""

import sys
import logging
from typing import Optional

import click
from . import __version__
from .main import hello, add, multiply, divide, run as app_run

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="opencode-testing")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool) -> None:
    """opencode-testing - A Python application for testing opencode functionality."""
    # Ensure ctx.obj exists
    if ctx.obj is None:
        ctx.obj = {}

    # Configure logging
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug

    if debug:
        logger.debug("Debug mode enabled")
    elif verbose:
        logger.info("Verbose mode enabled")


@cli.command()
@click.option("--name", default="World", help="Name to greet.")
@click.pass_context
def greet(ctx: click.Context, name: str) -> None:
    """Greet someone."""
    message = hello(name)
    click.echo(message)
    if ctx.obj.get("verbose"):
        click.echo(f"Greeted: {name}")


@cli.command()
@click.argument("a", type=float)
@click.argument("b", type=float)
@click.pass_context
def calculate(ctx: click.Context, a: float, b: float) -> None:
    """Perform calculations on two numbers."""
    click.echo(f"{a} + {b} = {add(a, b)}")
    click.echo(f"{a} * {b} = {multiply(a, b)}")
    
    try:
        click.echo(f"{a} / {b} = {divide(a, b)}")
    except ValueError as e:
        click.echo(f"Division error: {e}", err=True)


@cli.command()
@click.option("--name", default="World", help="Name to greet.")
@click.option("--timeout", type=int, default=30, help="Timeout in seconds.")
@click.pass_context
def run(ctx: click.Context, name: str, timeout: int) -> None:
    """Run the main application."""
    if ctx.obj.get("verbose"):
        click.echo(f"Running with name={name}, timeout={timeout}")
    
    # Call the main application logic
    try:
        # Simulate some work
        import time
        if ctx.obj.get("verbose"):
            click.echo("Working...")
        
        # Use the main module's run function
        result = app_run("--name", name)
        
        if result == 0:
            click.echo("Application completed successfully")
        else:
            click.echo(f"Application failed with exit code {result}", err=True)
            ctx.exit(result)
            
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=ctx.obj.get("debug"))
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Display system and package information."""
    import platform
    click.echo(f"opencode-testing v{__version__}")
    click.echo(f"Python {platform.python_version()} on {platform.system()} {platform.release()}")
    click.echo(f"Platform: {platform.platform()}")
    
    if ctx.obj.get("verbose"):
        import sys
        click.echo(f"Executable: {sys.executable}")
        click.echo(f"Path: {sys.path}")


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"Fatal error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()