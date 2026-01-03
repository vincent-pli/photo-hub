"""Configuration for multi-language photo analysis."""

from enum import Enum
from typing import Dict


class Language(str, Enum):
    """Supported languages for photo analysis."""
    EN = "en"  # English
    ZH = "zh"  # Chinese
    AUTO = "auto"  # Auto-detect (defaults to English)
    
    @classmethod
    def normalize(cls, language: str) -> "Language":
        """Normalize language string to Language enum."""
        language_lower = language.lower().strip()
        if language_lower in ("en", "english", "eng"):
            return cls.EN
        elif language_lower in ("zh", "chinese", "cn", "zh-cn", "zh_cn"):
            return cls.ZH
        elif language_lower in ("auto", "automatic"):
            return cls.AUTO
        else:
            # Default to English for unknown languages
            return cls.EN


# Default prompt templates for different languages
DEFAULT_PROMPTS: Dict[Language, str] = {
    Language.EN: """Analyze this photo and provide a detailed description. Include:
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
}""",
    
    Language.ZH: """分析这张照片并提供详细描述。包括：
1. 主要场景描述（照片中发生了什么）
2. 人物（如果有）：大致数量、年龄范围、活动
3. 地点：室内/室外、如果可识别则说明具体地点
4. 物体：场景中的主要物体
5. 标签：5-10个相关搜索关键词

请严格按照以下JSON格式返回分析结果：
{
    "description": "详细的场景描述",
    "people": ["人物1", "人物2", ...],
    "locations": ["地点1", "地点2", ...],
    "objects": ["物体1", "物体2", ...],
    "tags": ["标签1", "标签2", ...]
}""",
}


def get_prompt_for_language(language: Language) -> str:
    """Get the default prompt for the specified language.
    
    Args:
        language: Language enum value
        
    Returns:
        Prompt string for the specified language
        
    Raises:
        ValueError: If language is AUTO (should be resolved first)
    """
    if language == Language.AUTO:
        # Default to English for auto detection
        return DEFAULT_PROMPTS[Language.EN]
    
    if language not in DEFAULT_PROMPTS:
        # Fall back to English for unsupported languages
        return DEFAULT_PROMPTS[Language.EN]
    
    return DEFAULT_PROMPTS[language]


def resolve_language(language: Language) -> Language:
    """Resolve AUTO language to a concrete language.
    
    Args:
        language: Language enum value
        
    Returns:
        Resolved language (EN or ZH)
    """
    if language == Language.AUTO:
        # For now, default to English
        # Could be enhanced to detect system language
        return Language.EN
    return language