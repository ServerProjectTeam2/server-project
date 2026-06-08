from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.weather.schema import CurrentWeather, WeatherLocation
from backend.weather.service import (
    WeatherServiceError,
    get_current_weather,
    search_locations,
)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/search", response_model=List[WeatherLocation])
async def search_weather_locations(
    query: str = Query(..., min_length=2, description="Location keyword. Example: Seoul, Busan, Jeju"),
    count: int = Query(5, ge=1, le=100),
    country_code: Optional[str] = Query("KR", description="ISO country code. Use empty value for global search."),
):
    try:
        return search_locations(query=query, count=count, country_code=country_code or None)
    except WeatherServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/current", response_model=CurrentWeather)
async def read_current_weather(
    place: Optional[str] = Query(None, description="Address or place keyword. Example: Yeoksam-dong, Hongdae station"),
    city: Optional[str] = Query(None, description="Location name. Example: Seoul, Busan"),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    nx: Optional[int] = Query(None, ge=1, description="KMA grid x coordinate"),
    ny: Optional[int] = Query(None, ge=1, description="KMA grid y coordinate"),
    country_code: Optional[str] = Query("KR", description="ISO country code used for city search"),
):
    try:
        return get_current_weather(
            place=place,
            city=city,
            latitude=latitude,
            longitude=longitude,
            nx=nx,
            ny=ny,
            country_code=country_code or None,
        )
    except WeatherServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
