"""Factory for creating photo analyzers based on model names."""

import re
import logging
from typing import Optional, Dict, Any
from .base import PhotoAnalyzer


def create_analyzer(
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> PhotoAnalyzer:
    """Create a photo analyzer based on the model name.
    
    Args:
        model: Model identifier (e.g., "gemini-2.0-flash-exp", "qwen-max", "mock")
        api_key: API key for the service (if required)
        base_url: Custom base URL for API (for self-hosted or custom endpoints)
        **kwargs: Additional arguments passed to the analyzer constructor
    
    Returns:
        PhotoAnalyzer instance
        
    Raises:
        ValueError: If model is not recognized or required parameters are missing
        ImportError: If required dependencies are not installed
    """
    model_lower = model.lower()
    
    # Check for mock analyzer
    if model_lower.startswith("mock"):
        from .gemini_client_new import MockPhotoAnalyzer
        return MockPhotoAnalyzer(model=model)
    
    # Check for Gemini models
    if model_lower.startswith("gemini"):
        from .gemini_client_new import GeminiPhotoAnalyzer
        if not api_key:
            # Try to get from environment variable
            import os
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "API key required for Gemini models. "
                    "Provide --api-key or set GOOGLE_API_KEY environment variable."
                )
        return GeminiPhotoAnalyzer(api_key=api_key, model=model, **kwargs)
    
    # Check for Qwen models
    if model_lower.startswith("qwen"):
        from .qwen_client import QwenPhotoAnalyzer
        if not api_key:
            # Try to get from environment variable
            import os
            api_key = os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError(
                    "API key required for Qwen models. "
                    "Provide --api-key or set QWEN_API_KEY/DASHSCOPE_API_KEY environment variable."
                )
        
        # Provide helpful hints for VL models
        if "vl" in model_lower and model_lower not in ["qwen-vl-plus", "qwen-vl-max", "qwen-vl-chat"]:
            logger = logging.getLogger(__name__)
            logger.info(
                f"Note: Using Qwen VL model '{model}'. "
                f"For vision-language tasks, recommended models are: "
                f"qwen-vl-plus, qwen-vl-max, qwen-vl-chat"
            )
        
        return QwenPhotoAnalyzer(api_key=api_key, model=model, base_url=base_url, **kwargs)
    
    # Try to infer from common patterns
    if "gpt" in model_lower or "openai" in model_lower:
        raise ValueError(
            f"OpenAI models not yet supported. Model: {model}"
        )
    
    raise ValueError(
        f"Unrecognized model: {model}. "
        f"Supported models: gemini-*, qwen-*, mock\n"
        f"Qwen examples: qwen-max, qwen-turbo, qwen-plus, qwen-vl-plus, qwen-vl-max, qwen3-vl-flash\n"
        f"Gemini examples: gemini-2.0-flash-exp, gemini-flash-latest, gemini-2.5-flash"
    )