from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from backend.clothing.router import router as clothing_router
from backend.recommendation.router import router as recommendation_router
from backend.weather.router import router as weather_router

app = FastAPI(title="Weather Clothing Recommendation API")

# 정적 파일(이미지) 접근 설정
UPLOAD_DIR = "backend/static/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="static")

app.include_router(weather_router)
app.include_router(clothing_router)
app.include_router(recommendation_router)


@app.get("/")
async def root():
    return {"message": "Weather Clothing Recommendation API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
