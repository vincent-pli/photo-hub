"""Qwen API client for photo analysis using OpenAI-compatible API."""

import asyncio
import base64
import logging
import time
import json
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from PIL import Image
from datetime import datetime

try:
    import openai
    from openai import AsyncOpenAI
    QWEN_AVAILABLE = True
except ImportError:
    QWEN_AVAILABLE = False
    openai = None
    AsyncOpenAI = None

from photo_hub.photo_search.models import AnalysisResult
from photo_hub.photo_search.base import PhotoAnalyzer
from photo_hub.photo_search.config import Language, get_prompt_for_language

logger = logging.getLogger(__name__)

# Default prompt for photo analysis (same as Gemini for consistency)
DEFAULT_PROMPT = """Analyze this photo and provide a detailed description. Include:
1. Main scene description (what is happening in the photo)
2. People (if any): approximate number, age range, activities
3. Locations: indoor/outdoor, specific places if recognizable
4. Objects: main objects in the scene
5. Tags: 5-10 relevant keywords for searching

Return the analysis in this exact JSON format:
{
    "description": "detailed scene description",
    "people": ["person1", "person2", ...],
    "locations": ["location1", "location2", ...],
    "objects": ["object1", "object2", ...],
    "tags": ["tag1", "tag2", ...]
}"""


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts delays based on API responses."""
    
    def __init__(self, initial_delay: float = 1.0, min_delay: float = 0.1, max_delay: float = 60.0):
        self.delay = initial_delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.success_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
        self._lock = asyncio.Lock()
    
    async def wait(self):
        """Wait for the current delay period."""
        await asyncio.sleep(self.delay)
    
    async def adjust_delay(self, success: bool):
        """Adjust delay based on API call success."""
        async with self._lock:
            if success:
                self.success_count += 1
                self.consecutive_errors = 0
                # If we have many successes, reduce delay
                if self.success_count > 10:
                    self.delay = max(self.min_delay, self.delay * 0.9)
                    self.success_count = 0
            else:
                self.error_count += 1
                self.consecutive_errors += 1
                self.success_count = 0
                # Increase delay on errors
                if self.consecutive_errors > 2:
                    self.delay = min(self.max_delay, self.delay * 1.5)
                elif self.consecutive_errors > 0:
                    self.delay = min(self.max_delay, self.delay * 1.2)


class QwenPhotoAnalyzer(PhotoAnalyzer):
    """Analyze photos using Qwen API with OpenAI-compatible interface."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "qwen-max", 
        base_url: Optional[str] = None
    ):
        if not QWEN_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )
        
        self._model = model
        self._rate_limit_delay = 1  # seconds between requests (reasonable default)
        self._max_concurrent = 5
        self._batch_size = 10
        
        # Initialize adaptive rate limiter
        self.rate_limiter = AdaptiveRateLimiter(initial_delay=1.0)
        
        # Configure OpenAI client for Qwen
        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        else:
            # Default Qwen endpoint
            client_kwargs["base_url"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # Add timeout to prevent hanging (30 seconds connect, 60 seconds read)
        client_kwargs["timeout"] = 60.0
        
        # Create both sync and async clients
        if openai:
            self.client = openai.OpenAI(**client_kwargs)  # type: ignore
        else:
            self.client = None
        
        if AsyncOpenAI:
            self.async_client = AsyncOpenAI(**client_kwargs)  # type: ignore
        else:
            self.async_client = None
    
    @property
    def model(self) -> str:
        return self._model
    
    def analyze_photo(self, image_path: str, prompt: Optional[str] = None, language: Language = Language.AUTO) -> AnalysisResult:
        """Analyze a single photo with Qwen."""
        logger.info(f"Analyzing photo with Qwen: {image_path} with language: {language}")
        
        # Load and preprocess image
        image_data = self._load_and_preprocess_image(image_path)
        
        # Get appropriate prompt based on language if no custom prompt provided
        if prompt is None:
            prompt = get_prompt_for_language(language)
        
        try:
            # Check if client is available
            if self.client is None:
                raise ImportError("OpenAI client not available. Please install openai package.")
            
            # Encode image to base64
            img_base64 = self._pil_to_base64(image_data)
            
            # Call Qwen API following official documentation
            # Note: Qwen API may not support all OpenAI parameters like max_tokens, temperature
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]}
                    ]
                    # Removed max_tokens and temperature as they may not be supported by Qwen API
                    # Using default timeout from client configuration
                )
            except Exception as api_error:
                # Try without any extra parameters if the first call fails
                error_msg = str(api_error)
                if "unexpected argument" in error_msg.lower() or "invalid parameter" in error_msg.lower():
                    logger.warning(f"Retrying without extra parameters for {self.model}")
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt or DEFAULT_PROMPT},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                            ]}
                        ]
                    )
                else:
                    raise
            
            # Parse response
            response_text = response.choices[0].message.content
            if response_text is None:
                raise ValueError(f"Qwen API returned empty response for {image_path}")
            
            # Ensure response_text is not None for type checker
            assert response_text is not None
            result = self._parse_response(response_text, image_path)
            
            # Rate limiting
            time.sleep(self._rate_limit_delay)
            
            return result
            
        except Exception as e:
            logger.error(f"Qwen API error for {image_path}: {e}")
            
            # Provide helpful error messages
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                # Provide specific suggestions for common model naming issues
                suggestions = []
                if "vl" in self.model.lower():
                    suggestions = ["qwen-vl-plus", "qwen-vl-max", "qwen-vl-chat"]
                else:
                    suggestions = ["qwen-max", "qwen-turbo", "qwen-plus", "qwen2.5-72b-instruct"]
                
                raise ValueError(
                    f"Model '{self.model}' not found or not supported. "
                    f"Please check the model name. Supported Qwen models include: "
                    f"{', '.join(suggestions)}. "
                    f"See https://help.aliyun.com/zh/model-studio/getting-started/models for full list."
                )
            elif "401" in error_msg or "auth" in error_msg.lower():
                raise ValueError(
                    f"Authentication failed. Please check your API key. "
                    f"Set QWEN_API_KEY or DASHSCOPE_API_KEY environment variable."
                )
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                raise TimeoutError(
                    f"Qwen API call timed out for {image_path}. "
                    f"This could be due to network issues or model availability. "
                    f"Model: {self.model}"
                )
            raise
    
    async def analyze_photo_async(self, image_path: str, prompt: Optional[str] = None, language: Language = Language.AUTO) -> AnalysisResult:
        """Asynchronously analyze a single photo with Qwen."""
        logger.info(f"Analyzing photo asynchronously with Qwen: {image_path} with language: {language}")
        
        # Check if async client is available
        if self.async_client is None:
            # Fall back to synchronous version
            logger.warning("Async client not available, falling back to synchronous analysis")
            return self.analyze_photo(image_path, prompt, language)
        
        # Load and preprocess image
        image_data = self._load_and_preprocess_image(image_path)
        
        # Get appropriate prompt based on language if no custom prompt provided
        if prompt is None:
            prompt = get_prompt_for_language(language)
        
        try:
            # Encode image to base64
            img_base64 = self._pil_to_base64(image_data)
            
            # Call Qwen API asynchronously
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]}
                    ]
                )
            except Exception as api_error:
                # Try without any extra parameters if the first call fails
                error_msg = str(api_error)
                if "unexpected argument" in error_msg.lower() or "invalid parameter" in error_msg.lower():
                    logger.warning(f"Retrying without extra parameters for {self.model}")
                    response = await self.async_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt or DEFAULT_PROMPT},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                            ]}
                        ]
                    )
                else:
                    raise
            
            # Parse response
            response_text = response.choices[0].message.content
            if response_text is None:
                raise ValueError(f"Qwen API returned empty response for {image_path}")
            
            # Ensure response_text is not None for type checker
            assert response_text is not None
            result = self._parse_response(response_text, image_path)
            
            # Adaptive rate limiting
            await self.rate_limiter.wait()
            await self.rate_limiter.adjust_delay(success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Qwen API async error for {image_path}: {e}")
            
            # Update rate limiter on error
            await self.rate_limiter.adjust_delay(success=False)
            
            # Provide helpful error messages
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                suggestions = []
                if "vl" in self.model.lower():
                    suggestions = ["qwen-vl-plus", "qwen-vl-max", "qwen-vl-chat"]
                else:
                    suggestions = ["qwen-max", "qwen-turbo", "qwen-plus", "qwen2.5-72b-instruct"]
                
                raise ValueError(
                    f"Model '{self.model}' not found or not supported. "
                    f"Please check the model name. Supported Qwen models include: "
                    f"{', '.join(suggestions)}"
                )
            elif "401" in error_msg or "auth" in error_msg.lower():
                raise ValueError(
                    f"Authentication failed. Please check your API key."
                )
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                raise TimeoutError(
                    f"Qwen API call timed out for {image_path}. Model: {self.model}"
                )
            raise
    
    def batch_analyze(
        self, 
        image_paths: List[str], 
        prompt: Optional[str] = None,
        language: Language = Language.AUTO
    ) -> List[AnalysisResult]:
        """Analyze multiple photos with rate limiting."""
        results = []
        for i, image_path in enumerate(image_paths):
            try:
                result = self.analyze_photo(image_path, prompt, language)
                results.append(result)
                logger.info(f"Completed {i+1}/{len(image_paths)}: {image_path}")
            except Exception as e:
                logger.error(f"Failed to analyze {image_path}: {e}")
                # Continue with next photo
                continue
        return results
    
    def _load_and_preprocess_image(self, image_path: str) -> Image.Image:
        """Load image and return PIL Image object."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Open with PIL to validate and potentially resize
        try:
            img = Image.open(image_path)
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            
            # Resize if too large (API may have limits)
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Return the image object
            return img
        except Exception as e:
            raise ValueError(f"Failed to load image {image_path}: {e}")
    
    def _pil_to_base64(self, img: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        import io
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def _parse_response(self, response_text: str, image_path: str) -> AnalysisResult:
        """Parse Qwen response into AnalysisResult."""
        # Extract JSON from response (might have markdown code blocks)
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            logger.warning(f"No JSON found in response for {image_path}")
            # Fallback: use entire response as description
            return AnalysisResult(
                photo_path=image_path,
                llm_model=self.model,
                description=response_text.strip(),
                people=[],
                locations=[],
                objects=[],
                tags=[],
                generated_at=datetime.now()
            )
        
        try:
            data = json.loads(json_match.group())
            return AnalysisResult(
                photo_path=image_path,
                llm_model=self.model,
                description=data.get("description", ""),
                people=data.get("people", []),
                locations=data.get("locations", []),
                objects=data.get("objects", []),
                tags=data.get("tags", []),
                generated_at=datetime.now()
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {image_path}: {e}")
            # Fallback
            return AnalysisResult(
                photo_path=image_path,
                llm_model=self.model,
                description=response_text.strip(),
                people=[],
                locations=[],
                objects=[],
                tags=[],
                generated_at=datetime.now()
            )
    
    def set_rate_limit_delay(self, seconds: float) -> None:
        """Set delay between API calls (for rate limiting)."""
        self._rate_limit_delay = seconds
        self.rate_limiter.delay = seconds
    
    def set_concurrency_limit(self, max_concurrent: int) -> None:
        """Set maximum number of concurrent API calls."""
        self._max_concurrent = max_concurrent
    
    def set_batch_size(self, batch_size: int) -> None:
        """Set batch size for processing."""
        self._batch_size = batch_size


# Convenience function
def create_qwen_analyzer(api_key: str, model: str = "qwen-max") -> QwenPhotoAnalyzer:
    """Create a Qwen photo analyzer instance."""
    return QwenPhotoAnalyzer(api_key=api_key, model=model)