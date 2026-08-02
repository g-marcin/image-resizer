from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.routes import images
from app.telemetry import setup_telemetry
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

Instrumentator().instrument(app).expose(app)
setup_telemetry(app)

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


