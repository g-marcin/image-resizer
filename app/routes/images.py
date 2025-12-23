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
            raise HTTPException(
                status_code=404,
                detail=f"Original image not found. Looking for: {image_path}"
            )
        
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
            raise HTTPException(
                status_code=404,
                detail=f"Image not found. Looking for: {image_path}"
            )
        
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

