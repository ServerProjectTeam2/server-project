from fastapi import FastAPI

from backend.clothing.router import router as clothing_router
from backend.recommendation.router import router as recommendation_router
from backend.weather.router import router as weather_router

app = FastAPI(title="Weather Clothing Recommendation API")

app.include_router(weather_router)
app.include_router(clothing_router)
app.include_router(recommendation_router)


@app.get("/")
async def root():
    return {"message": "Weather Clothing Recommendation API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
