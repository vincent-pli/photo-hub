"""Data models for photo metadata and analysis results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import hashlib


@dataclass
class PhotoMetadata:
    """Basic metadata extracted from a photo file."""
    path: str
    filename: str
    size: int  # in bytes
    created_time: datetime
    modified_time: datetime
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    format: Optional[str] = None
    exif_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def file_hash(self) -> str:
        """Calculate MD5 hash of the file for deduplication."""
        return hashlib.md5(self.path.encode()).hexdigest()
    
    @property
    def directory(self) -> str:
        """Get directory containing the photo."""
        return str(Path(self.path).parent)


@dataclass
class AnalysisResult:
    """LLM analysis result for a photo."""
    photo_path: str
    llm_model: str
    description: str  # Scene description
    people: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "photo_path": self.photo_path,
            "llm_model": self.llm_model,
            "description": self.description,
            "people": self.people,
            "locations": self.locations,
            "objects": self.objects,
            "tags": self.tags,
            "generated_at": self.generated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """Create from dictionary."""
        return cls(
            photo_path=data["photo_path"],
            llm_model=data["llm_model"],
            description=data["description"],
            people=data.get("people", []),
            locations=data.get("locations", []),
            objects=data.get("objects", []),
            tags=data.get("tags", []),
            generated_at=datetime.fromisoformat(data["generated_at"]),
        )