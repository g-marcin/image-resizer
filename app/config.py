import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
env_path = PROJECT_ROOT / ".env"
print(f"Loading .env from: {env_path} (exists: {env_path.exists()})")
result = load_dotenv(dotenv_path=str(env_path), override=True)
print(f"load_dotenv result: {result}")

assets_dir_str = os.getenv("ASSETS_DIR", "/path/to/dog-assets")
print(f"ASSETS_DIR from env: {assets_dir_str}")
ASSETS_DIR = Path(assets_dir_str)
if not ASSETS_DIR.is_absolute():
    ASSETS_DIR = (PROJECT_ROOT / assets_dir_str).resolve()

cache_dir_str = os.getenv("CACHE_DIR", "/tmp/image_cache")
CACHE_DIR = Path(cache_dir_str)
if not CACHE_DIR.is_absolute():
    CACHE_DIR = (PROJECT_ROOT / cache_dir_str).resolve()

BASE_URL = os.getenv("BASE_URL", "https://cdn.mxmil.dev")
PORT = int(os.getenv("PORT", 8001))
MAX_WIDTH = int(os.getenv("MAX_WIDTH", "5000"))
MAX_HEIGHT = int(os.getenv("MAX_HEIGHT", "5000"))
DEFAULT_QUALITY = int(os.getenv("DEFAULT_QUALITY", "85"))
MAX_CACHE_FILES = int(os.getenv("MAX_CACHE_FILES", "1000"))

