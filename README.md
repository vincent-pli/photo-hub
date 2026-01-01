# photo-hub

AI-powered photo management and search tool.

## Features

- Modern Python project structure with `src` layout
- CLI interface for easy usage
- Comprehensive test suite with pytest
- Documentation with Sphinx
- **AI-powered photo search**: Scan directories, analyze photos with Gemini AI, and search by content
- Extensible architecture supporting multiple LLM backends
- SQLite-based metadata storage
- MIT licensed

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

Or install all dependencies (including development tools):

```bash
pip install photo-hub[photo,dev]
```

You'll also need a Google AI Studio API key for Gemini AI. Set it as an environment variable:
```bash
export GOOGLE_API_KEY="your-api-key-here"
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

### Step 2: Set up your Gemini API key

```bash
# Set your Google AI Studio API key as an environment variable
export GOOGLE_API_KEY="your-api-key-here"

# Or use the --api-key option with commands
```

> **Note**: Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

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
# Scan a directory and analyze photos with Gemini AI
photo-hub photos scan ~/Pictures --recursive

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
├── src/opencode_testing/     # Source code
│   ├── __init__.py
│   ├── cli.py               # CLI interface
│   ├── main.py              # Core application logic
│   └── photo_search/        # AI-powered photo search module
│       ├── __init__.py
│       ├── models.py        # Data models
│       ├── scanner.py       # Photo directory scanner
│       ├── gemini_client.py # Gemini AI integration
│       └── metadata_store.py # SQLite storage
├── tests/                    # Test files
├── docs/                     # Documentation
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── LICENSE                  # MIT License
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.