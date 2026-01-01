"""photo-hub - AI-powered photo management and search tool."""

__version__ = "0.1.0"
__author__ = "photo-hub contributors"
__license__ = "MIT"

import sys
from typing import Any, Dict, List, Optional

# Public API
from .main import hello, add, multiply, divide
from .cli import main as cli_main

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "hello",
    "add",
    "multiply",
    "divide",
    "cli_main",
]

# Optional: Initialize logging or configuration
try:
    import logging

    logging.getLogger(__name__).addHandler(logging.NullHandler())
except ImportError:
    pass

# Optional: Configuration dictionary
config: Dict[str, Any] = {
    "debug": False,
    "verbose": False,
    "timeout": 30,
}