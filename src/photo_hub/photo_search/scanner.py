"""Photo directory scanner and metadata extractor."""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Iterator, Optional
from PIL import Image, UnidentifiedImageError

from photo_hub.photo_search.models import PhotoMetadata

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}


class PhotoScanner:
    """Scanner for photo directories."""
    
    def __init__(self, recursive: bool = True):
        self.recursive = recursive
        self._stats = {"scanned": 0, "skipped": 0, "errors": 0}
    
    def scan_directory(self, directory: str) -> List[PhotoMetadata]:
        """Scan a directory and return list of photo metadata."""
        directory_path = Path(directory).resolve()
        if not directory_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        photos = []
        for photo_meta in self._scan_directory_iter(directory_path):
            photos.append(photo_meta)
        
        logger.info(
            f"Scan completed: {self._stats['scanned']} scanned, "
            f"{self._stats['skipped']} skipped, {self._stats['errors']} errors"
        )
        return photos
    
    def _scan_directory_iter(self, directory: Path) -> Iterator[PhotoMetadata]:
        """Generator that yields photo metadata from directory."""
        try:
            entries = list(directory.iterdir())
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")
            return
        
        for entry in entries:
            if entry.is_dir() and self.recursive:
                yield from self._scan_directory_iter(entry)
            elif entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    photo_meta = self._extract_metadata(entry)
                    if photo_meta:
                        self._stats["scanned"] += 1
                        yield photo_meta
                    else:
                        self._stats["skipped"] += 1
                except Exception as e:
                    logger.error(f"Error processing {entry}: {e}")
                    self._stats["errors"] += 1
    
    def _extract_metadata(self, file_path: Path) -> Optional[PhotoMetadata]:
        """Extract metadata from a single photo file."""
        try:
            # Basic file stats
            stat = file_path.stat()
            size = stat.st_size
            
            # Image-specific metadata
            width, height, format = None, None, None
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    format = img.format
                    # Try to get EXIF data if available
                    exif_data = {}
                    if hasattr(img, '_getexif') and img._getexif():
                        exif_data = img._getexif()
            except UnidentifiedImageError:
                logger.debug(f"Not a valid image file: {file_path}")
                return None
            
            return PhotoMetadata(
                path=str(file_path.resolve()),
                filename=file_path.name,
                size=size,
                created_time=datetime.fromtimestamp(stat.st_ctime),
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                image_width=width,
                image_height=height,
                format=format,
                exif_data=exif_data if exif_data else {},
            )
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            return None
    
    def get_stats(self) -> dict:
        """Get scanning statistics."""
        return self._stats.copy()


def scan_photos(directory: str, recursive: bool = True) -> List[PhotoMetadata]:
    """Convenience function to scan photos in a directory."""
    scanner = PhotoScanner(recursive=recursive)
    return scanner.scan_directory(directory)