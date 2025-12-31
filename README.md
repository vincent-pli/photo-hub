# opencode-testing

A Python application for testing opencode functionality.

## Features

- Modern Python project structure with `src` layout
- CLI interface for easy usage
- Comprehensive test suite with pytest
- Documentation with Sphinx
- MIT licensed

## Installation

### Using pip (from source)

```bash
git clone <repository-url>
cd opencode-testing
pip install -e .
```

### Development setup

```bash
git clone <repository-url>
cd opencode-testing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Usage

### Command line interface

After installation, you can use the `opencode-testing` command:

```bash
opencode-testing --help
opencode-testing run <options>
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
opencode-testing/
├── src/opencode_testing/     # Source code
├── tests/                    # Test files
├── docs/                     # Documentation
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── LICENSE                  # MIT License
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.