"""
Image Service

This module provides image downloading and processing utilities.
"""

import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.core.exceptions import ImageDownloadError
from src.core.config import get_settings
from src.utils.validators import validate_image_url, sanitize_filename
from src.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ImageService:
    """Service for downloading and processing images."""
    
    def __init__(self):
        """Initialize image service."""
        self.settings = get_settings()
    
    @retry_with_backoff(max_attempts=3, initial_delay=1.0)
    def download_image(self, url: str, output_dir: str = ".") -> str:
        """Download image from URL with validation and retry.
        
        Args:
            url: Image URL to download
            output_dir: Directory to save image (defaults to current directory)
        
        Returns:
            Path to downloaded image file
        
        Raises:
            ImageDownloadError: If download fails
        """
        # Validate URL
        is_valid, error_msg = validate_image_url(url, self.settings.max_image_size_mb)
        if not is_valid:
            raise ImageDownloadError(f"Invalid image URL: {error_msg}")
        
        logger.info(f"Downloading image from: {url}")
        
        try:
            # Download with timeout
            response = requests.get(
                url,
                timeout=self.settings.request_timeout,
                headers={"User-Agent": "CFL-Player-Identification/1.0"}
            )
            response.raise_for_status()
            
            # Check content size
            content_length = len(response.content)
            max_size_bytes = self.settings.max_image_size_mb * 1024 * 1024
            
            if content_length > max_size_bytes:
                raise ImageDownloadError(
                    f"Image too large: {content_length / (1024*1024):.1f}MB "
                    f"(max: {self.settings.max_image_size_mb}MB)"
                )
            
            # Generate filename
            url_path = Path(url)
            extension = url_path.suffix if url_path.suffix else '.jpg'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = sanitize_filename(f"temp_image_{timestamp}{extension}")
            
            # Save to file
            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Image downloaded successfully: {output_path}")
            return str(output_path)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            raise ImageDownloadError(f"Failed to download image: {str(e)}")
    
    def cleanup_temp_image(self, image_path: str) -> None:
        """Remove temporary downloaded image.
        
        Args:
            image_path: Path to image file to remove
        """
        try:
            path = Path(image_path)
            if path.exists() and path.name.startswith("temp_image_"):
                path.unlink()
                logger.debug(f"Cleaned up temporary image: {image_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary image {image_path}: {e}")
