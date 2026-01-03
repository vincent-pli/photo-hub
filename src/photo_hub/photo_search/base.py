"""Base analyzer interface for photo analysis with different AI models."""

from abc import ABC, abstractmethod
from typing import List, Optional
from .models import AnalysisResult
from .config import Language, resolve_language, get_prompt_for_language


class PhotoAnalyzer(ABC):
    """Abstract base class for photo analyzers."""
    
    @property
    @abstractmethod
    def model(self) -> str:
        """Get the model name used by this analyzer."""
        pass
    
    @abstractmethod
    def analyze_photo(self, image_path: str, prompt: Optional[str] = None, language: Language = Language.AUTO) -> AnalysisResult:
        """Analyze a single photo.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for analysis
            language: Language for analysis (defaults to AUTO, which resolves to English)
            
        Returns:
            AnalysisResult object with analysis results
        """
        pass
    
    @abstractmethod
    def batch_analyze(self, image_paths: List[str], prompt: Optional[str] = None, language: Language = Language.AUTO) -> List[AnalysisResult]:
        """Analyze multiple photos.
        
        Args:
            image_paths: List of paths to image files
            prompt: Optional custom prompt for analysis
            language: Language for analysis (defaults to AUTO, which resolves to English)
            
        Returns:
            List of AnalysisResult objects
        """
        pass
    
    def set_rate_limit_delay(self, seconds: float) -> None:
        """Set delay between API calls (for rate limiting).
        
        Args:
            seconds: Delay in seconds between API calls
        """
        # Default implementation does nothing
        pass