# Dog API CDN Service - Image Resizing CDN

## Overview

Standalone FastAPI service for serving and resizing dog breed images. Supports on-the-fly resizing with dimensions in the URL path.

## Architecture

- **Service**: FastAPI application
- **Storage**: Local filesystem (`dog-assets` directory)
- **Caching**: Resized images cached to disk
- **URL Pattern**: `/images/{path}/{filename}-{width}-{height}.jpg`

## Project Structure

```
dog-cdn/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── image_service.py
│   └── routes/
│       ├── __init__.py
│       └── images.py
├── requirements.txt
├── .env.example
└── README.md
```

## Dependencies

**requirements.txt:**
```python
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
Pillow>=10.0.0
python-dotenv>=1.0.0
```

## Configuration

**app/config.py:**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ASSETS_DIR = Path(os.getenv("ASSETS_DIR", "/path/to/dog-assets"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/image_cache"))
BASE_URL = os.getenv("BASE_URL", "https://cdn.mxmil.dev")
PORT = int(os.getenv("PORT", 8001))
MAX_WIDTH = int(os.getenv("MAX_WIDTH", "5000"))
MAX_HEIGHT = int(os.getenv("MAX_HEIGHT", "5000"))
DEFAULT_QUALITY = int(os.getenv("DEFAULT_QUALITY", "85"))
```

**.env.example:**
```env
ASSETS_DIR=/path/to/dog-assets
CACHE_DIR=/tmp/image_cache
BASE_URL=https://cdn.mxmil.dev
PORT=8001
MAX_WIDTH=5000
MAX_HEIGHT=5000
DEFAULT_QUALITY=85
```

## Implementation

**app/services/image_service.py:**
```python
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import Optional
import hashlib
import app.config as config

def resize_image(
    image_path: Path,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: int = None
) -> BytesIO:
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    if quality is None:
        quality = config.DEFAULT_QUALITY
    
    if width and width > config.MAX_WIDTH:
        width = config.MAX_WIDTH
    if height and height > config.MAX_HEIGHT:
        height = config.MAX_HEIGHT
    
    cache_key = f"{image_path.stem}_{width}_{height}_{quality}"
    cache_file = config.CACHE_DIR / f"{hashlib.md5(cache_key.encode()).hexdigest()}.jpg"
    
    if cache_file.exists():
        with open(cache_file, 'rb') as f:
            cached = BytesIO(f.read())
            cached.seek(0)
            return cached
    
    with Image.open(image_path) as img:
        original_format = img.format
        
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        if width or height:
            if width and height:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            elif width:
                ratio = width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((width, new_height), Image.Resampling.LANCZOS)
            elif height:
                ratio = height / img.height
                new_width = int(img.width * ratio)
                img = img.resize((new_width, height), Image.Resampling.LANCZOS)
        
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'wb') as f:
            f.write(output.getvalue())
        
        output.seek(0)
        return output

def get_image_info(image_path: Path) -> dict:
    with Image.open(image_path) as img:
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode
        }
```

**app/routes/images.py:**
```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
from pathlib import Path
import re
import app.config as config
from app.services.image_service import resize_image

router = APIRouter()

@router.get(
    "/images/{file_path:path}",
    tags=["Images"],
    summary="Serve image file",
    description="Serves images with optional resizing. URL pattern: /images/path/to/image-{width}-{height}.jpg"
)
async def serve_image(file_path: str):
    path_obj = Path(file_path)
    filename = path_obj.name
    
    pattern = r'^(.+)-(\d+)-(\d+)\.(jpg|jpeg|png)$'
    match_result = re.match(pattern, filename, re.IGNORECASE)
    
    if match_result:
        base_name, width_str, height_str, ext = match_result.groups()
        width = int(width_str)
        height = int(height_str)
        
        if width > config.MAX_WIDTH or height > config.MAX_HEIGHT:
            raise HTTPException(
                status_code=400,
                detail=f"Dimensions exceed maximum allowed size ({config.MAX_WIDTH}x{config.MAX_HEIGHT})"
            )
        
        original_filename = f"{base_name}.{ext}"
        original_path = path_obj.parent / original_filename
        image_path = config.ASSETS_DIR / original_path
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Original image not found")
        
        try:
            resized = resize_image(image_path, width, height)
            return Response(
                content=resized.read(),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                    "X-Original-Image": str(original_path)
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    else:
        image_path = config.ASSETS_DIR / file_path
        
        if not image_path.exists() or not image_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(
            image_path,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable"
            }
        )

@router.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns service health status"
)
async def health_check():
    return {
        "status": "healthy",
        "assets_dir": str(config.ASSETS_DIR),
        "assets_exists": config.ASSETS_DIR.exists(),
        "cache_dir": str(config.CACHE_DIR)
    }
```

**app/main.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import images
import app.config as config

app = FastAPI(
    title="Dog API CDN",
    description="CDN service for serving and resizing dog breed images",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(images.router)

@app.get("/")
async def root():
    return {
        "service": "Dog API CDN",
        "version": "1.0.0",
        "endpoints": {
            "images": "/images/{path}",
            "health": "/health"
        }
    }
```

## Usage Examples

### Original Image
```
GET https://cdn.mxmil.dev/images/retriever/image.jpg
```

### Resized Image (1200x800)
```
GET https://cdn.mxmil.dev/images/retriever/image-1200-800.jpg
```

### Resized Image (width only, maintains aspect ratio)
```
GET https://cdn.mxmil.dev/images/retriever/image-800-0.jpg
```
Note: For width-only or height-only, use `0` for the other dimension in URL pattern, but the service will calculate it automatically.

### Health Check
```
GET https://cdn.mxmil.dev/health
```

## URL Pattern Rules

- **Original**: `/images/{breed}/{filename}.jpg`
- **Resized**: `/images/{breed}/{filename}-{width}-{height}.jpg`
- Dimensions must be integers
- Supported formats: `.jpg`, `.jpeg`, `.png`
- Case-insensitive matching

## Features

- ✅ On-the-fly image resizing
- ✅ Disk caching of resized images
- ✅ Aspect ratio preservation
- ✅ JPEG optimization
- ✅ CORS support
- ✅ Cache headers for CDN
- ✅ Maximum dimension limits
- ✅ Health check endpoint

## Deployment

### Run with Uvicorn
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Run as Service (systemd)
**/etc/systemd/system/dog-cdn.service:**
```ini
[Unit]
Description=Dog API CDN Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/dog-cdn
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name cdn.mxmil.dev;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Performance Considerations

- **Cache Directory**: Use fast storage (SSD) for cache directory
- **Cache Cleanup**: Implement periodic cleanup of old cached files
- **Memory**: Pillow processes images in memory; monitor for large images
- **Concurrency**: Uvicorn handles multiple requests; adjust workers as needed

## Security Considerations

- Validate file paths to prevent directory traversal
- Set maximum dimension limits
- Rate limiting (consider adding)
- Input validation for dimensions

## Integration with Main API

Update your main API's `get_image_url` function to support resizing:

```python
def get_image_url(image_path: Path, width: int = None, height: int = None) -> str:
    relative_path = image_path.relative_to(config.ASSETS_DIR)
    
    if width and height:
        base_name = image_path.stem
        extension = image_path.suffix
        return f"{config.BASE_URL_IMG}/images/{relative_path.parent.as_posix()}/{base_name}-{width}-{height}{extension}"
    
    return f"{config.BASE_URL_IMG}/images/{relative_path.as_posix()}"
```