"""CLI interface for photo-hub."""

import sys
import os
import json
import logging
from typing import Optional

import click
from . import __version__
from .main import hello, add, multiply, divide, run as app_run

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="photo-hub")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool) -> None:
    """photo-hub - AI-powered photo management and search tool."""
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
    click.echo(f"photo-hub v{__version__}")
    click.echo(f"Python {platform.python_version()} on {platform.system()} {platform.release()}")
    click.echo(f"Platform: {platform.platform()}")
    
    if ctx.obj.get("verbose"):
        import sys
        click.echo(f"Executable: {sys.executable}")
        click.echo(f"Path: {sys.path}")


@cli.group()
def photos():
    """Manage and search photos with AI analysis."""
    pass


@photos.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--recursive/--no-recursive", default=True, help="Scan subdirectories recursively")
@click.option("--api-key", help="Google AI Studio API key (or set GOOGLE_API_KEY env var)")
@click.option("--model", default="gemini-2.0-flash-exp", help="Gemini model to use (e.g., gemini-2.0-flash-exp, gemini-flash-latest, gemini-2.5-flash, gemini-2.0-flash)")
@click.option("--db-path", default="photo_search.db", help="Database file path")
@click.option("--skip-existing", is_flag=True, help="Skip photos already analyzed")
@click.option("--mock", is_flag=True, help="Use mock analyzer for testing (no API calls)")
@click.pass_context
def scan(ctx, directory, recursive, api_key, model, db_path, skip_existing, mock):
    """Scan directory and analyze photos with Gemini."""
    try:
        from photo_hub.photo_search.scanner import scan_photos
        from photo_hub.photo_search.gemini_client_new import GeminiPhotoAnalyzer, MockPhotoAnalyzer
        from photo_hub.photo_search.metadata_store import MetadataStore
    except ImportError as e:
        click.echo(f"Error: Photo search dependencies not installed. Install with: pip install photo-hub[photo]", err=True)
        click.echo(f"Detailed error: {e}", err=True)
        ctx.exit(1)
    
    click.echo(f"Scanning directory: {directory} (recursive: {recursive})")
    click.echo(f"Database: {db_path}")
    
    # Initialize components
    store = MetadataStore(db_path)
    
    # Choose analyzer based on mock flag
    if mock:
        click.echo("Using mock analyzer (no API calls)")
        analyzer = MockPhotoAnalyzer(model="mock-gemini")
    else:
        # Get API key from parameter or environment
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            click.echo("Error: API key required. Set --api-key or GOOGLE_API_KEY environment variable.", err=True)
            ctx.exit(1)
        click.echo(f"Using model: {model}")
        analyzer = GeminiPhotoAnalyzer(api_key=api_key, model=model)
    
    # Scan photos
    photos = scan_photos(directory, recursive=recursive)
    click.echo(f"Found {len(photos)} photos")
    
    # Filter out already analyzed photos if requested
    if skip_existing:
        filtered_photos = []
        for photo in photos:
            existing = store.get_analysis_result(photo.path, model)
            if existing:
                click.echo(f"Skipping already analyzed: {photo.filename}")
            else:
                filtered_photos.append(photo)
        photos = filtered_photos
        click.echo(f"After filtering, {len(photos)} photos to analyze")
    
    if not photos:
        click.echo("No photos to analyze.")
        return
    
    # Analyze photos
    successful = 0
    for i, photo in enumerate(photos, 1):
        click.echo(f"Analyzing [{i}/{len(photos)}]: {photo.filename}")
        try:
            result = analyzer.analyze_photo(photo.path)
            store.save_analysis_result(result)
            successful += 1
            click.echo(f"  ✓ {result.description[:100]}...")
        except Exception as e:
            click.echo(f"  ✗ Error: {e}", err=True)
            if ctx.obj.get("debug"):
                import traceback
                traceback.print_exc()
    
    click.echo(f"Analysis complete: {successful}/{len(photos)} successful")
    
    # Show stats
    stats = store.get_stats()
    click.echo(f"\nDatabase statistics:")
    click.echo(f"  Total photos: {stats.get('total_photos', 0)}")
    click.echo(f"  Total analyses: {stats.get('total_analyses', 0)}")
    click.echo(f"  Models used: {stats.get('models_used', 0)}")


@photos.command()
@click.argument("query")
@click.option("--db-path", default="photo_search.db", help="Database file path")
@click.option("--limit", default=20, help="Maximum results to show")
@click.option("--output-format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.pass_context
def search(ctx, query, db_path, limit, output_format):
    """Search analyzed photos by keywords."""
    try:
        from photo_hub.photo_search.metadata_store import MetadataStore
    except ImportError as e:
        click.echo(f"Error: Photo search dependencies not installed. Install with: pip install photo-hub[photo]", err=True)
        click.echo(f"Detailed error: {e}", err=True)
        ctx.exit(1)
    
    click.echo(f"Searching for: '{query}'")
    
    store = MetadataStore(db_path)
    results = store.search_photos(query, limit=limit)
    
    if output_format == "json":
        import json
        click.echo(json.dumps(results, indent=2, default=str))
    else:
        if not results:
            click.echo("No results found.")
            return
        
        click.echo(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            click.echo(f"\n{i}. {result['filename']}")
            click.echo(f"   Path: {result['path']}")
            if result.get('description'):
                click.echo(f"   Description: {result['description'][:200]}...")
            if result.get('tags'):
                tags = result['tags']
                if isinstance(tags, str):
                    tags = json.loads(tags)
                click.echo(f"   Tags: {', '.join(tags[:10])}")


@photos.command()
@click.option("--db-path", default="photo_search.db", help="Database file path")
@click.pass_context
def stats(ctx, db_path):
    """Show photo database statistics."""
    try:
        from photo_hub.photo_search.metadata_store import MetadataStore
    except ImportError as e:
        click.echo(f"Error: Photo search dependencies not installed. Install with: pip install photo-hub[photo]", err=True)
        click.echo(f"Detailed error: {e}", err=True)
        ctx.exit(1)
    
    store = MetadataStore(db_path)
    stats = store.get_stats()
    
    click.echo("Photo Database Statistics:")
    click.echo(f"  Database file: {db_path}")
    click.echo(f"  Total photos: {stats.get('total_photos', 0)}")
    click.echo(f"  Total analyses: {stats.get('total_analyses', 0)}")
    click.echo(f"  Models used: {stats.get('models_used', 0)}")
    
    # Additional stats if verbose
    if ctx.obj.get("verbose"):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT llm_model, COUNT(*) FROM analysis_results GROUP BY llm_model")
        models = cursor.fetchall()
        if models:
            click.echo("  Analyses by model:")
            for model, count in models:
                click.echo(f"    {model}: {count}")
        conn.close()


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"Fatal error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()