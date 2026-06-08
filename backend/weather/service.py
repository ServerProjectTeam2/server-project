from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from backend.weather.schema import CurrentWeather, WeatherLocation

if load_dotenv:
    load_dotenv()

KMA_APIHUB_BASE_URL = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0"
KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_KEYWORD_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KST_OFFSET = timedelta(hours=9)

PRECIPITATION_TYPES = {
    "0": "No precipitation",
    "1": "Rain",
    "2": "Rain and snow",
    "3": "Snow",
    "4": "Shower",
    "5": "Drizzle",
    "6": "Drizzle and snow",
    "7": "Snow flurry",
}

SKY_TYPES = {
    "1": "Clear",
    "3": "Cloudy",
    "4": "Overcast",
}

CITY_GRID = {
    "seoul": ("Seoul", 37.5665, 126.9780, 60, 127),
    "\uc11c\uc6b8": ("Seoul", 37.5665, 126.9780, 60, 127),
    "busan": ("Busan", 35.1796, 129.0756, 98, 76),
    "\ubd80\uc0b0": ("Busan", 35.1796, 129.0756, 98, 76),
    "daegu": ("Daegu", 35.8714, 128.6014, 89, 90),
    "\ub300\uad6c": ("Daegu", 35.8714, 128.6014, 89, 90),
    "incheon": ("Incheon", 37.4563, 126.7052, 55, 124),
    "\uc778\ucc9c": ("Incheon", 37.4563, 126.7052, 55, 124),
    "gwangju": ("Gwangju", 35.1595, 126.8526, 58, 74),
    "\uad11\uc8fc": ("Gwangju", 35.1595, 126.8526, 58, 74),
    "daejeon": ("Daejeon", 36.3504, 127.3845, 67, 100),
    "\ub300\uc804": ("Daejeon", 36.3504, 127.3845, 67, 100),
    "ulsan": ("Ulsan", 35.5384, 129.3114, 102, 84),
    "\uc6b8\uc0b0": ("Ulsan", 35.5384, 129.3114, 102, 84),
    "sejong": ("Sejong", 36.4800, 127.2890, 66, 103),
    "\uc138\uc885": ("Sejong", 36.4800, 127.2890, 66, 103),
    "jeju": ("Jeju", 33.4996, 126.5312, 52, 38),
    "\uc81c\uc8fc": ("Jeju", 33.4996, 126.5312, 52, 38),
    "suwon": ("Suwon", 37.2636, 127.0286, 60, 121),
    "\uc218\uc6d0": ("Suwon", 37.2636, 127.0286, 60, 121),
    "chuncheon": ("Chuncheon", 37.8813, 127.7298, 73, 134),
    "\ucd98\ucc9c": ("Chuncheon", 37.8813, 127.7298, 73, 134),
    "cheongju": ("Cheongju", 36.6424, 127.4890, 69, 106),
    "\uccad\uc8fc": ("Cheongju", 36.6424, 127.4890, 69, 106),
    "jeonju": ("Jeonju", 35.8242, 127.1480, 63, 89),
    "\uc804\uc8fc": ("Jeonju", 35.8242, 127.1480, 63, 89),
    "gangneung": ("Gangneung", 37.7519, 128.8761, 92, 131),
    "\uac15\ub989": ("Gangneung", 37.7519, 128.8761, 92, 131),
}


class WeatherServiceError(Exception):
    pass


def search_locations(
    query: str,
    count: int = 5,
    language: str = "ko",
    country_code: Optional[str] = None,
) -> List[WeatherLocation]:
    del language, country_code
    keyword = query.strip().lower()
    if len(keyword) < 2:
        raise WeatherServiceError("Location keyword must be at least 2 characters.")

    matches: List[WeatherLocation] = []
    seen: Set[Tuple[int, int]] = set()
    for alias, city in CITY_GRID.items():
        if keyword in alias.lower() or keyword in city[0].lower():
            location = _city_to_location(city)
            grid_key = (location.nx or 0, location.ny or 0)
            if grid_key not in seen:
                matches.append(location)
                seen.add(grid_key)
        if len(matches) >= count:
            break
    if matches:
        return matches

    kakao_key = os.getenv("KAKAO_REST_API_KEY") or os.getenv("KAKAO_API_KEY")
    if kakao_key:
        return _search_kakao_locations(query, min(count, 15), kakao_key)
    return matches


def get_current_weather(
    place: Optional[str] = None,
    city: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    nx: Optional[int] = None,
    ny: Optional[int] = None,
    country_code: Optional[str] = "KR",
) -> CurrentWeather:
    del country_code
    location = _resolve_location(place, city, latitude, longitude, nx, ny)
    if location.nx is None or location.ny is None:
        raise WeatherServiceError("KMA grid coordinates nx/ny are required.")

    now = _now_kst()
    ncst_base_date, ncst_base_time = _latest_ultra_ncst_base(now)
    fcst_base_date, fcst_base_time = _latest_ultra_fcst_base(now)

    current = _items_to_map(
        _request_vilage_fcst("getUltraSrtNcst", ncst_base_date, ncst_base_time, location.nx, location.ny),
        value_key="obsrValue",
    )
    forecast = _nearest_forecast_map(
        _request_vilage_fcst("getUltraSrtFcst", fcst_base_date, fcst_base_time, location.nx, location.ny)
    )

    temperature = _to_float(current.get("T1H") or forecast.get("T1H"))
    humidity = _to_int(current.get("REH") or forecast.get("REH"))
    precipitation = _parse_precipitation(current.get("RN1") or forecast.get("RN1"))
    wind_speed = _to_float(current.get("WSD") or forecast.get("WSD"))
    wind_direction = _to_int(current.get("VEC") or forecast.get("VEC"))
    pty = str(_to_int(current.get("PTY") or forecast.get("PTY")) or 0)
    sky = str(_to_int(forecast.get("SKY")) or "")

    return CurrentWeather(
        location=location,
        time=f"{ncst_base_date}T{ncst_base_time}",
        temperature=temperature,
        apparent_temperature=temperature,
        relative_humidity=humidity,
        precipitation=precipitation,
        rain=precipitation if pty in {"1", "2", "4", "5", "6"} else 0.0,
        snowfall=precipitation if pty in {"2", "3", "6", "7"} else 0.0,
        weather_code=_kma_weather_code(pty, sky),
        weather_description=_weather_description(pty, sky),
        cloud_cover=_sky_to_cloud_cover(sky),
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        wind_gusts=None,
        is_day=None,
        daily_min_temperature=None,
        daily_max_temperature=None,
        daily_precipitation_probability=None,
        clothing_hints=_build_clothing_hints(temperature, precipitation, wind_speed, pty),
        source="KMA APIHub",
    )


def _request_vilage_fcst(endpoint: str, base_date: str, base_time: str, nx: int, ny: int) -> List[Dict[str, Any]]:
    auth_key = os.getenv("KMA_API_KEY") or os.getenv("KMA_AUTH_KEY")
    if not auth_key:
        raise WeatherServiceError("KMA_API_KEY is not set. Add your APIHub authKey to .env.")
    auth_key = auth_key.strip().strip('"').strip("'")

    params = {
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
        "authKey": auth_key,
    }
    url = f"{KMA_APIHUB_BASE_URL}/{endpoint}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=10) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise WeatherServiceError(f"KMA APIHub request failed: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise WeatherServiceError(f"KMA APIHub request failed: {exc}") from exc

    if "Unauthorized" in raw:
        raise WeatherServiceError("KMA APIHub authorization failed. Check authKey and API subscription.")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WeatherServiceError(f"KMA APIHub did not return JSON: {raw[:300]}") from exc

    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") != "00":
        message = header.get("resultMsg", "Unknown KMA APIHub error")
        raise WeatherServiceError(f"KMA APIHub error: {message}")

    item = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if isinstance(item, dict):
        return [item]
    return item


def _resolve_location(
    place: Optional[str],
    city: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    nx: Optional[int],
    ny: Optional[int],
) -> WeatherLocation:
    if nx is not None and ny is not None:
        return WeatherLocation(
            name=city or "KMA grid",
            country="Korea",
            country_code="KR",
            latitude=latitude or 0.0,
            longitude=longitude or 0.0,
            nx=nx,
            ny=ny,
            timezone="Asia/Seoul",
        )

    if place:
        return _geocode_place(place)

    if latitude is not None and longitude is not None:
        grid_x, grid_y = _lat_lon_to_grid(latitude, longitude)
        return WeatherLocation(
            name=city or "Selected coordinates",
            country="Korea",
            country_code="KR",
            latitude=latitude,
            longitude=longitude,
            nx=grid_x,
            ny=grid_y,
            timezone="Asia/Seoul",
        )

    if city:
        location = _lookup_city(city)
        if location:
            return location
        raise WeatherServiceError(f"Unsupported city: {city}. Use latitude/longitude or nx/ny.")

    raise WeatherServiceError("place, city, latitude/longitude, or nx/ny is required.")


def _geocode_place(place: str) -> WeatherLocation:
    kakao_key = os.getenv("KAKAO_REST_API_KEY") or os.getenv("KAKAO_API_KEY")
    if not kakao_key:
        raise WeatherServiceError("KAKAO_REST_API_KEY is required for place/address search.")

    kakao_key = kakao_key.strip().strip('"').strip("'")
    document = _search_kakao(KAKAO_ADDRESS_SEARCH_URL, place, kakao_key)
    if not document:
        document = _search_kakao(KAKAO_KEYWORD_SEARCH_URL, place, kakao_key)
    if not document:
        raise WeatherServiceError(f"Cannot find place/address: {place}")

    longitude = _to_float(document.get("x"))
    latitude = _to_float(document.get("y"))
    if latitude is None or longitude is None:
        raise WeatherServiceError(f"Kakao returned invalid coordinates for: {place}")

    nx, ny = _lat_lon_to_grid(latitude, longitude)
    name = (
        document.get("place_name")
        or document.get("address_name")
        or document.get("road_address_name")
        or place
    )
    return WeatherLocation(
        name=name,
        country="Korea",
        country_code="KR",
        latitude=latitude,
        longitude=longitude,
        nx=nx,
        ny=ny,
        timezone="Asia/Seoul",
    )


def _search_kakao(url: str, query: str, kakao_key: str) -> Optional[Dict[str, Any]]:
    request_url = f"{url}?{urlencode({'query': query, 'size': 1})}"
    request = Request(request_url, headers={"Authorization": f"KakaoAK {kakao_key}"})

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise WeatherServiceError(f"Kakao Local API request failed: {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise WeatherServiceError(f"Kakao Local API request failed: {exc}") from exc

    documents = data.get("documents", [])
    return documents[0] if documents else None


def _search_kakao_locations(query: str, count: int, kakao_key: str) -> List[WeatherLocation]:
    kakao_key = kakao_key.strip().strip('"').strip("'")
    documents = _search_kakao_documents(KAKAO_ADDRESS_SEARCH_URL, query, count, kakao_key)
    if not documents:
        documents = _search_kakao_documents(KAKAO_KEYWORD_SEARCH_URL, query, count, kakao_key)

    locations: List[WeatherLocation] = []
    seen: Set[Tuple[int, int]] = set()
    for document in documents:
        longitude = _to_float(document.get("x"))
        latitude = _to_float(document.get("y"))
        if latitude is None or longitude is None:
            continue
        nx, ny = _lat_lon_to_grid(latitude, longitude)
        grid_key = (nx, ny)
        if grid_key in seen:
            continue
        seen.add(grid_key)
        locations.append(
            WeatherLocation(
                name=(
                    document.get("place_name")
                    or document.get("address_name")
                    or document.get("road_address_name")
                    or query
                ),
                country="Korea",
                country_code="KR",
                latitude=latitude,
                longitude=longitude,
                nx=nx,
                ny=ny,
                timezone="Asia/Seoul",
            )
        )
    return locations


def _search_kakao_documents(url: str, query: str, count: int, kakao_key: str) -> List[Dict[str, Any]]:
    request_url = f"{url}?{urlencode({'query': query, 'size': count})}"
    request = Request(request_url, headers={"Authorization": f"KakaoAK {kakao_key}"})

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise WeatherServiceError(f"Kakao Local API request failed: {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise WeatherServiceError(f"Kakao Local API request failed: {exc}") from exc

    return data.get("documents", [])


def _lookup_city(city: str) -> Optional[WeatherLocation]:
    key = city.strip().lower()
    return _city_to_location(CITY_GRID[key]) if key in CITY_GRID else None


def _city_to_location(city: Tuple[str, float, float, int, int]) -> WeatherLocation:
    name, latitude, longitude, nx, ny = city
    return WeatherLocation(
        name=name,
        country="Korea",
        country_code="KR",
        latitude=latitude,
        longitude=longitude,
        nx=nx,
        ny=ny,
        timezone="Asia/Seoul",
    )


def _now_kst() -> datetime:
    return datetime.utcnow() + KST_OFFSET


def _latest_ultra_ncst_base(now: datetime) -> Tuple[str, str]:
    base = now.replace(minute=0, second=0, microsecond=0)
    if now.minute < 40:
        base -= timedelta(hours=1)
    return base.strftime("%Y%m%d"), base.strftime("%H00")


def _latest_ultra_fcst_base(now: datetime) -> Tuple[str, str]:
    base = now.replace(minute=30, second=0, microsecond=0)
    if now.minute < 45:
        base -= timedelta(hours=1)
    return base.strftime("%Y%m%d"), base.strftime("%H30")


def _items_to_map(items: List[Dict[str, Any]], value_key: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for item in items:
        category = item.get("category")
        value = item.get(value_key)
        if category and value is not None:
            values[category] = str(value)
    return values


def _nearest_forecast_map(items: List[Dict[str, Any]]) -> Dict[str, str]:
    grouped: Dict[Tuple[str, str], Dict[str, str]] = {}
    for item in items:
        fcst_date = item.get("fcstDate")
        fcst_time = item.get("fcstTime")
        category = item.get("category")
        value = item.get("fcstValue")
        if fcst_date and fcst_time and category and value is not None:
            grouped.setdefault((fcst_date, fcst_time), {})[category] = str(value)
    return grouped[sorted(grouped.keys())[0]] if grouped else {}


def _weather_description(pty: str, sky: str) -> str:
    if pty and pty != "0":
        return PRECIPITATION_TYPES.get(pty, "Precipitation")
    return SKY_TYPES.get(sky, "Unknown")


def _kma_weather_code(pty: str, sky: str) -> int:
    if pty and pty != "0":
        return int(pty)
    return int(sky) if sky.isdigit() else 0


def _sky_to_cloud_cover(sky: str) -> Optional[int]:
    return {"1": 0, "3": 60, "4": 100}.get(sky)


def _parse_precipitation(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    normalized = value.strip()
    if normalized in {"0", "0.0", "None"}:
        return 0.0
    digits = "".join(ch for ch in normalized if ch.isdigit() or ch == ".")
    return float(digits) if digits else 0.0


def _to_float(value: Optional[str]) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def _to_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(float(value)) if value is not None else None
    except ValueError:
        return None


def _build_clothing_hints(
    temperature: Optional[float],
    precipitation: Optional[float],
    wind_speed: Optional[float],
    pty: str,
) -> List[str]:
    hints: List[str] = []

    if temperature is not None:
        if temperature < 0:
            hints.append("Very cold: use padded outerwear, thick knitwear, and winter accessories.")
        elif temperature < 8:
            hints.append("Cold: a coat or thick outerwear is recommended.")
        elif temperature < 16:
            hints.append("Cool: a jacket, cardigan, or sweatshirt works well.")
        elif temperature < 23:
            hints.append("Mild: long sleeves or a light cardigan should be enough.")
        elif temperature < 28:
            hints.append("Warm: short sleeves, thin shirts, and breathable bottoms are suitable.")
        else:
            hints.append("Hot: choose thin, breathable clothes and lighter colors.")

    if (precipitation and precipitation > 0) or pty != "0":
        hints.append("Precipitation is expected: prepare an umbrella and shoes that can handle wet ground.")

    if wind_speed and wind_speed >= 8:
        hints.append("Wind is strong: bring a windbreaker rather than relying on light clothing only.")

    return hints


def _lat_lon_to_grid(latitude: float, longitude: float) -> Tuple[int, int]:
    re = 6371.00877
    grid = 5.0
    slat1 = 30.0
    slat2 = 60.0
    olon = 126.0
    olat = 38.0
    xo = 43.0
    yo = 136.0

    degrad = math.pi / 180.0
    re_grid = re / grid
    slat1_rad = slat1 * degrad
    slat2_rad = slat2 * degrad
    olon_rad = olon * degrad
    olat_rad = olat * degrad

    sn = math.tan(math.pi * 0.25 + slat2_rad * 0.5) / math.tan(math.pi * 0.25 + slat1_rad * 0.5)
    sn = math.log(math.cos(slat1_rad) / math.cos(slat2_rad)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1_rad * 0.5)
    sf = (sf**sn * math.cos(slat1_rad)) / sn
    ro = math.tan(math.pi * 0.25 + olat_rad * 0.5)
    ro = re_grid * sf / (ro**sn)

    ra = math.tan(math.pi * 0.25 + latitude * degrad * 0.5)
    ra = re_grid * sf / (ra**sn)
    theta = longitude * degrad - olon_rad
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = int(ra * math.sin(theta) + xo + 0.5)
    y = int(ro - ra * math.cos(theta) + yo + 0.5)
    return x, y
