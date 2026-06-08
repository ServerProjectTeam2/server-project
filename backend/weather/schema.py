from typing import List, Optional

from pydantic import BaseModel, Field


class WeatherLocation(BaseModel):
    name: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    admin1: Optional[str] = None
    latitude: float
    longitude: float
    nx: Optional[int] = None
    ny: Optional[int] = None
    timezone: Optional[str] = None


class CurrentWeather(BaseModel):
    location: WeatherLocation
    time: Optional[str] = None
    temperature: Optional[float] = None
    apparent_temperature: Optional[float] = None
    relative_humidity: Optional[int] = None
    precipitation: Optional[float] = None
    rain: Optional[float] = None
    snowfall: Optional[float] = None
    weather_code: Optional[int] = None
    weather_description: str
    cloud_cover: Optional[int] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[int] = None
    wind_gusts: Optional[float] = None
    is_day: Optional[bool] = None
    daily_min_temperature: Optional[float] = None
    daily_max_temperature: Optional[float] = None
    daily_precipitation_probability: Optional[int] = None
    clothing_hints: List[str] = Field(default_factory=list)
    source: str = "KMA"
