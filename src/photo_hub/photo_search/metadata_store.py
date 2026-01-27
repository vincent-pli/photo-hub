"""Metadata storage for photos and analysis results."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import sqlite3

from photo_hub.photo_search.models import PhotoMetadata, AnalysisResult

logger = logging.getLogger(__name__)


class MetadataStore:
    """SQLite-based storage for photo metadata and analysis results."""
    
    def __init__(self, db_path: str = "photo_search.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Photos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    created_time TIMESTAMP NOT NULL,
                    modified_time TIMESTAMP NOT NULL,
                    image_width INTEGER,
                    image_height INTEGER,
                    format TEXT,
                    exif_data TEXT,
                    file_hash TEXT NOT NULL,
                    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    photo_id INTEGER NOT NULL,
                    llm_model TEXT NOT NULL,
                    description TEXT NOT NULL,
                    people TEXT,  -- JSON array
                    locations TEXT,  -- JSON array
                    objects TEXT,  -- JSON array
                    tags TEXT,  -- JSON array
                    generated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (photo_id) REFERENCES photos (id) ON DELETE CASCADE,
                    UNIQUE(photo_id, llm_model)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_path ON photos(path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_hash ON photos(file_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_photo ON analysis_results(photo_id)")
            
            conn.commit()
    
    def save_photo_metadata(self, metadata: PhotoMetadata) -> int:
        """Save photo metadata, return photo ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if photo already exists
            cursor.execute(
                "SELECT id FROM photos WHERE path = ? OR file_hash = ?",
                (metadata.path, metadata.file_hash)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE photos SET
                        filename = ?,
                        size = ?,
                        created_time = ?,
                        modified_time = ?,
                        image_width = ?,
                        image_height = ?,
                        format = ?,
                        exif_data = ?,
                        scanned_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    metadata.filename,
                    metadata.size,
                    metadata.created_time.isoformat(),
                    metadata.modified_time.isoformat(),
                    metadata.image_width,
                    metadata.image_height,
                    metadata.format,
                    json.dumps(metadata.exif_data),
                    existing[0]
                ))
                return existing[0]
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO photos (
                        path, filename, size, created_time, modified_time,
                        image_width, image_height, format, exif_data, file_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.path,
                    metadata.filename,
                    metadata.size,
                    metadata.created_time.isoformat(),
                    metadata.modified_time.isoformat(),
                    metadata.image_width,
                    metadata.image_height,
                    metadata.format,
                    json.dumps(metadata.exif_data),
                    metadata.file_hash,
                ))
                lastrowid = cursor.lastrowid
                if lastrowid is None:
                    raise ValueError("Failed to get last insert ID")
                return lastrowid
    
    def save_analysis_result(self, result: AnalysisResult) -> int:
        """Save analysis result, return result ID."""
        # First ensure photo exists
        photo_id = self.save_photo_metadata_from_path(result.photo_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if analysis already exists for this photo and model
            cursor.execute(
                "SELECT id FROM analysis_results WHERE photo_id = ? AND llm_model = ?",
                (photo_id, result.llm_model)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing analysis
                cursor.execute("""
                    UPDATE analysis_results SET
                        description = ?,
                        people = ?,
                        locations = ?,
                        objects = ?,
                        tags = ?,
                        generated_at = ?
                    WHERE id = ?
                """, (
                    result.description,
                    json.dumps(result.people),
                    json.dumps(result.locations),
                    json.dumps(result.objects),
                    json.dumps(result.tags),
                    result.generated_at.isoformat(),
                    existing[0]
                ))
                return existing[0]
            else:
                # Insert new analysis
                cursor.execute("""
                    INSERT INTO analysis_results (
                        photo_id, llm_model, description,
                        people, locations, objects, tags, generated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    photo_id,
                    result.llm_model,
                    result.description,
                    json.dumps(result.people),
                    json.dumps(result.locations),
                    json.dumps(result.objects),
                    json.dumps(result.tags),
                    result.generated_at.isoformat(),
                ))
                lastrowid = cursor.lastrowid
                if lastrowid is None:
                    raise ValueError("Failed to get last insert ID")
                return lastrowid
    
    async def save_analysis_result_batch(self, result: AnalysisResult) -> None:
        """Save analysis result to batch for later bulk insert."""
        # This is a no-op in the base class, overridden in BatchMetadataStore
        # We still save it immediately for backward compatibility
        self.save_analysis_result(result)
    
    async def flush_batch(self) -> None:
        """Flush any pending batch writes."""
        # No-op in base class
        pass
    
    def save_photo_metadata_from_path(self, photo_path: str) -> int:
        """Save basic photo metadata from file path."""
        from photo_hub.photo_search.scanner import PhotoScanner
        
        scanner = PhotoScanner(recursive=False)
        metadata = scanner._extract_metadata(Path(photo_path))
        if metadata:
            return self.save_photo_metadata(metadata)
        else:
            raise ValueError(f"Could not extract metadata from {photo_path}")
    
    def get_photo_metadata(self, photo_path: str) -> Optional[PhotoMetadata]:
        """Get photo metadata by path."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM photos WHERE path = ?", (photo_path,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_photo_metadata(row)
            return None
    
    def get_analysis_result(self, photo_path: str, llm_model: str) -> Optional[AnalysisResult]:
        """Get analysis result for a photo."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ar.*, p.path 
                FROM analysis_results ar
                JOIN photos p ON ar.photo_id = p.id
                WHERE p.path = ? AND ar.llm_model = ?
            """, (photo_path, llm_model))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_analysis_result(row)
            return None
    
    def search_photos(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search photos by keywords in analysis results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT p.*, ar.description, ar.tags
                FROM photos p
                LEFT JOIN analysis_results ar ON p.id = ar.photo_id
                WHERE ar.description LIKE ? 
                   OR ar.people LIKE ?
                   OR ar.locations LIKE ?
                   OR ar.objects LIKE ?
                   OR ar.tags LIKE ?
                ORDER BY p.modified_time DESC
                LIMIT ?
            """, (search_term, search_term, search_term, search_term, search_term, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                for field in ["people", "locations", "objects", "tags"]:
                    if result.get(field):
                        result[field] = json.loads(result[field])
                results.append(result)
            
            return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            cursor.execute("SELECT COUNT(*) FROM photos")
            stats["total_photos"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM analysis_results")
            stats["total_analyses"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT llm_model) FROM analysis_results")
            stats["models_used"] = cursor.fetchone()[0]
            
            return stats
    
    def _row_to_photo_metadata(self, row) -> PhotoMetadata:
        """Convert database row to PhotoMetadata."""
        return PhotoMetadata(
            path=row["path"],
            filename=row["filename"],
            size=row["size"],
            created_time=datetime.fromisoformat(row["created_time"]),
            modified_time=datetime.fromisoformat(row["modified_time"]),
            image_width=row["image_width"],
            image_height=row["image_height"],
            format=row["format"],
            exif_data=json.loads(row["exif_data"]) if row["exif_data"] else {},
        )
    
    def _row_to_analysis_result(self, row) -> AnalysisResult:
        """Convert database row to AnalysisResult."""
        return AnalysisResult(
            photo_path=row["path"],
            llm_model=row["llm_model"],
            description=row["description"],
            people=json.loads(row["people"]) if row["people"] else [],
            locations=json.loads(row["locations"]) if row["locations"] else [],
            objects=json.loads(row["objects"]) if row["objects"] else [],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            generated_at=datetime.fromisoformat(row["generated_at"]),
        )


class BatchMetadataStore(MetadataStore):
    """Batch metadata store with async support for concurrent processing."""
    
    def __init__(self, db_path: str = "photo_search.db", batch_size: int = 50):
        super().__init__(db_path)
        self.batch_size = batch_size
        self._pending_results: List[AnalysisResult] = []
        self._pending_metadata: List[PhotoMetadata] = []
        self._lock = asyncio.Lock()
    
    async def save_analysis_result_batch(self, result: AnalysisResult) -> None:
        """Save analysis result to batch for later bulk insert."""
        async with self._lock:
            self._pending_results.append(result)
            if len(self._pending_results) >= self.batch_size:
                await self._flush_results()
    
    async def save_photo_metadata_batch(self, metadata: PhotoMetadata) -> None:
        """Save photo metadata to batch for later bulk insert."""
        async with self._lock:
            self._pending_metadata.append(metadata)
            if len(self._pending_metadata) >= self.batch_size:
                await self._flush_metadata()
    
    async def flush_batch(self) -> None:
        """Flush any pending batch writes."""
        async with self._lock:
            if self._pending_results:
                await self._flush_results()
            if self._pending_metadata:
                await self._flush_metadata()
    
    async def _flush_results(self) -> None:
        """Flush pending analysis results to database."""
        if not self._pending_results:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare batch insert
                batch_data = []
                for result in self._pending_results:
                    # First ensure photo exists
                    photo_id = self.save_photo_metadata_from_path(result.photo_path)
                    
                    batch_data.append((
                        photo_id,
                        result.llm_model,
                        result.description,
                        json.dumps(result.people),
                        json.dumps(result.locations),
                        json.dumps(result.objects),
                        json.dumps(result.tags),
                        result.generated_at.isoformat(),
                    ))
                
                # Use INSERT OR REPLACE to handle duplicates
                cursor.executemany("""
                    INSERT OR REPLACE INTO analysis_results (
                        photo_id, llm_model, description,
                        people, locations, objects, tags, generated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, batch_data)
                
                conn.commit()
                logger.info(f"Flushed {len(batch_data)} analysis results to database")
                
        except Exception as e:
            logger.error(f"Failed to flush analysis results batch: {e}")
            # Fall back to individual saves
            for result in self._pending_results:
                try:
                    self.save_analysis_result(result)
                except Exception as inner_e:
                    logger.error(f"Failed to save individual result: {inner_e}")
        finally:
            self._pending_results.clear()
    
    async def _flush_metadata(self) -> None:
        """Flush pending photo metadata to database."""
        if not self._pending_metadata:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare batch insert
                batch_data = []
                for metadata in self._pending_metadata:
                    batch_data.append((
                        metadata.path,
                        metadata.filename,
                        metadata.size,
                        metadata.created_time.isoformat(),
                        metadata.modified_time.isoformat(),
                        metadata.image_width,
                        metadata.image_height,
                        metadata.format,
                        json.dumps(metadata.exif_data),
                        metadata.file_hash,
                    ))
                
                # Use INSERT OR REPLACE to handle duplicates
                cursor.executemany("""
                    INSERT OR REPLACE INTO photos (
                        path, filename, size, created_time, modified_time,
                        image_width, image_height, format, exif_data, file_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch_data)
                
                conn.commit()
                logger.info(f"Flushed {len(batch_data)} photo metadata records to database")
                
        except Exception as e:
            logger.error(f"Failed to flush metadata batch: {e}")
            # Fall back to individual saves
            for metadata in self._pending_metadata:
                try:
                    self.save_photo_metadata(metadata)
                except Exception as inner_e:
                    logger.error(f"Failed to save individual metadata: {inner_e}")
        finally:
            self._pending_metadata.clear()