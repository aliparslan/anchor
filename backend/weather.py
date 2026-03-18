import aiohttp

# Keep Open-Meteo for geocoding (weather.gov has no geocoder)
async def geocode_zip(zip_code: str) -> dict | None:
    """Geocode a zip code or city name to coordinates using Open-Meteo."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": zip_code, "count": 1, "language": "en", "format": "json"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
    results = data.get("results")
    if not results:
        return None
    r = results[0]
    return {
        "lat": r["latitude"],
        "lon": r["longitude"],
        "name": r.get("name", zip_code),
    }


WEATHER_GOV_UA = "(Base Dashboard, base-app@localhost)"


def condition_to_code(condition: str) -> int:
    """Map weather.gov short forecast text to our icon code system."""
    c = condition.lower()
    if "thunder" in c or "lightning" in c:
        return 95
    if "snow" in c or "blizzard" in c or "sleet" in c or "ice" in c:
        return 73
    if "rain" in c or "shower" in c or "drizzle" in c:
        return 63
    if "fog" in c:
        return 45
    if "overcast" in c:
        return 3
    if "mostly cloudy" in c or "partly" in c:
        return 2
    if "mostly clear" in c or "mostly sunny" in c:
        return 1
    return 0  # Clear / Sunny


async def fetch_weather(lat: float, lon: float) -> dict | None:
    """Fetch weather from weather.gov (NWS) API."""
    headers = {"User-Agent": WEATHER_GOV_UA, "Accept": "application/geo+json"}

    async with aiohttp.ClientSession() as session:
        # Step 1: Get grid point
        points_url = f"https://api.weather.gov/points/{round(lat, 4)},{round(lon, 4)}"
        async with session.get(points_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                print(f"[Weather] points API returned {resp.status}")
                return None
            points_data = await resp.json()

        props = points_data.get("properties", {})
        hourly_url = props.get("forecastHourly")
        if not hourly_url:
            print("[Weather] No forecastHourly URL in points response")
            return None

        # Step 2: Get hourly forecast
        async with session.get(hourly_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                print(f"[Weather] hourly forecast API returned {resp.status}")
                return None
            hourly_data = await resp.json()

    periods = hourly_data.get("properties", {}).get("periods", [])
    if not periods:
        return None

    now = periods[0]
    temp = now.get("temperature", 0)
    condition = now.get("shortForecast", "Unknown")
    weather_code = condition_to_code(condition)

    # Rain chance from current period
    rain_chance = 0
    precip = now.get("probabilityOfPrecipitation", {})
    if precip and precip.get("value") is not None:
        rain_chance = precip["value"]

    # Daily high/low from first 24 hours
    temps_24h = [p.get("temperature", 0) for p in periods[:24]]
    high = max(temps_24h) if temps_24h else temp
    low = min(temps_24h) if temps_24h else temp

    # Next 4 hours for forecast row
    hourly = []
    for p in periods[1:5]:
        hourly.append({
            "time": p.get("startTime", ""),
            "temp": p.get("temperature", 0),
            "condition": p.get("shortForecast", ""),
            "weather_code": condition_to_code(p.get("shortForecast", "")),
        })

    return {
        "temp": temp,
        "weather_code": weather_code,
        "condition": condition,
        "high": high,
        "low": low,
        "rain_chance": rain_chance,
        "hourly": hourly,
    }
