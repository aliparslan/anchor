import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


async def geocode_zip(zip_code: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(GEOCODE_URL, params={
            "name": zip_code,
            "count": 1,
            "language": "en",
            "format": "json",
        })
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        r = results[0]
        return {"lat": r["latitude"], "lon": r["longitude"], "name": r.get("name", "")}


async def fetch_weather(lat: float, lon: float) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(WEATHER_URL, params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "temperature_unit": "fahrenheit",
            "forecast_days": 1,
            "timezone": "auto",
        })
        data = resp.json()
        current = data.get("current", {})
        daily = data.get("daily", {})
        return {
            "temp": round(current.get("temperature_2m", 0)),
            "weather_code": current.get("weather_code", 0),
            "high": round(daily.get("temperature_2m_max", [0])[0]),
            "low": round(daily.get("temperature_2m_min", [0])[0]),
            "rain_chance": daily.get("precipitation_probability_max", [0])[0],
        }
