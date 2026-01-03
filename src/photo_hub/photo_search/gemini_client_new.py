"""Gemini API client for photo analysis using the new google.genai library."""

import base64
import logging
import time
import json
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from PIL import Image
import io
from datetime import datetime

try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from photo_hub.photo_search.models import AnalysisResult
from photo_hub.photo_search.base import PhotoAnalyzer
from photo_hub.photo_search.config import Language, get_prompt_for_language, resolve_language

logger = logging.getLogger(__name__)

# Default prompt for photo analysis
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


class GeminiPhotoAnalyzer(PhotoAnalyzer):
    """Analyze photos using Gemini API with the new google.genai library."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google.genai not installed. "
                "Install with: pip install google-genai"
            )
        
        self.client = genai.Client(api_key=api_key)  # type: ignore
        self._model = model
        self._rate_limit_delay = 30  # seconds between requests (for free tier)
    
    @property
    def model(self) -> str:
        return self._model
        
    def analyze_photo(self, image_path: str, prompt: Optional[str] = None, language: Language = Language.AUTO) -> AnalysisResult:
        """Analyze a single photo with Gemini."""
        logger.info(f"Analyzing photo: {image_path} with language: {language}")
        
        # Load and preprocess image
        image_data = self._load_and_preprocess_image(image_path)
        
        # Get appropriate prompt based on language if no custom prompt provided
        if prompt is None:
            prompt = get_prompt_for_language(language)
        
        try:
            # Call Gemini API with the new library
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, image_data]
            )
            
            # Parse response
            response_text = response.text
            if response_text is None:
                raise ValueError(f"Gemini API returned empty response for {image_path}")
            result = self._parse_response(response_text, image_path)
            
            # Rate limiting for free tier
            time.sleep(self._rate_limit_delay)
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error for {image_path}: {e}")
            
            # Provide more helpful error message for model not found
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower() or "not supported" in error_msg.lower():
                # Try to get list of available models
                try:
                    models = self.client.models.list()
                    # Extract model IDs (remove 'models/' prefix) and filter for generateContent support
                    available_models = []
                    for m in models:
                        # Check if model supports generateContent (may be in supported_actions or supported_methods)
                        supports_generate = False
                        if hasattr(m, 'supported_actions') and 'generateContent' in m.supported_actions:
                            supports_generate = True
                        elif hasattr(m, 'supported_methods') and 'generateContent' in m.supported_methods:
                            supports_generate = True
                        elif hasattr(m, 'capabilities') and 'generateContent' in m.capabilities:
                            supports_generate = True
                        # Also include any model with 'gemini' in name (fallback)
                        elif 'gemini' in m.name.lower():
                            supports_generate = True
                            
                        if supports_generate:
                            model_id = m.name.replace('models/', '')
                            # Filter out embedding models
                            if 'embedding' not in model_id.lower():
                                available_models.append(model_id)
                    
                    # Remove duplicates and the current failed model
                    available_models = list(set(available_models))
                    if self.model in available_models:
                        available_models.remove(self.model)
                    
                    # Sort to put more recent/better models first
                    available_models.sort()
                    suggested = available_models[:5] if available_models else ["gemini-2.0-flash-exp", "gemini-flash-latest", "gemini-2.5-flash"]
                except Exception as list_error:
                    logger.debug(f"Failed to list models: {list_error}")
                    suggested = ["gemini-2.0-flash-exp", "gemini-flash-latest", "gemini-2.5-flash"]
                
                raise ValueError(
                    f"Model '{self.model}' not found or not supported. "
                    f"Please try one of: {', '.join(suggested)}. "
                    f"Use --model flag to specify a different model. "
                    f"Original error: {error_msg}"
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
            
            # Resize if too large (Gemini has limits)
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Return the image object
            return img
        except Exception as e:
            raise ValueError(f"Failed to load image {image_path}: {e}")
    
    def _parse_response(self, response_text: str, image_path: str) -> AnalysisResult:
        """Parse Gemini response into AnalysisResult."""
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
    
    def set_rate_limit_delay(self, seconds: float):
        """Set delay between API calls (for rate limiting)."""
        self._rate_limit_delay = seconds


# Convenience function
def create_analyzer(api_key: str) -> GeminiPhotoAnalyzer:
    """Create a Gemini photo analyzer instance."""
    return GeminiPhotoAnalyzer(api_key=api_key)


class MockPhotoAnalyzer(PhotoAnalyzer):
    """Mock analyzer for testing without real API calls."""
    
    def __init__(self, model: str = "mock-gemini"):
        self._model = model
        self._mock_responses_en = {
            "warm.jpeg": {
                "description": "A warm and cozy indoor scene with soft lighting",
                "people": ["person sitting", "family member"],
                "locations": ["living room", "home", "indoors"],
                "objects": ["sofa", "lamp", "book", "blanket"],
                "tags": ["cozy", "warm", "home", "comfort", "relaxing"]
            },
            "beach_sunset.jpg": {
                "description": "A beautiful sunset at the beach with golden sand and orange sky",
                "people": ["couple walking", "children playing"],
                "locations": ["beach", "ocean", "shoreline"],
                "objects": ["sun", "waves", "sand", "umbrella"],
                "tags": ["sunset", "beach", "ocean", "evening", "vacation"]
            },
            "mountain_hike.png": {
                "description": "People hiking on a mountain trail with scenic views",
                "people": ["hikers", "tourists"],
                "locations": ["mountain", "trail", "forest"],
                "objects": ["backpack", "trees", "rocks", "sky"],
                "tags": ["hiking", "mountain", "nature", "outdoor", "adventure"]
            },
            "birthday_party.jpeg": {
                "description": "A birthday party celebration with cake and balloons",
                "people": ["family", "friends", "children"],
                "locations": ["living room", "indoors", "home"],
                "objects": ["cake", "balloons", "candles", "gifts"],
                "tags": ["birthday", "party", "celebration", "family", "cake"]
            },
            "office_work.jpg": {
                "description": "People working in a modern office environment",
                "people": ["office workers", "colleagues"],
                "locations": ["office", "workspace", "indoors"],
                "objects": ["computer", "desk", "chair", "monitor"],
                "tags": ["office", "work", "business", "computer", "professional"]
            }
        }
        self._mock_responses_zh = {
            "warm.jpeg": {
                "description": "温暖舒适的室内场景，光线柔和",
                "people": ["坐着的人", "家庭成员"],
                "locations": ["客厅", "家", "室内"],
                "objects": ["沙发", "台灯", "书", "毯子"],
                "tags": ["舒适", "温暖", "家", "放松", "温馨"]
            },
            "beach_sunset.jpg": {
                "description": "海滩上美丽的日落，金色沙滩和橙色的天空",
                "people": ["散步的情侣", "玩耍的孩子们"],
                "locations": ["海滩", "海洋", "海岸线"],
                "objects": ["太阳", "波浪", "沙子", "遮阳伞"],
                "tags": ["日落", "海滩", "海洋", "傍晚", "假期"]
            },
            "mountain_hike.png": {
                "description": "人们在山间小径上徒步，风景优美",
                "people": ["徒步者", "游客"],
                "locations": ["山脉", "小径", "森林"],
                "objects": ["背包", "树木", "岩石", "天空"],
                "tags": ["徒步", "山脉", "自然", "户外", "冒险"]
            },
            "birthday_party.jpeg": {
                "description": "生日派对庆祝，有蛋糕和气球",
                "people": ["家人", "朋友", "孩子们"],
                "locations": ["客厅", "室内", "家"],
                "objects": ["蛋糕", "气球", "蜡烛", "礼物"],
                "tags": ["生日", "派对", "庆祝", "家庭", "蛋糕"]
            },
            "office_work.jpg": {
                "description": "人们在现代办公室环境中工作",
                "people": ["办公室职员", "同事"],
                "locations": ["办公室", "工作区", "室内"],
                "objects": ["电脑", "桌子", "椅子", "显示器"],
                "tags": ["办公室", "工作", "商务", "电脑", "专业"]
            }
        }
    
    @property
    def model(self) -> str:
        return self._model
    
    def analyze_photo(self, image_path: str, prompt: Optional[str] = None, language: Language = Language.AUTO) -> AnalysisResult:
        """Mock analysis based on filename."""
        filename = Path(image_path).name
        
        # Choose response dictionary based on language
        resolved_language = resolve_language(language)
        if resolved_language == Language.ZH:
            responses = self._mock_responses_zh
        else:
            responses = self._mock_responses_en
        
        if filename in responses:
            data = responses[filename]
        else:
            # Default response for unknown files
            if resolved_language == Language.ZH:
                data = {
                    "description": f"一张标题为 {filename} 的照片",
                    "people": [],
                    "locations": ["未知"],
                    "objects": [],
                    "tags": ["照片", "图像"]
                }
            else:
                data = {
                    "description": f"A photo titled {filename}",
                    "people": [],
                    "locations": ["unknown"],
                    "objects": [],
                    "tags": ["photo", "image"]
                }
        
        return AnalysisResult(
            photo_path=image_path,
            llm_model=self.model,
            description=data["description"],
            people=data["people"],
            locations=data["locations"],
            objects=data["objects"],
            tags=data["tags"],
            generated_at=datetime.now()
        )
    
    def batch_analyze(self, image_paths: List[str], prompt: Optional[str] = None, language: Language = Language.AUTO) -> List[AnalysisResult]:
        """Mock batch analysis."""
        return [self.analyze_photo(path, prompt, language) for path in image_paths]
    
    def set_rate_limit_delay(self, seconds: float):
        """Mock method for compatibility."""
        pass


# Convenience function for mock analyzer
def create_mock_analyzer() -> MockPhotoAnalyzer:
    """Create a mock photo analyzer for testing."""
    return MockPhotoAnalyzer()