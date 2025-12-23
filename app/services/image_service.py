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
        
        cleanup_cache()
        
        output.seek(0)
        return output

def cleanup_cache():
    if not config.CACHE_DIR.exists():
        return
    
    cache_files = list(config.CACHE_DIR.glob("*.jpg"))
    
    if len(cache_files) <= config.MAX_CACHE_FILES:
        return
    
    cache_files.sort(key=lambda f: f.stat().st_mtime)
    files_to_delete = cache_files[:-config.MAX_CACHE_FILES]
    
    for file in files_to_delete:
        try:
            file.unlink()
        except Exception:
            pass

def get_image_info(image_path: Path) -> dict:
    with Image.open(image_path) as img:
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode
        }


