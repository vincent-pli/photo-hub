"""FastAPI web interface for photo-hub."""

import asyncio
import json
import logging
import uuid
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', force=True)
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .config import WebConfig, get_default_config

# Import photo-hub components
try:
    from photo_hub.photo_search.scanner import scan_photos
    from photo_hub.photo_search.metadata_store import MetadataStore
    from photo_hub.photo_search.factory import create_analyzer
    from photo_hub.photo_search.config import Language as PhotoLanguage
    from photo_hub.photo_search.models import PhotoMetadata
    # If import succeeds, use the real Language
    Language = PhotoLanguage  # type: ignore
    HAS_PHOTO_DEPS = True
except ImportError as e:
    logging.warning(f"Photo search dependencies not available: {e}")
    # Mock components for development
    scan_photos = None
    MetadataStore = None
    create_analyzer = None
    PhotoMetadata = None
    HAS_PHOTO_DEPS = False
    
    # Create mock Language class
    from enum import Enum
    class Language(str, Enum):
        EN = "en"
        ZH = "zh"
        AUTO = "auto"
        
        @classmethod
        def normalize(cls, language: str) -> "Language":
            language_lower = language.lower().strip()
            if language_lower in ("en", "english", "eng"):
                return cls.EN
            elif language_lower in ("zh", "chinese", "cn", "zh-cn", "zh_cn"):
                return cls.ZH
            elif language_lower in ("auto", "automatic"):
                return cls.AUTO
            else:
                return cls.EN

app = FastAPI(
    title="photo-hub API",
    description="AI-powered photo management and search",
    version="0.1.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
import os
from pathlib import Path

def find_static_dir() -> Path:
    """Find the static directory."""
    import sys
    
    # Always try current working directory first (for development)
    cwd = Path.cwd()
    
    # Check if we're in project root with src/photo_hub/web/static
    project_static = cwd / "src" / "photo_hub" / "web" / "static"
    if project_static.exists():
        logging.info(f"Found static directory at {project_static}")
        return project_static
    
    # Try relative to this file (for installed package)
    base_dir = Path(__file__).parent
    static_dir = base_dir / "static"
    if static_dir.exists():
        logging.info(f"Found static directory at {static_dir}")
        return static_dir
    
    # Try from environment variable
    env_static = os.environ.get("PHOTO_HUB_STATIC")
    if env_static:
        env_path = Path(env_static)
        if env_path.exists():
            logging.info(f"Found static directory at {env_path}")
            return env_path
    
    # Fallback
    logging.warning(f"Static directory not found, using: {static_dir}")
    return static_dir

static_dir = find_static_dir()
logging.info(f"Static directory path: {static_dir}")
logging.info(f"Static directory exists: {static_dir.exists()}")
logging.info(f"Static directory absolute: {static_dir.absolute()}")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logging.info(f"Mounted static files at /static from {static_dir}")
else:
    logging.warning(f"Static directory not found: {static_dir}")
    # List possible locations for debugging
    cwd = Path.cwd()
    logging.warning(f"Current working directory: {cwd}")
    logging.warning(f"API file location: {Path(__file__).absolute()}")

# Global state
config = get_default_config()
scan_tasks: Dict[str, Dict[str, Any]] = {}  # task_id -> task info
executor = ThreadPoolExecutor(max_workers=2)

# Pydantic models for request/response


class ScanRequest(BaseModel):
    directory: str = Field(..., description="Directory to scan")
    recursive: bool = Field(True, description="Scan subdirectories")
    skip_existing: bool = Field(True, description="Skip already analyzed photos")
    language: Optional[str] = Field("auto", description="Language for analysis (en/zh/auto)")
    max_concurrent: Optional[int] = Field(None, description="Maximum concurrent API calls (default: 5 for Qwen, 3 for Gemini)")
    batch_size: Optional[int] = Field(None, description="Batch size for processing (default: 10)")


class ScanStatusResponse(BaseModel):
    task_id: str
    status: str  # "pending", "scanning", "analyzing", "completed", "error"
    progress: float  # 0.0 to 1.0
    current_file: Optional[str] = None
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    successful_analyses: Optional[int] = None
    skipped_files: Optional[int] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    request: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(20, description="Maximum results to return")


class PhotoResult(BaseModel):
    filename: str
    path: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    people: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    objects: Optional[List[str]] = None
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None


class SearchResponse(BaseModel):
    results: List[PhotoResult]
    total: int


class StatsResponse(BaseModel):
    total_photos: int
    total_analyses: int
    models_used: int
    database_path: str


async def scan_directory_task_async(task_id: str, request: ScanRequest):
    """Async background task to scan and analyze photos with concurrency."""
    task_info = scan_tasks[task_id]
    
    try:
        if not scan_photos or not MetadataStore or not create_analyzer:
            raise ImportError("Photo search dependencies not installed")
        
        # Update task status
        task_info["status"] = "scanning"
        task_info["progress"] = 0.1
        
        # Initialize components with batch support
        store = MetadataStore(config.db_path)
        # Try to use batch store if available
        try:
            from photo_hub.photo_search.metadata_store import BatchMetadataStore
            batch_store = BatchMetadataStore(config.db_path, batch_size=50)
            task_info["batch_mode"] = True
        except ImportError:
            batch_store = store
            task_info["batch_mode"] = False
        
        # Get API key from config
        api_key = config.get_api_key()
        if not api_key and not config.model.lower().startswith("mock"):
            # Try to use mock analyzer if no API key
            logging.warning("No API key found, using mock analyzer")
            analyzer = create_analyzer(model="mock")
        else:
            analyzer = create_analyzer(
                model=config.model,
                api_key=api_key,
                base_url=config.get_base_url()
            )
        
        # Set concurrency limits from config or defaults
        max_concurrent = getattr(config, "max_concurrent", 5)
        batch_size = getattr(config, "batch_size", 10)
        
        analyzer.set_concurrency_limit(max_concurrent)
        analyzer.set_batch_size(batch_size)
        
        # Scan photos
        photos = scan_photos(request.directory, recursive=request.recursive)
        task_info["total_files"] = len(photos)
        task_info["status"] = "analyzing"
        task_info["progress"] = 0.2
        task_info["concurrent_workers"] = max_concurrent
        
        # Filter out already analyzed photos if requested
        skipped_files = 0
        if request.skip_existing:
            filtered_photos = []
            for photo in photos:
                existing = store.get_analysis_result(photo.path, analyzer.model)
                if existing:
                    logging.debug(f"Skipping already analyzed: {photo.filename} (model: {analyzer.model})")
                    skipped_files += 1
                else:
                    filtered_photos.append(photo)
            photos = filtered_photos
            task_info["total_files"] = len(photos)
        
        # Convert language string to appropriate Language enum
        # Use config language if request language is not specified or is "auto"
        language_str: str = request.language if request.language and request.language != "auto" else config.language
        
        # Always use the photo_search Language enum if available
        if HAS_PHOTO_DEPS:
            from photo_hub.photo_search.config import Language as PhotoLanguage
            language_enum = PhotoLanguage.normalize(language_str)
        else:
            # Fallback for testing - convert to string that analyzer can handle
            # Mock analyzers typically accept string values
            language_enum = language_str if language_str != "auto" else "en"
        
        # Analyze photos asynchronously
        successful = 0
        failed = 0
        
        # Get image paths for batch processing
        image_paths = [photo.path for photo in photos]
        
        # Update progress tracking
        task_info["current_file"] = "Starting batch analysis..."
        task_info["processed_files"] = 0
        
        # Use async batch analysis if available
        try:
            results = await analyzer.batch_analyze_async(
                image_paths=image_paths,
                language=language_enum,  # type: ignore
                max_concurrent=max_concurrent,
                batch_size=batch_size
            )
            
            # Save results with batch support
            for i, result in enumerate(results):
                task_info["current_file"] = Path(result.photo_path).name
                task_info["processed_files"] = i + 1
                task_info["progress"] = 0.2 + ((i + 1) / len(photos) * 0.8) if photos else 0.8
                
                if task_info["batch_mode"]:
                    await batch_store.save_analysis_result_batch(result)
                else:
                    store.save_analysis_result(result)
                
                successful += 1
                logging.info(f"Analyzed: {Path(result.photo_path).name}")
                
        except (AttributeError, NotImplementedError):
            # Fall back to synchronous processing if async not available
            logging.warning("Async batch analysis not available, falling back to synchronous")
            for i, photo in enumerate(photos):
                task_info["current_file"] = photo.filename
                task_info["processed_files"] = i
                task_info["progress"] = 0.2 + (i / len(photos) * 0.8) if photos else 0.8
                
                try:
                    result = analyzer.analyze_photo(photo.path, language=language_enum)  # type: ignore
                    store.save_analysis_result(result)
                    successful += 1
                    logging.info(f"Analyzed: {photo.filename}")
                except Exception as e:
                    logging.error(f"Error analyzing {photo.filename}: {e}")
                    failed += 1
        
        # Flush any pending batch writes
        if task_info["batch_mode"]:
            await batch_store.flush_batch()
        
        # Update final status
        task_info["status"] = "completed"
        task_info["progress"] = 1.0
        task_info["successful_analyses"] = successful
        task_info["failed_analyses"] = failed
        task_info["skipped_files"] = skipped_files
        task_info["processed_files"] = len(photos)
        task_info["completed_at"] = datetime.now()
        
        # Get final stats
        stats = store.get_stats()
        task_info["stats"] = stats
        
    except Exception as e:
        logging.error(f"Scan task failed: {e}", exc_info=True)
        task_info["status"] = "error"
        task_info["error_message"] = str(e)
        task_info["completed_at"] = datetime.now()


def scan_directory_task(task_id: str, request: ScanRequest):
    """Synchronous wrapper for async scan task."""
    asyncio.run(scan_directory_task_async(task_id, request))


# API endpoints


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>photo-hub</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            h1 { color: #4f46e5; }
            .container { max-width: 800px; margin: 0 auto; }
            .links { margin: 30px 0; }
            .links a { display: inline-block; margin: 10px; padding: 15px 30px; 
                      background: #4f46e5; color: white; text-decoration: none; 
                      border-radius: 8px; font-weight: bold; }
            .links a:hover { background: #7c3aed; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>photo-hub API Server</h1>
            <p>AI-powered photo management and search tool</p>
            <div class="links">
                <a href="/static/index.html">Launch Web Interface</a>
                <a href="/docs">API Documentation</a>
                <a href="/api/health">Health Check</a>
            </div>
            <p style="margin-top: 40px; color: #666;">
                Server is running. Use the web interface to scan and search photos.
            </p>
        </div>
    </body>
    </html>
    """


@app.post("/api/scan", response_model=ScanStatusResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start scanning and analyzing a directory."""
    # Validate directory exists
    directory_path = Path(request.directory)
    if not directory_path.exists() or not directory_path.is_dir():
        raise HTTPException(status_code=400, detail="The specified directory does not exist or is not accessible. Please check the path and permissions.")
    
    # Create task
    task_id = str(uuid.uuid4())
    task_info = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "current_file": None,
        "total_files": None,
        "processed_files": None,
        "successful_analyses": None,
        "error_message": None,
        "started_at": datetime.now(),
        "completed_at": None,
        "request": request.dict(),
    }
    scan_tasks[task_id] = task_info
    
    # Start background task
    background_tasks.add_task(scan_directory_task, task_id, request)
    
    return ScanStatusResponse(**task_info)


@app.get("/api/scan/{task_id}", response_model=ScanStatusResponse)
async def get_scan_status(task_id: str):
    """Get status of a scan task."""
    task_info = scan_tasks.get(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Scan task not found. It may have expired or been deleted.")
    return ScanStatusResponse(**task_info)


@app.get("/api/scan", response_model=List[ScanStatusResponse])
async def list_scans(limit: int = 10):
    """List recent scan tasks."""
    tasks = list(scan_tasks.values())
    tasks.sort(key=lambda x: x["started_at"], reverse=True)
    return [ScanStatusResponse(**task) for task in tasks[:limit]]


@app.post("/api/search", response_model=SearchResponse)
async def search_photos(request: SearchRequest):
    """Search analyzed photos."""
    try:
        if not MetadataStore:
            raise ImportError("Photo search dependencies not installed")
        
        store = MetadataStore(config.db_path)
        results = store.search_photos(request.query, limit=request.limit)
        
        # Convert to response format
        photo_results = []
        for result in results:
            photo_results.append(PhotoResult(
                filename=result.get("filename", ""),
                path=result.get("path", ""),
                description=result.get("description"),
                tags=result.get("tags", []),
                people=result.get("people", []),
                locations=result.get("locations", []),
                objects=result.get("objects", []),
                created_time=datetime.fromisoformat(result["created_time"]) if result.get("created_time") else None,
                modified_time=datetime.fromisoformat(result["modified_time"]) if result.get("modified_time") else None,
            ))
        
        return SearchResponse(results=photo_results, total=len(photo_results))
    except Exception as e:
        logging.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while searching photos. Please try again later.")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics."""
    try:
        if not MetadataStore:
            raise ImportError("Photo search dependencies not installed")
        
        store = MetadataStore(config.db_path)
        stats = store.get_stats()
        
        return StatsResponse(
            total_photos=stats.get("total_photos", 0),
            total_analyses=stats.get("total_analyses", 0),
            models_used=stats.get("models_used", 0),
            database_path=config.db_path,
        )
    except Exception as e:
        logging.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve database statistics. Please ensure the database is properly configured.")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)