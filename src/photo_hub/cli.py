"""CLI interface for photo-hub."""

import sys
import os
import json
import logging
from pathlib import Path
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
@click.option("--api-key", help="API key for the AI service (or set GOOGLE_API_KEY/QWEN_API_KEY environment variable)")
@click.option("--model", default="gemini-2.0-flash-exp", help="Model to use (e.g., gemini-2.0-flash-exp, qwen-max, qwen-turbo, mock)")
@click.option("--base-url", help="Custom base URL for API (for self-hosted or custom endpoints)")
@click.option("--db-path", default="~/.photo-hub/database.db", help="Database file path")
@click.option("--skip-existing", is_flag=True, help="Skip photos already analyzed")
@click.option("--language", type=click.Choice(["en", "zh", "auto"]), default="auto", help="Language for analysis (en=English, zh=Chinese, auto=auto-detect)")
@click.option("--mock", is_flag=True, help="Use mock analyzer for testing (no API calls)")
@click.option("--max-concurrent", type=int, help="Maximum concurrent API calls (default: 5 for Qwen, 3 for Gemini)")
@click.option("--batch-size", type=int, default=10, help="Batch size for processing (default: 10)")
@click.option("--async-mode", is_flag=True, help="Use async processing for better performance")
@click.pass_context
def scan(ctx, directory, recursive, api_key, model, base_url, db_path, skip_existing, language, mock, max_concurrent, batch_size, async_mode):
    """Scan directory and analyze photos with AI models."""
    from photo_hub.photo_search.config import Language
    from pathlib import Path
    try:
        from photo_hub.photo_search.scanner import scan_photos
        from photo_hub.photo_search.metadata_store import MetadataStore
        from photo_hub.photo_search.factory import create_analyzer
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
        from photo_hub.photo_search.gemini_client_new import MockPhotoAnalyzer
        analyzer = MockPhotoAnalyzer(model="mock")
    else:
        click.echo(f"Using model: {model}")
        try:
            analyzer = create_analyzer(
                model=model,
                api_key=api_key,
                base_url=base_url
            )
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        except ImportError as e:
            # Provide specific installation instructions based on model type
            if model.lower().startswith("qwen"):
                click.echo(f"Error: Missing dependencies for Qwen model '{model}'.", err=True)
                click.echo(f"To install Qwen dependencies, run:", err=True)
                click.echo(f"  pip install photo-hub[photo]", err=True)
                click.echo(f"Or install specific packages:", err=True)
                click.echo(f"  pip install openai pillow", err=True)
            elif model.lower().startswith("gemini"):
                click.echo(f"Error: Missing dependencies for Gemini model '{model}'.", err=True)
                click.echo(f"To install Gemini dependencies, run:", err=True)
                click.echo(f"  pip install photo-hub[photo]", err=True)
                click.echo(f"Or install specific packages:", err=True)
                click.echo(f"  pip install google-genai pillow", err=True)
            else:
                click.echo(f"Error: Missing dependencies for model '{model}'.", err=True)
                click.echo(f"To install all photo analysis dependencies, run:", err=True)
                click.echo(f"  pip install photo-hub[photo]", err=True)
            click.echo(f"Detailed error: {e}", err=True)
            ctx.exit(1)
    
    # Scan photos
    photos = scan_photos(directory, recursive=recursive)
    click.echo(f"Found {len(photos)} photos")
    
    # Filter out already analyzed photos if requested
    skipped_files = 0
    if skip_existing:
        filtered_photos = []
        for photo in photos:
            existing = store.get_analysis_result(photo.path, model)
            if existing:
                click.echo(f"Skipping already analyzed: {photo.filename}")
                skipped_files += 1
            else:
                filtered_photos.append(photo)
        photos = filtered_photos
        click.echo(f"After filtering, {len(photos)} photos to analyze (skipped {skipped_files})")
    
    # Convert language string to Language enum
    language_enum = Language.normalize(language)
    
    if not photos:
        click.echo("No photos to analyze.")
        return
    
    # Set concurrency limits
    if max_concurrent:
        analyzer.set_concurrency_limit(max_concurrent)
    analyzer.set_batch_size(batch_size)
    
    # Analyze photos
    successful = 0
    failed = 0
    
    if async_mode:
        # Use async processing
        click.echo(f"Using async mode with {max_concurrent or 'default'} concurrent workers")
        try:
            import asyncio
            
            async def analyze_async():
                nonlocal successful, failed
                
                # Try to use batch store for better performance
                try:
                    from photo_hub.photo_search.metadata_store import BatchMetadataStore
                    batch_store = BatchMetadataStore(db_path, batch_size=50)
                    use_batch = True
                except ImportError:
                    batch_store = store
                    use_batch = False
                
                # Get image paths
                image_paths = [photo.path for photo in photos]
                
                # Use async batch analysis if available
                try:
                    results = await analyzer.batch_analyze_async(
                        image_paths=image_paths,
                        language=language_enum,
                        max_concurrent=max_concurrent or 5,
                        batch_size=batch_size
                    )
                    
                    # Save results
                    for i, result in enumerate(results, 1):
                        click.echo(f"Analyzed [{i}/{len(photos)}]: {Path(result.photo_path).name}")
                        
                        if use_batch:
                            await batch_store.save_analysis_result_batch(result)
                        else:
                            store.save_analysis_result(result)
                        
                        successful += 1
                        click.echo(f"  ✓ {result.description[:100]}...")
                    
                    # Flush batch if used
                    if use_batch:
                        await batch_store.flush_batch()
                        
                except (AttributeError, NotImplementedError):
                    # Fall back to synchronous processing
                    click.echo("Async batch analysis not available, falling back to synchronous")
                    for i, photo in enumerate(photos, 1):
                        click.echo(f"Analyzing [{i}/{len(photos)}]: {photo.filename}")
                        try:
                            result = analyzer.analyze_photo(photo.path, language=language_enum)
                            store.save_analysis_result(result)
                            successful += 1
                            click.echo(f"  ✓ {result.description[:100]}...")
                        except Exception as e:
                            click.echo(f"  ✗ Error: {e}", err=True)
                            failed += 1
                            if ctx.obj.get("debug"):
                                import traceback
                                traceback.print_exc()
            
            # Run async analysis
            asyncio.run(analyze_async())
            
        except ImportError as e:
            click.echo(f"Async mode not available: {e}, falling back to synchronous", err=True)
            async_mode = False
    
    if not async_mode:
        # Synchronous processing
        for i, photo in enumerate(photos, 1):
            click.echo(f"Analyzing [{i}/{len(photos)}]: {photo.filename}")
            try:
                result = analyzer.analyze_photo(photo.path, language=language_enum)
                store.save_analysis_result(result)
                successful += 1
                click.echo(f"  ✓ {result.description[:100]}...")
            except Exception as e:
                click.echo(f"  ✗ Error: {e}", err=True)
                failed += 1
                if ctx.obj.get("debug"):
                    import traceback
                    traceback.print_exc()
    
    total_attempted = successful + failed
    click.echo(f"Analysis complete: {successful}/{total_attempted} successful, {failed} failed")
    if skipped_files > 0:
        click.echo(f"Skipped {skipped_files} already analyzed photos")
    
    # Show stats
    stats = store.get_stats()
    click.echo(f"\nDatabase statistics:")
    click.echo(f"  Total photos: {stats.get('total_photos', 0)}")
    click.echo(f"  Total analyses: {stats.get('total_analyses', 0)}")
    click.echo(f"  Models used: {stats.get('models_used', 0)}")


@photos.command()
@click.argument("query")
@click.option("--db-path", default="~/.photo-hub/database.db", help="Database file path")
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
@click.option("--db-path", default="~/.photo-hub/database.db", help="Database file path")
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


@cli.command()
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--init", is_flag=True, help="Initialize configuration file with defaults")
@click.option("--set", nargs=2, multiple=True, help="Set configuration value (e.g., --set model gemini-2.0-flash)")
@click.option("--file", default=None, help="Configuration file path (default: auto-detect)")
def config(show, init, set, file):
    """Manage photo-hub configuration."""
    try:
        from photo_hub.web.config import WebConfig
    except ImportError as e:
        click.echo("Error: Web dependencies are not installed.", err=True)
        click.echo("Install them with: pip install photo-hub[web]", err=True)
        click.echo(f"Detailed error: {e}", err=True)
        sys.exit(1)
    
    # Load config
    config_obj = WebConfig.load_from_file(Path(file) if file else None)
    
    if init:
        # Initialize with defaults
        default_config = WebConfig()
        config_path = default_config.get_config_path(file)
        default_config.save_to_file(config_path)
        click.echo(f"Initialized configuration file at {config_path}")
        click.echo("Default configuration:")
        click.echo(json.dumps(default_config.to_dict(), indent=2))
        return
    
    if set:
        # Update configuration values
        config_dict = config_obj.to_dict()
        for key, value in set:
            if key in config_dict:
                # Convert value to appropriate type
                if key == "db_path":
                    config_obj.db_path = value
                elif key == "model":
                    config_obj.model = value
                elif key == "language":
                    config_obj.language = value
                elif key == "max_concurrent":
                    config_obj.max_concurrent = int(value)
                elif key == "batch_size":
                    config_obj.batch_size = int(value)
                else:
                    click.echo(f"Warning: Unknown configuration key '{key}'", err=True)
            else:
                click.echo(f"Warning: Unknown configuration key '{key}'", err=True)
        
        # Save updated config
        config_path = config_obj.get_config_path(file)
        config_obj.save_to_file(config_path)
        click.echo(f"Updated configuration saved to {config_path}")
    
    # Show configuration
    if show or (not init and not set):
        config_path = config_obj.get_config_path(file)
        click.echo(f"Configuration file: {config_path}")
        click.echo("Current configuration:")
        click.echo(json.dumps(config_obj.to_dict(), indent=2))
        click.echo("\nNote: API keys should be set via environment variables:")
        click.echo("  For Gemini: export GOOGLE_API_KEY='your-key'")
        click.echo("  For Qwen: export QWEN_API_KEY='your-key'")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the web server to")
@click.option("--port", default=8000, help="Port to run the web server on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def web(host, port, reload):
    """Launch the photo-hub web interface."""
    try:
        from photo_hub.web import app
        import uvicorn
    except ImportError as e:
        click.echo("Error: Web dependencies are not installed.", err=True)
        click.echo("Install them with: pip install photo-hub[web]", err=True)
        click.echo(f"Detailed error: {e}", err=True)
        sys.exit(1)
    
    click.echo(f"Starting photo-hub web server on http://{host}:{port}")
    click.echo("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"Fatal error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()