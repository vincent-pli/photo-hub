# photo-hub

AI-powered photo management and search tool.

## Features

### Core Features
- **AI-powered photo analysis**: Automatically analyze photo content using Gemini AI or Qwen AI
- **Natural language search**: Search photos by description, tags, objects, or locations using English or Chinese keywords
- **Multi-model support**: Extensible architecture supporting Gemini, Qwen, and other LLM backends
- **Smart scanning**: Skip already analyzed photos, recursive directory scanning, incremental updates

### Web Interface
- **Modern responsive UI**: Clean, intuitive interface for photo management
- **Real-time progress tracking**: Live updates during scanning and analysis
- **Interactive search**: Instant search results with photo previews
- **Multi-language support (i18n)**: Full English/中文 interface with real-time language switching
- **Database statistics**: Visual dashboard with photo counts and analysis metrics
- **RESTful API**: Complete API for integration and automation

### Configuration & Management
- **Hierarchical configuration**: User, project, and default configuration layers
- **CLI configuration management**: Dedicated `config` command for easy settings management
- **Secure API key handling**: Environment variables for API keys (never stored in config files)
- **Flexible database storage**: SQLite-based metadata storage with customizable location

### Technical Features
- **Modern Python architecture**: Clean `src` layout with type hints and best practices
- **FastAPI web framework**: High-performance async web server with automatic API documentation
- **Comprehensive testing**: pytest test suite with coverage reporting
- **Full documentation**: Sphinx-generated documentation with examples
- **MIT licensed**: Open source with permissive licensing

## Installation

### Using pip (from source)

```bash
git clone <repository-url>
cd photo-hub
pip install -e .
```

### Installing photo search features

The photo search functionality requires additional dependencies. Install them with:

```bash
pip install photo-hub[photo]
```

This will install:
- `pillow>=10.0` - Image processing
- `google-genai>=1.0` - Gemini AI integration (for Gemini models)
- `openai>=1.0` - Qwen AI integration (for Qwen models via OpenAI-compatible API)
- `sqlalchemy>=2.0` - Database storage

Or install all dependencies (including development tools):

```bash
pip install photo-hub[photo,dev]
```

### Installing web interface features

For the web interface, additional dependencies are required:

```bash
# Install with web interface support
pip install photo-hub[photo,web]

# Or install everything (photo search, web interface, and dev tools)
pip install photo-hub[photo,web,dev]
```

Web interface dependencies include:
- `fastapi>=0.104.0` - Modern web framework
- `uvicorn>=0.24.0` - ASGI server
- `jinja2>=3.1.0` - Template engine (for future enhancements)

**Note**: If you get "Missing dependencies" errors when using AI models, make sure you've installed the `[photo]` extras. For web interface, install `[web]` extras.

You'll need an API key for the AI service you want to use:

- For Gemini AI: Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- For Qwen AI: Get an API key from [DashScope](https://dashscope.aliyun.com/) (Alibaba Cloud)

Set the appropriate environment variable:
```bash
# For Gemini
export GOOGLE_API_KEY="your-google-api-key"

# For Qwen
export QWEN_API_KEY="your-qwen-api-key"
```

### Development setup

```bash
git clone <repository-url>
cd photo-hub
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Quick Start

Get started with AI-powered photo search in minutes:

### Step 1: Install with photo search features

```bash
# Install the package with photo search dependencies
pip install photo-hub[photo]
```

### Step 2: Set up your API key

Choose your AI service:

#### Option A: Gemini AI (Google)
```bash
# Set your Google AI Studio API key as an environment variable
export GOOGLE_API_KEY="your-api-key-here"
```

#### Option B: Qwen AI (Alibaba Cloud)
```bash
# Set your DashScope API key as an environment variable
export QWEN_API_KEY="your-api-key-here"
```

> **Note**: 
> - Get a free Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
> - Get a Qwen API key from [DashScope](https://dashscope.aliyun.com/)

> **Testing without API key**: Use `--mock` flag for testing without real API calls

> **Cost considerations**: Gemini Pro Vision offers free usage (2 requests/minute). Beyond that, pricing is $0.0025 per image. Use `--skip-existing` to avoid re-analyzing photos.

### Step 3: Test the installation

```bash
# Check available commands
photo-hub --help

# Check photo search commands
photo-hub photos --help
```

### Step 4: Scan and analyze your photos

```bash
# Scan a directory and analyze photos with AI models (default: Gemini)
photo-hub photos scan ~/Pictures --recursive

# Use Qwen model instead
photo-hub photos scan ~/Pictures --recursive --model qwen-max --api-key $QWEN_API_KEY

# Use --skip-existing to avoid re-analyzing already processed photos
photo-hub photos scan ~/Pictures --recursive --skip-existing
```

### Step 5: Search for photos

```bash
# Search by keywords (searches in descriptions, tags, locations, etc.)
photo-hub photos search "beach sunset"
photo-hub photos search "birthday party"
photo-hub photos search "mountain hiking"
photo-hub photos search "office work"
```

### Step 6: Check database status

```bash
# View statistics about your photo database
photo-hub photos stats
```

### Step 7: Advanced usage

```bash
# Use a mock analyzer for testing (no API calls required)
photo-hub photos scan ~/Pictures --mock

# Specify a custom database location
photo-hub photos scan ~/Pictures --db-path custom_photos.db

# Search with JSON output format
photo-hub photos search "beach" --output-format json

# Get detailed verbose output
photo-hub photos scan ~/Pictures --verbose
```

### Complete Example: End-to-end workflow

Here's a complete example showing how to analyze and search photos:

```bash
# 1. Install the package
pip install photo-hub[photo]

# 2. Set API key (or use --mock for testing)
export GOOGLE_API_KEY="your-actual-api-key"

# 3. Scan your photos directory
photo-hub photos scan ~/VacationPhotos --recursive --skip-existing

# 4. Search for specific memories
photo-hub photos search "beach sunset"
photo-hub photos search "family dinner"
photo-hub photos search "mountain hike"

# 5. Check what's in your database
photo-hub photos stats

# 6. Search with advanced options
photo-hub photos search "ocean" --limit 5 --output-format json
```

 **Expected output for search command:**
```
Searching for: 'beach sunset'
Found 3 results:

1. sunset_beach_2023.jpg
   Path: /Users/you/VacationPhotos/sunset_beach_2023.jpg
   Description: A beautiful sunset over the ocean with golden reflections on the water...
   Tags: sunset, beach, ocean, evening, vacation, golden hour

2. family_beach_day.jpg
   Path: /Users/you/VacationPhotos/family_beach_day.jpg
   Description: Family playing on the beach during sunset...
   Tags: family, beach, sunset, playing, sand, children

3. beach_sunset_panorama.jpg
   Path: /Users/you/VacationPhotos/beach_sunset_panorama.jpg
   Description: Panoramic view of beach during sunset...
   Tags: panorama, beach, sunset, wide angle, scenic
```

### Web Interface Quick Start

Get started with the modern web interface in 5 minutes:

```bash
# 1. Install the package (if not already installed)
pip install -e .

# 2. Set your API key (optional, but needed for real AI analysis)
export GOOGLE_API_KEY="your-google-api-key"

# 3. Start the web server
python run_server.py

# Server will start on http://localhost:8000
# Access the interface at: http://localhost:8000/static/index.html
```

**Web Interface Steps:**
1. **Open browser**: Go to `http://localhost:8000/static/index.html`
2. **Select language**: Choose English or 中文 from top-right dropdown
3. **Scan photos**: 
   - Go to "Scan Photos" tab
   - Enter directory path (e.g., `~/Pictures`)
   - Click "Start Scan"
   - Watch real-time progress
4. **Search photos**:
   - Go to "Search Photos" tab
   - Enter keywords (e.g., "温暖" or "beach")
   - View results with descriptions and tags
5. **Check statistics**:
   - Go to "Statistics" tab
   - View photo counts and analysis data

**Configuration Management via CLI:**
```bash
# Check current configuration
photo-hub config --show

# Change AI model
photo-hub config --set model gemini-2.0-flash

# Set preferred language for analysis
photo-hub config --set language zh

# Restart web server after configuration changes
```

## Usage

### Command line interface

After installation, you can use the `photo-hub` command:

```bash
photo-hub --help
photo-hub run <options>
```

### Photo Search Commands Reference

For detailed usage information, see the command help:

```bash
# Get help for all photo commands
photo-hub photos --help

# Get help for specific commands
photo-hub photos scan --help
photo-hub photos search --help
photo-hub photos stats --help
```

#### `photos scan` - Scan and analyze photos
```bash
# Basic usage
photo-hub photos scan /path/to/photos --api-key YOUR_API_KEY

# Common options
photo-hub photos scan /path/to/photos --recursive  # Scan subdirectories
photo-hub photos scan /path/to/photos --skip-existing  # Skip already analyzed photos
photo-hub photos scan /path/to/photos --db-path custom.db  # Custom database file
photo-hub photos scan /path/to/photos --mock  # Use mock analyzer (no API calls)
```

#### `photos search` - Search analyzed photos
```bash
# Basic search
photo-hub photos search "query"

# With options
photo-hub photos search "beach" --limit 10  # Limit results
photo-hub photos search "mountain" --output-format json  # JSON output
```

#### `photos stats` - View database statistics
```bash
# Show statistics
photo-hub photos stats
photo-hub photos stats --db-path custom.db  # Custom database
```

### Python API

```python
from opencode_testing import main

# Use the application
result = main.run()
```

## Development

### Running tests

```bash
pytest
```

### Building documentation

```bash
cd docs
make html
```

### Code formatting

The project uses black for code formatting:

```bash
black src/ tests/
```

## Project Structure

```
photo-hub/
├── src/photo_hub/           # Main source code
│   ├── __init__.py
│   ├── cli.py               # CLI interface with config management
│   ├── __main__.py          # Entry point for CLI
│   ├── photo_search/        # AI-powered photo search module
│   │   ├── __init__.py
│   │   ├── models.py        # Data models (PhotoMetadata, etc.)
│   │   ├── scanner.py       # Photo directory scanner
│   │   ├── gemini_client.py # Gemini AI integration
│   │   ├── qwen_client.py   # Qwen AI integration
│   │   ├── metadata_store.py # SQLite database storage
│   │   ├── factory.py       # Analyzer factory pattern
│   │   └── config.py        # Photo search configuration
│   └── web/                 # Web interface module
│       ├── __init__.py
│       ├── api.py           # FastAPI REST endpoints
│       ├── config.py        # Web configuration system
│       └── static/          # Frontend static files
│           ├── index.html   # Main HTML interface
│           ├── css/style.css # Styling
│           ├── js/app.js    # Frontend application logic
│           ├── js/i18n.js   # Internationalization library
│           └── i18n/        # Translation files
│               ├── en.json  # English translations
│               └── zh.json  # Chinese translations
├── tests/                   # Test suite
├── docs/                    # Documentation (Sphinx)
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # This file
├── LICENSE                 # MIT License
├── run_server.py           # Convenience script to start web server
└── config.json             # Example configuration file
```

## Web Interface

photo-hub includes a modern, responsive web interface with full i18n (internationalization) support for easy photo management.

### Starting the Web Server

```bash
# Start the web server directly
python run_server.py

# Or install and use the CLI command
pip install -e .
photo-hub web
```

The web interface will be available at **http://localhost:8000/static/index.html**. You can also access the API documentation at **http://localhost:8000/docs**.

### Web Interface Features

- **Multi-language support**: Full English/中文 interface with real-time language switching
- **Visual photo scanning**: Select directories and scan photos through the browser
- **Real-time progress tracking**: Monitor scan and analysis progress with live updates
- **Interactive search**: Search photos by description, tags, or content with instant results
- **Photo preview**: View analyzed photos with AI-generated descriptions and tags
- **Database statistics**: View photo counts, analysis statistics, and model usage
- **Recent scans history**: Track previous scan tasks with their status and results
- **Responsive design**: Works on desktop and mobile devices

### Using the Web Interface

1. **Access the interface**: Open http://localhost:8000/static/index.html in your browser
2. **Select language**: Use the language selector in the top-right corner (English/中文)
3. **Scan photos**:
   - Go to the "Scan Photos" tab
   - Enter a directory path (e.g., `~/Pictures` or `/Users/username/Photos`)
   - Configure options: recursive scanning, skip existing photos
   - Click "Start Scan" and monitor progress in real-time
4. **Search photos**:
   - Go to the "Search Photos" tab  
   - Enter keywords in English or Chinese (e.g., "beach sunset" or "温暖")
   - View search results with photo descriptions and tags
5. **View statistics**:
   - Go to the "Statistics" tab
   - See total photos analyzed, models used, and database information

### Web API Endpoints

The web server provides these REST API endpoints:
- `GET /api/health` - Server health check
- `POST /api/scan` - Start photo scanning task
- `GET /api/scan/{task_id}` - Get scan task status
- `GET /api/scan` - List recent scan tasks
- `POST /api/search` - Search photos by keywords
- `GET /api/stats` - Get database statistics

## Configuration System

photo-hub uses a hierarchical configuration system with multiple configuration sources and a dedicated CLI for management.

### Configuration File Locations

Configuration is loaded from these locations (in order of priority):

1. **User configuration**: `~/.photo-hub/config.json` (highest priority, user-specific)
2. **Project configuration**: `./config.json` (current working directory, project-specific)  
3. **Default configuration**: Built-in defaults (lowest priority)

### Configuration Options

| Option | Description | Default | Valid Values |
|--------|-------------|---------|--------------|
| `db_path` | Database file path | `~/.photo-hub/database.db` | Any valid file path |
| `model` | AI model for photo analysis | `gemini-2.0-flash-exp` | `gemini-2.0-flash-exp`, `qwen3-vl-flash`, `qwen-max`, etc. |
| `language` | Language for AI analysis | `auto` (auto-detect) | `en`, `zh`, `auto` |
| `skip_existing` | Skip already analyzed photos | `true` | `true`, `false` |

### Managing Configuration with CLI

Use the `photo-hub config` command to manage configuration:

```bash
# Show current configuration with API key status
photo-hub config --show

# Initialize a new configuration file with defaults
photo-hub config --init

# Set specific configuration values
photo-hub config --set model gemini-2.0-flash --set language en

# Set multiple values at once
photo-hub config --set model qwen3-vl-flash --set language zh

# Use a custom configuration file
photo-hub config --file ./my-config.json --show

# Check if configuration is valid
photo-hub config --validate
```

### Configuration Example

Example configuration file (`~/.photo-hub/config.json`):
```json
{
  "db_path": "/Users/username/.photo-hub/database.db",
  "model": "gemini-2.0-flash",
  "language": "zh",
  "skip_existing": true
}
```

### API Keys Security

For security, API keys are **never stored in configuration files**. They must be set as environment variables:

```bash
# For Gemini AI (Google)
export GOOGLE_API_KEY="your-google-api-key-here"

# For Qwen AI (Alibaba Cloud)
export QWEN_API_KEY="your-qwen-api-key-here"

# Check if API keys are configured (shown in config --show)
photo-hub config --show
```

### Internationalization (i18n) Configuration

The web interface supports multiple languages through the i18n system:

- **Automatic detection**: Browser language is automatically detected
- **Manual selection**: Language can be changed via the UI dropdown
- **Persistent preference**: Language preference is saved in browser localStorage
- **Translation files**: Located in `src/photo_hub/web/static/i18n/` (en.json, zh.json)

To add a new language:
1. Create a new JSON file in the i18n directory (e.g., `fr.json`)
2. Add translations for all keys from `en.json`
3. Add the language option to the HTML selector in `index.html`

### API Keys

For security, API keys are not stored in configuration files. Set them as environment variables:

```bash
# Gemini API key
export GOOGLE_API_KEY="your-key"

# Qwen API key  
export QWEN_API_KEY="your-key"
```

## Troubleshooting

### Web Interface Issues

**Problem**: Web interface shows "Static directory not found" or 404 errors
- **Solution**: 
  - Run `python run_server.py` from the project root directory
  - Or install in development mode: `pip install -e .`
  - Ensure static files are included: check `pyproject.toml` includes `include_package_data = true`

**Problem**: Web interface loads but shows "Directory: Unknown" or UI text not translated
- **Solution**: 
  - Clear browser cache and reload the page
  - Check that i18n files (`en.json`, `zh.json`) are present in `src/photo_hub/web/static/i18n/`
  - Verify browser language settings or manually select language from dropdown

**Problem**: API calls fail with connection errors
- **Solution**:
  - Ensure server is running: check `http://localhost:8000/api/health`
  - Verify no other process is using port 8000: `lsof -ti:8000`
  - Restart server: `python run_server.py`

### Configuration Issues

**Problem**: Configuration changes not taking effect
- **Solution**:
  - Check configuration priority: `photo-hub config --show` shows which file is used
  - User config (`~/.photo-hub/config.json`) overrides project config (`./config.json`)
  - Restart web server after changing configuration

**Problem**: API keys not recognized
- **Solution**:
  - API keys must be set as environment variables, not in config files
  - Check if keys are set: `echo $GOOGLE_API_KEY` or `echo $QWEN_API_KEY`
  - Verify in web interface: `photo-hub config --show` shows API key status
  - Reload shell or restart server after setting environment variables

### Scan and Search Issues

**Problem**: Scan starts but no photos are analyzed
- **Solution**:
  - Check directory permissions: ensure readable photo files
  - Verify supported image formats: JPEG, PNG, WebP, etc.
  - Use `--skip-existing false` to force re-analysis of all photos
  - Check server logs for specific errors

**Problem**: Search returns no results
- **Solution**:
  - Ensure photos have been analyzed: check `photo-hub photos stats`
  - Try different keywords in English or Chinese
  - Use broader search terms initially
  - Check database path: ensure using same database as scans

**Problem**: AI analysis fails with API errors
- **Solution**:
  - Verify API keys are valid and have sufficient quota
  - Try different model: `photo-hub config --set model gemini-2.0-flash`
  - Use mock analyzer for testing: add `--mock` flag to CLI scans
  - Check network connectivity to AI service APIs

### Internationalization (i18n) Issues

**Problem**: Language selector not working or text not translating
- **Solution**:
  - Clear browser localStorage: Developer Tools → Application → Storage → Clear
  - Check JavaScript console for i18n loading errors
  - Verify translation files have complete key sets matching `en.json`
  - Ensure all UI elements have `data-i18n` attributes

**Problem**: Mixed languages in interface
- **Solution**:
  - Language detection uses browser preference, can be manually overridden
  - UI preference is saved in localStorage, persists across sessions
  - Some dynamic content (like API error messages) may remain in English

### Performance Issues

**Problem**: Slow photo scanning or analysis
- **Solution**:
  - Use `--skip-existing true` (default) to avoid re-analyzing photos
  - Limit concurrent API calls (rate limiting varies by AI provider)
  - Consider using faster models like `gemini-2.0-flash` vs `gemini-pro-vision`
  - Process smaller directories in batches

**Problem**: High memory or CPU usage
- **Solution**:
  - Large images are resized before analysis to reduce processing load
  - Database operations are optimized with indexes
  - Web server uses async processing for concurrent requests
  - Monitor with system tools to identify bottlenecks

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.