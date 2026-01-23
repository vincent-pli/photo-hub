"""photo-hub web interface."""

from .api import app
from .config import WebConfig, get_default_config

__all__ = ["app", "WebConfig", "get_default_config"]