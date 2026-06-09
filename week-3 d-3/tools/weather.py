"""
🌤️ Weather Tool (Stretch Goal)

Gets current weather and forecast for any city.

Uses wttr.in (free, no API key) or Open-Meteo (free, no API key).
"""

import os
import json
from typing import Optional

import requests


def get_weather(city: str, forecast_days: int = 0) -> str:
    """
    Get current weather for a city.

    Uses wttr.in — free, no API key required.

    Args:
        city: City name (e.g., "London", "New York", "Tokyo")
        forecast_days: Number of forecast days (0 = current only, max 3)

    Returns:
        Formatted weather string
    """
    try:
        if forecast_days > 0:
            url = f"https://wttr.in/{city}?format=j1&days={min(forecast_days, 3)}"
        else:
            url = f"https://wttr.in/{city}?format=j1"

        resp = requests.get(url, timeout=10, headers={"User-Agent": "curl/8.0"})
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_condition", [{}])[0]

        temp_c = current.get("temp_C", "?")
        feels_like = current.get("FeelsLikeC", "?")
        humidity = current.get("humidity", "?")
        wind = current.get("windspeedKmph", "?")
        desc = current.get("weatherDesc", [{}])[0].get("value", "?")
        uv = current.get("uvIndex", "?")

        lines = [
            f"🌤️  Weather in {city.title()}",
            f"   {desc}",
            f"   🌡️  {temp_c}°C (feels like {feels_like}°C)",
            f"   💧 Humidity: {humidity}%",
            f"   💨 Wind: {wind} km/h",
            f"   ☀️  UV Index: {uv}",
        ]

        if forecast_days > 0:
            forecasts = data.get("weather", [])
            for i, day in enumerate(forecasts[1:], 1):
                date = day.get("date", "?")
                hi = day.get("maxtempC", "?")
                lo = day.get("mintempC", "?")
                desc_day = day.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", "?")
                lines.append(f"   📅 Day +{i} ({date}): {desc_day}, {lo}–{hi}°C")

        return "\n".join(lines)

    except requests.exceptions.RequestException as e:
        return f"❌ Weather API error: {e}"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return f"❌ Could not parse weather data: {e}"
    except Exception as e:
        return f"❌ Unexpected weather error: {e}"


# ──────────────────────────────────────────────────────────────
# JSON Schema for tool calling
# ──────────────────────────────────────────────────────────────

SCHEMA = {
    "name": "get_weather",
    "description": "Get current weather and optional forecast for any city worldwide",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name (e.g., 'London', 'New York', 'Mumbai')",
            },
            "forecast_days": {
                "type": "integer",
                "description": "Number of forecast days to include (0 = current only, max 3)",
                "default": 0,
            },
        },
        "required": ["city"],
    },
}


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🌤️  Weather Tool Test")
    print("-" * 40)
    result = get_weather("London", forecast_days=1)
    print(result)
