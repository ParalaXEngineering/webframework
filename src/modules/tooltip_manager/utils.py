"""Utility functions for tooltip system

This module provides image processing utilities for tooltips.

Image Processing Workflow:
--------------------------
To add images to tooltips, the recommended workflow is:

1. **In the UI**: User pastes or uploads an image in the WYSIWYG editor
2. **In the editor**: The editor converts the image to base64 data URI automatically
3. **On save**: The HTML content (including base64 images) is stored in the database

Alternatively, for programmatic/batch usage:

1. Call process_image_to_base64() with an image file path
2. The function returns a data URI string like: "data:image/jpeg;base64,/9j/4AAQ..."
3. Embed this in HTML: <img src="data:image/jpeg;base64,...">
4. Store the complete HTML in the tooltip content field

Configuration (via settings_manager):
-------------------------------------
- tooltip_system.image_max_width: Maximum width in pixels (default: 800)
- tooltip_system.image_max_height: Maximum height in pixels (default: 600)
- tooltip_system.image_quality: JPEG quality 1-100 (default: 85)

These settings ensure images are optimized for tooltips and don't bloat the database.

Example Usage:
-------------
```python
from src.modules.tooltip_manager.utils import process_image_to_base64

# Process an image file
image_path = "path/to/image.jpg"
data_uri = process_image_to_base64(image_path, max_width=800, max_height=600, quality=85)

# Create HTML content with the image
html_content = f'<img src="{data_uri}" alt="Part diagram"><br>Part description here'

# Register tooltip with HTML content
tooltip_manager.register_tooltip(
    keyword="PartNumber",
    content=html_content,
    contexts=["Global"]
)
```

Note: For most use cases, the WYSIWYG editor (TinyMCE/Quill) handles
image-to-base64 conversion automatically. This utility is primarily for
programmatic/batch operations.
"""

import base64
import io
from pathlib import Path
from typing import Union
from PIL import Image


def process_image_to_base64(
    image_source: Union[Path, str, bytes],
    max_width: int = 800,
    max_height: int = 600,
    quality: int = 85
) -> str:
    """
    Resize image and encode to base64 data URI.
    
    Args:
        image_source: Path to image file, file-like object, or bytes
        max_width: Maximum width for resized image
        max_height: Maximum height for resized image
        quality: JPEG quality (1-100)
    
    Returns:
        Data URI string (e.g., "data:image/jpeg;base64,/9j/4AAQ...")
    
    Raises:
        PIL.UnidentifiedImageError: If image cannot be identified
        IOError: If image cannot be opened
    """
    # Open image
    if isinstance(image_source, (str, Path)):
        img = Image.open(image_source)
    elif isinstance(image_source, bytes):
        img = Image.open(io.BytesIO(image_source))
    else:
        img = Image.open(image_source)
    
    # Convert RGBA to RGB if necessary
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = background
    elif img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    
    # Resize maintaining aspect ratio
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Determine format
    format_str = 'JPEG'
    mime_type = 'image/jpeg'
    if hasattr(image_source, 'name'):
        ext = Path(image_source.name).suffix.lower()
        if ext == '.png':
            format_str = 'PNG'
            mime_type = 'image/png'
    
    # Encode to base64
    buffer = io.BytesIO()
    if format_str == 'JPEG':
        img.save(buffer, format=format_str, quality=quality, optimize=True)
    else:
        img.save(buffer, format=format_str, optimize=True)
    
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return f"data:{mime_type};base64,{img_base64}"
