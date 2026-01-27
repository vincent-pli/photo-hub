"""Configuration for photo-hub web API."""

import json
import os
from pathlib import Path
from typing import Optional

# Default configuration for end-users
DEFAULT_DB_PATH = str(Path.home() / ".photo-hub" / "database.db")
DEFAULT_MODEL = "gemini-2.0-flash-exp"  # Use Gemini by default (free tier available)
DEFAULT_LANGUAGE = "auto"
DEFAULT_RECURSIVE = True
DEFAULT_SKIP_EXISTING = True
DEFAULT_MAX_CONCURRENT = 5  # Default concurrent API calls
DEFAULT_BATCH_SIZE = 10  # Default batch size for processing

# Configuration file path
CONFIG_FILE_PATH = Path.home() / ".photo-hub" / "config.json"

# API keys will be loaded from environment variables
# Users can set these if they want to use specific models
ENV_GOOGLE_API_KEY = "GOOGLE_API_KEY"
ENV_QWEN_API_KEY = "QWEN_API_KEY"


class WebConfig:
    """Configuration manager for web application."""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        google_api_key: Optional[str] = None,
        qwen_api_key: Optional[str] = None,
        max_concurrent: Optional[int] = None,
        batch_size: Optional[int] = None,
    ):
        # Expand ~ in db_path if present
        if db_path:
            db_path = os.path.expanduser(db_path)
        self.db_path = db_path or DEFAULT_DB_PATH
        self.model = model or DEFAULT_MODEL
        self.language = language or DEFAULT_LANGUAGE
        self.google_api_key = google_api_key or os.environ.get(ENV_GOOGLE_API_KEY)
        self.qwen_api_key = qwen_api_key or os.environ.get(ENV_QWEN_API_KEY)
        self.max_concurrent = max_concurrent or DEFAULT_MAX_CONCURRENT
        self.batch_size = batch_size or DEFAULT_BATCH_SIZE
        
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "WebConfig":
        """Load configuration from JSON file."""
        if config_path is None:
            config_path = CONFIG_FILE_PATH
        
        if not config_path.exists():
            return cls()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return cls(
                db_path=config_data.get("db_path"),
                model=config_data.get("model"),
                language=config_data.get("language"),
                google_api_key=config_data.get("google_api_key"),
                qwen_api_key=config_data.get("qwen_api_key"),
                max_concurrent=config_data.get("max_concurrent"),
                batch_size=config_data.get("batch_size"),
            )
        except (json.JSONDecodeError, IOError) as e:
            # If config file is invalid, log warning and use defaults
            import logging
            logging.warning(f"Failed to load config file {config_path}: {e}")
            return cls()
    
    def save_to_file(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to JSON file."""
        if config_path is None:
            config_path = CONFIG_FILE_PATH
        
        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            "db_path": self.db_path,
            "model": self.model,
            "language": self.language,
            "max_concurrent": self.max_concurrent,
            "batch_size": self.batch_size,
            # Note: API keys are not saved to config file for security
            # Users should use environment variables
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            import logging
            logging.error(f"Failed to save config file {config_path}: {e}")
    
    def get_api_key(self) -> Optional[str]:
        """Get appropriate API key based on selected model."""
        if self.model.lower().startswith("gemini"):
            return self.google_api_key
        elif self.model.lower().startswith("qwen"):
            return self.qwen_api_key
        return None
    
    def get_base_url(self) -> Optional[str]:
        """Get base URL for API if needed."""
        # For self-hosted or custom endpoints, can be extended later
        return None
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "db_path": self.db_path,
            "model": self.model,
            "language": self.language,
            "max_concurrent": self.max_concurrent,
            "batch_size": self.batch_size,
            "google_api_key_set": bool(self.google_api_key),
            "qwen_api_key_set": bool(self.qwen_api_key),
        }
    
    def get_config_path(self, custom_path: Optional[str] = None) -> Path:
        """Get configuration file path."""
        if custom_path:
            return Path(custom_path)
        return CONFIG_FILE_PATH
    
    @classmethod
    def load_default(cls) -> "WebConfig":
        """Load default configuration."""
        return cls.load_from_file()


def get_default_config() -> WebConfig:
    """Create default configuration for web application."""
    return WebConfig.load_from_file()