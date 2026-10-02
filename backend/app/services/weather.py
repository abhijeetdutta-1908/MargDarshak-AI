"""OpenWeather current conditions + 5-day forecast, with a clearly-labelled seasonal fallback."""

import asyncio
import logging
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta

import httpx

from app.config import get_settings
from app.models import Destination
from app.services.http import ExternalAPIError, request_json
from app.utils.cache import TTLCache

log = logging.getLogger("margdarshak")
BASE = "https://api.openweathermap.org/data/2.5"
WET = {"Rain", "Drizzle", "Thunderstorm", "Snow"}
MONSOON_MONTHS = {6, 7, 8, 9}

_cache = TTLCache(get_settings().weather_cache_seconds)


def _daily(forecast: dict) -> list[dict]:
    """Collapse 3-hourly forecast slots into one entry per local day."""
    tz = timedelta(seconds=forecast.get("city", {}).get("timezone", 0))
    days = defaultdict(list)
    for slot in forecast.get("list", []):
        local = datetime.fromtimestamp(slot["dt"], UTC) + tz
        days[local.date()].append((local.hour, slot))
    out = []
    for day, slots in sorted(days.items()):
        daytime = [s for h, s in slots if 8 <= h <= 19] or [s for _, s in slots]
        conditions = Counter(s["weather"][0]["main"] for s in daytime)
        condition = conditions.most_common(1)[0][0]
        icon = Counter(s["weather"][0]["icon"] for s in daytime).most_common(1)[0][0]
        pop = max(s.get("pop", 0) for s in daytime)
        out.append({
            "date": day.isoformat(),
            "temp_min": round(min(s["main"]["temp_min"] for _, s in slots), 1),
            "temp_max": round(max(s["main"]["temp_max"] for _, s in slots), 1),
            "condition": condition,
            "icon": icon,
            "rain_probability": round(pop, 2),
            "rain_likely": pop >= 0.5 or bool(WET & set(conditions)),
        })
    return out


async def _fetch_live(client: httpx.AsyncClient, dest: Destination, key: str) -> dict:
    params = {"lat": dest.latitude, "lon": dest.longitude, "units": "metric", "appid": key}
    current, forecast = await asyncio.gather(
        request_json(client, "GET", f"{BASE}/weather", "OpenWeather", params=params),
        request_json(client, "GET", f"{BASE}/forecast", "OpenWeather", params=params),
    )
    w = current["weather"][0]
    return {
        "source": "live",
        "provider": "OpenWeather",
        "destination_id": dest.id,
        "destination": dest.name,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "current": {
            "temperature": current["main"]["temp"],
            "feels_like": current["main"]["feels_like"],
            "humidity": current["main"]["humidity"],
            "weather_condition": w["main"],
            "description": w["description"],
            "wind_speed": current.get("wind", {}).get("speed"),
            "icon": w["icon"],
        },
        "forecast": _daily(forecast),
        "seasonal": seasonal_guidance(dest, date.today().month),
        "note": None,
    }


def seasonal_guidance(dest: Destination, month: int) -> dict:
    in_season = month in dest.best_seasons
    monsoon = month in MONSOON_MONTHS and not in_season
    if in_season:
        summary = "Usually a good time to visit"
    elif monsoon:
        summary = "Monsoon season: rain is likely"
    else:
        summary = "Outside the best season: check conditions before travelling"
    return {"month": month, "in_best_season": in_season, "rain_likely": monsoon, "summary": summary}


def fallback(dest: Destination, reason: str) -> dict:
    return {
        "source": "fallback",
        "provider": None,
        "destination_id": dest.id,
        "destination": dest.name,
        "fetched_at": None,
        "current": None,
        "forecast": [],
        "seasonal": seasonal_guidance(dest, date.today().month),
        "note": f"Live weather unavailable ({reason}). Showing seasonal guidance from destination data.",
    }


async def get_weather(client: httpx.AsyncClient, dest: Destination) -> dict:
    key = get_settings().openweather_api_key
    if not key:
        return fallback(dest, "OPENWEATHER_API_KEY not configured")
    if (hit := _cache.get(dest.id)) is not None:
        return hit
    try:
        data = await _fetch_live(client, dest, key)
    except ExternalAPIError as e:
        log.warning("Weather for %s failed: %s", dest.name, e.reason)
        return fallback(dest, e.reason)
    except (KeyError, IndexError, TypeError):
        log.exception("Unexpected OpenWeather payload for %s", dest.name)
        return fallback(dest, "OpenWeather returned an unexpected response")
    _cache.set(dest.id, data)
    return data


def day_outlook(weather: dict, dest: Destination, day: date | None) -> dict:
    """Weather for one trip day: live forecast when the date is covered, else seasonal guidance."""
    if day:
        for f in weather.get("forecast", []):
            if f["date"] == day.isoformat():
                return {"source": "forecast", "rain_likely": f["rain_likely"],
                        "summary": f"{f['condition']}, {f['temp_min']:.0f}–{f['temp_max']:.0f}°C"
                                   + (f", {round(f['rain_probability'] * 100)}% chance of rain" if f["rain_probability"] else "")}
    g = seasonal_guidance(dest, (day or date.today()).month)
    return {"source": "seasonal", "rain_likely": g["rain_likely"], "summary": g["summary"]}
