"""Tests for photo search functionality."""

import pytest
import tempfile
import os
from pathlib import Path
import json
from datetime import datetime

# Skip photo search tests if dependencies not available
try:
    from opencode_testing.photo_search.models import PhotoMetadata, AnalysisResult
    from opencode_testing.photo_search.metadata_store import MetadataStore
    PHOTO_SEARCH_AVAILABLE = True
except ImportError:
    PHOTO_SEARCH_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PHOTO_SEARCH_AVAILABLE,
    reason="Photo search dependencies not installed"
)


class TestPhotoMetadata:
    """Test PhotoMetadata model."""
    
    def test_photo_metadata_creation(self):
        """Test creating PhotoMetadata instance."""
        created = datetime(2024, 1, 1, 10, 30, 0)
        modified = datetime(2024, 1, 2, 11, 30, 0)
        
        metadata = PhotoMetadata(
            path="/tmp/test.jpg",
            filename="test.jpg",
            size=1024,
            created_time=created,
            modified_time=modified,
            image_width=800,
            image_height=600,
            format="JPEG",
            exif_data={"Camera": "Test"}
        )
        
        assert metadata.path == "/tmp/test.jpg"
        assert metadata.filename == "test.jpg"
        assert metadata.size == 1024
        assert metadata.image_width == 800
        assert metadata.image_height == 600
        assert metadata.format == "JPEG"
        assert metadata.exif_data == {"Camera": "Test"}
        assert metadata.file_hash is not None
        assert metadata.directory == "/tmp"
    
    def test_photo_metadata_to_dict(self):
        """Test AnalysisResult to_dict and from_dict methods."""
        result = AnalysisResult(
            photo_path="/tmp/test.jpg",
            llm_model="gemini-1.5-pro-vision",
            description="A beautiful sunset",
            people=["person1", "person2"],
            locations=["beach", "ocean"],
            objects=["sun", "waves"],
            tags=["sunset", "beach", "ocean"],
            generated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        # Convert to dict
        result_dict = result.to_dict()
        assert result_dict["photo_path"] == "/tmp/test.jpg"
        assert result_dict["llm_model"] == "gemini-1.5-pro-vision"
        assert result_dict["description"] == "A beautiful sunset"
        assert result_dict["people"] == ["person1", "person2"]
        assert result_dict["tags"] == ["sunset", "beach", "ocean"]
        assert "generated_at" in result_dict
        
        # Convert back from dict
        result_from_dict = AnalysisResult.from_dict(result_dict)
        assert result_from_dict.photo_path == result.photo_path
        assert result_from_dict.llm_model == result.llm_model
        assert result_from_dict.description == result.description
        assert result_from_dict.people == result.people


class TestMetadataStore:
    """Test MetadataStore functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_store_initialization(self, temp_db):
        """Test initializing MetadataStore."""
        store = MetadataStore(temp_db)
        # Should create tables without error
        assert os.path.exists(temp_db)
    
    def test_save_and_retrieve_photo_metadata(self, temp_db):
        """Test saving and retrieving photo metadata."""
        store = MetadataStore(temp_db)
        
        # Create test metadata
        metadata = PhotoMetadata(
            path="/tmp/test.jpg",
            filename="test.jpg",
            size=1024,
            created_time=datetime.now(),
            modified_time=datetime.now(),
            image_width=800,
            image_height=600,
            format="JPEG",
            exif_data={}
        )
        
        # Save metadata
        photo_id = store.save_photo_metadata(metadata)
        assert photo_id is not None
        
        # Retrieve metadata
        retrieved = store.get_photo_metadata("/tmp/test.jpg")
        assert retrieved is not None
        assert retrieved.path == metadata.path
        assert retrieved.filename == metadata.filename
        assert retrieved.size == metadata.size
    
    def test_save_and_retrieve_analysis_result(self, temp_db):
        """Test saving and retrieving analysis results."""
        store = MetadataStore(temp_db)
        
        # First save photo metadata
        metadata = PhotoMetadata(
            path="/tmp/test.jpg",
            filename="test.jpg",
            size=1024,
            created_time=datetime.now(),
            modified_time=datetime.now(),
            image_width=800,
            image_height=600,
            format="JPEG",
            exif_data={}
        )
        store.save_photo_metadata(metadata)
        
        # Create analysis result
        result = AnalysisResult(
            photo_path="/tmp/test.jpg",
            llm_model="gemini-1.5-pro-vision",
            description="Test description",
            people=["person1"],
            locations=["location1"],
            objects=["object1"],
            tags=["tag1", "tag2"],
            generated_at=datetime.now()
        )
        
        # Save analysis result
        result_id = store.save_analysis_result(result)
        assert result_id is not None
        
        # Retrieve analysis result
        retrieved = store.get_analysis_result("/tmp/test.jpg", "gemini-1.5-pro-vision")
        assert retrieved is not None
        assert retrieved.photo_path == result.photo_path
        assert retrieved.llm_model == result.llm_model
        assert retrieved.description == result.description
        assert retrieved.people == result.people
    
    def test_search_photos(self, temp_db):
        """Test searching photos."""
        store = MetadataStore(temp_db)
        
        # Save some test data
        metadata = PhotoMetadata(
            path="/tmp/sunset.jpg",
            filename="sunset.jpg",
            size=1024,
            created_time=datetime.now(),
            modified_time=datetime.now(),
            image_width=800,
            image_height=600,
            format="JPEG",
            exif_data={}
        )
        store.save_photo_metadata(metadata)
        
        result = AnalysisResult(
            photo_path="/tmp/sunset.jpg",
            llm_model="gemini-1.5-pro-vision",
            description="Beautiful sunset at the beach",
            people=[],
            locations=["beach", "ocean"],
            objects=["sun", "waves"],
            tags=["sunset", "beach", "ocean", "evening"],
            generated_at=datetime.now()
        )
        store.save_analysis_result(result)
        
        # Search for photos
        results = store.search_photos("sunset", limit=10)
        assert len(results) >= 1
        assert any("sunset" in str(item).lower() for item in results)
    
    def test_get_stats(self, temp_db):
        """Test getting database statistics."""
        store = MetadataStore(temp_db)
        
        # Save some test data
        for i in range(3):
            metadata = PhotoMetadata(
                path=f"/tmp/photo{i}.jpg",
                filename=f"photo{i}.jpg",
                size=1024 * i,
                created_time=datetime.now(),
                modified_time=datetime.now(),
                image_width=800,
                image_height=600,
                format="JPEG",
                exif_data={}
            )
            store.save_photo_metadata(metadata)
            
            result = AnalysisResult(
                photo_path=f"/tmp/photo{i}.jpg",
                llm_model="gemini-1.5-pro-vision",
                description=f"Test photo {i}",
                people=[],
                locations=[],
                objects=[],
                tags=[f"tag{i}"],
                generated_at=datetime.now()
            )
            store.save_analysis_result(result)
        
        stats = store.get_stats()
        assert stats["total_photos"] >= 3
        assert stats["total_analyses"] >= 3
        assert stats["models_used"] >= 1


@pytest.mark.integration
class TestIntegration:
    """Integration tests for photo search functionality."""
    
    @pytest.fixture
    def test_directory(self):
        """Create a temporary directory with test images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some dummy files (not actual images)
            for i in range(3):
                file_path = Path(tmpdir) / f"test{i}.jpg"
                file_path.write_text(f"fake image data {i}")
            yield tmpdir
    
    def test_cli_photos_group(self):
        """Test that photos command group exists."""
        from opencode_testing.cli import cli
        import click
        
        # Check that photos command is registered
        assert 'photos' in cli.commands
        
        # Check subcommands
        photos_cmd = cli.commands['photos']
        assert isinstance(photos_cmd, click.Group)
        assert 'scan' in photos_cmd.commands
        assert 'search' in photos_cmd.commands
        assert 'stats' in photos_cmd.commands