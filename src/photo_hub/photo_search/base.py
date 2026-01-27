"""Base analyzer interface for photo analysis with different AI models."""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
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
    
    async def analyze_photo_async(self, image_path: str, prompt: Optional[str] = None, language: Language = Language.AUTO) -> AnalysisResult:
        """Asynchronously analyze a single photo.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for analysis
            language: Language for analysis (defaults to AUTO, which resolves to English)
            
        Returns:
            AnalysisResult object with analysis results
        """
        # Default implementation falls back to synchronous version
        return self.analyze_photo(image_path, prompt, language)
    
    async def batch_analyze_async(
        self, 
        image_paths: List[str], 
        prompt: Optional[str] = None, 
        language: Language = Language.AUTO,
        max_concurrent: int = 5,
        batch_size: int = 10
    ) -> List[AnalysisResult]:
        """Asynchronously analyze multiple photos with concurrency control.
        
        Args:
            image_paths: List of paths to image files
            prompt: Optional custom prompt for analysis
            language: Language for analysis (defaults to AUTO, which resolves to English)
            max_concurrent: Maximum number of concurrent API calls
            batch_size: Number of photos to process in each batch (for memory management)
            
        Returns:
            List of AnalysisResult objects
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_image(path: str) -> Optional[AnalysisResult]:
            async with semaphore:
                try:
                    return await self.analyze_photo_async(path, prompt, language)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to analyze {path}: {e}")
                    return None
        
        # Process in batches to manage memory
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]
            tasks = [process_image(path) for path in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    continue
                if result is not None:
                    results.append(result)
            
            # Clear batch to free memory
            del batch
            del tasks
        
        return results
    
    def set_rate_limit_delay(self, seconds: float) -> None:
        """Set delay between API calls (for rate limiting).
        
        Args:
            seconds: Delay in seconds between API calls
        """
        # Default implementation does nothing
        pass
    
    def set_concurrency_limit(self, max_concurrent: int) -> None:
        """Set maximum number of concurrent API calls.
        
        Args:
            max_concurrent: Maximum concurrent calls
        """
        # Default implementation does nothing
        pass
    
    def set_batch_size(self, batch_size: int) -> None:
        """Set batch size for processing.
        
        Args:
            batch_size: Number of items to process in each batch
        """
        # Default implementation does nothing
        pass