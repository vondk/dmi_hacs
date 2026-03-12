"""DMI Weather EDR API client."""
from __future__ import annotations

import logging
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    DMI_EDR_BASE_URL, EDR_COLLECTIONS_ENDPOINT,
    EDR_POSITION_QUERY, DEFAULT_TIMEOUT, EDR_PARAMETERS, MAX_FORECAST_DAYS
)

_LOGGER = logging.getLogger(__name__)

class DMIWeatherAPI:
    """DMI Weather API client."""
    
    def __init__(self, hass: HomeAssistant, latitude: float, longitude: float) -> None:
        self.hass = hass
        self.latitude = latitude
        self.longitude = longitude
        self.current_data: Dict[str, Any] = {}
        self.hourly_forecast_data: List[Dict[str, Any]] = []
        self.forecast_data: List[Dict[str, Any]] = []
        self.daily_forecast_data: List[Dict[str, Any]] = []
        self._last_request_time = 0
        self._rate_limit_delay = 5.0
        self._max_retries = 3
        self._update_lock = asyncio.Lock()
        
        # Use only the domain name - Home Assistant's HTTP client handles DNS
        self._api_urls = [
            DMI_EDR_BASE_URL,  # Original domain
        ]

    async def _rate_limit(self) -> None:
        """Ensure minimum delay between API requests to avoid rate limiting."""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._rate_limit_delay:
            delay = self._rate_limit_delay - time_since_last
            await asyncio.sleep(delay)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request using Home Assistant's HTTP client."""
        # Use Home Assistant's built-in HTTP client
        session = async_get_clientsession(self.hass)

        # Use the domain URL
        url = f"{self._api_urls[0]}{endpoint}"
        _LOGGER.debug("Making request to: %s", url)

        try:
            async with session.get(url, params=params, timeout=DEFAULT_TIMEOUT) as response:
                if response.status == 429:
                    _LOGGER.warning("Rate limit exceeded, waiting before retry")
                    await asyncio.sleep(10)
                    raise Exception("Rate limit exceeded, please try again later")
                elif response.status == 404:
                    error_text = await response.text()
                    _LOGGER.error("API returned 404: %s", error_text)
                    raise Exception("No weather data available for the requested time period. Please try again later.")
                elif response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("API request failed with status %d: %s", response.status, error_text)
                    raise Exception(f"API request failed with status {response.status}")
                
                data = await response.json()
                _LOGGER.debug("Response received from %s", url)
                return data

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout after %ds calling %s", DEFAULT_TIMEOUT, url)
            raise Exception("Timeout connecting to DMI EDR API. Please try again.")
        except Exception as e:
            if "Rate limit" in str(e) or "API request failed" in str(e) or "No weather data" in str(e):
                raise
            _LOGGER.error("Unexpected error calling %s: %s", url, e)
            raise Exception(f"Network error: {e}")

    async def test_connection(self) -> bool:
        """Test API connection without affecting rate limits."""
        try:
            await self._rate_limit()
            collections = await self._get_collections()
            return len(collections) > 0
        except Exception as e:
            _LOGGER.error("Connection test failed: %s", e)
            return False

    async def update(self) -> None:
        """Update weather data from DMI EDR API."""
        if self._update_lock.locked():
            _LOGGER.debug("Update already in progress, skipping concurrent request")
            return
        async with self._update_lock:
            collection_id = "harmonie_dini_sf"
            try:
                await self._fetch_weather_data(collection_id)
                _LOGGER.debug("Weather data updated successfully (collection: %s)", collection_id)
            except Exception as err:
                _LOGGER.warning("Failed to update weather data: %s", err)
                raise

    async def _get_collections(self) -> Dict[str, Any]:
        """Get available EDR collections."""
        await self._rate_limit()
        data = await self._make_request(EDR_COLLECTIONS_ENDPOINT)

        collections = {}
        if "collections" in data:
            for collection in data["collections"]:
                collections[collection["id"]] = collection

        _LOGGER.debug("Available collections: %s", list(collections.keys()))
        return collections

    async def _fetch_weather_data(self, collection_id: str) -> Dict[str, Any]:
        """Fetch weather data from DMI EDR API."""
        await self._rate_limit()
        
        now = dt_util.utcnow()
        end_time = now + timedelta(days=MAX_FORECAST_DAYS)
        start_time_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        _LOGGER.debug("Requesting weather data from %s to %s", start_time_str, end_time_str)

        essential_params = [
            "temperature-2m", "wind-speed-10m", "gust-wind-speed-10m",
            "total-precipitation", "fraction-of-cloud-cover", "dew-point-temperature-2m"
        ]
        params = {
            "coords": f"POINT({self.longitude} {self.latitude})",
            "datetime": f"{start_time_str}/{end_time_str}",
            "parameter-name": ",".join(essential_params),
            "crs": "crs84",
            "f": "CoverageJSON"
        }

        endpoint = f"{EDR_COLLECTIONS_ENDPOINT}/{collection_id}{EDR_POSITION_QUERY}"
        data = await self._make_request(endpoint, params)
        self._process_edr_data(data)

    def _process_edr_data(self, data: Dict[str, Any]) -> None:
        """Process the CoverageJSON data from EDR API."""
        if not data or "ranges" not in data:
            _LOGGER.error("No weather data received from DMI EDR API")
            return

        ranges = data["ranges"]
        domain = data.get("domain", {})
        axes = domain.get("axes", {})
        
        # Extract time axis
        time_values = axes.get("t", {}).get("values", [])
        if not time_values:
            _LOGGER.error("No time values in EDR response")
            return

        used_lon = axes.get("x", {}).get("values", [None])[0]
        used_lat = axes.get("y", {}).get("values", [None])[0]
        _LOGGER.debug("API returned data for coordinates: lat=%s, lon=%s", used_lat, used_lon)
        _LOGGER.debug("Processing %d time steps", len(time_values))
        
        # Process hourly data
        hourly_data = []
        
        for i, time_str in enumerate(time_values):
            try:
                # Parse time
                time_obj = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                
                # Extract weather values for this time step
                weather_data = {
                    "time": time_obj,
                    "temperature": self._extract_parameter_value(ranges, EDR_PARAMETERS["temperature"], i),
                    "pressure": None,  # Set to None if not requested
                    "humidity": None,  # Set to None if not requested
                    "wind_speed": self._extract_parameter_value(ranges, EDR_PARAMETERS["wind_speed"], i),
                    "wind_gust": self._extract_parameter_value(ranges, EDR_PARAMETERS["wind_gust"], i),
                    "precipitation": self._extract_parameter_value(ranges, EDR_PARAMETERS["precipitation"], i),
                    "cloud_cover": self._extract_parameter_value(ranges, EDR_PARAMETERS["cloud_cover"], i),
                    "dew_point": self._extract_parameter_value(ranges, EDR_PARAMETERS["dew_point"], i),
                    "weather_code": None,
                }
                
                # Estimate weather condition based on precipitation and cloud cover
                if weather_data["precipitation"] and weather_data["precipitation"] > 0.1:
                    weather_data["weather_code"] = "rainy"
                elif weather_data["cloud_cover"] and weather_data["cloud_cover"] > 80:
                    weather_data["weather_code"] = "cloudy"
                elif weather_data["cloud_cover"] and weather_data["cloud_cover"] > 30:
                    weather_data["weather_code"] = "partlycloudy"
                else:
                    weather_data["weather_code"] = "clear"
                
                hourly_data.append(weather_data)
                    
            except (ValueError, TypeError) as err:
                _LOGGER.warning("Error parsing data at index %d: %s", i, err)
                continue

        # Set current data to the first time step
        if hourly_data:
            self.current_data = hourly_data[0].copy()
            self.hourly_forecast_data = hourly_data[1:25]  # Next 24 hours
            self.forecast_data = hourly_data[1:]  # All future data

            _LOGGER.debug(
                "Parsed %d hourly entries, current: %s, temp: %s°C",
                len(hourly_data),
                hourly_data[0]["time"].strftime("%H:%M UTC"),
                round(hourly_data[0]["temperature"], 1) if hourly_data[0]["temperature"] is not None else "N/A",
            )

            # Aggregate into daily forecast
            daily_groups: Dict[Any, List] = defaultdict(list)
            for entry in hourly_data[1:]:
                daily_groups[entry["time"].date()].append(entry)

            daily_data = []
            condition_priority = ["rainy", "cloudy", "partlycloudy", "clear"]
            for day_date in sorted(daily_groups.keys()):
                entries = daily_groups[day_date]
                temps = [e["temperature"] for e in entries if e["temperature"] is not None]
                precips = [e["precipitation"] for e in entries if e["precipitation"] is not None]
                winds = [e["wind_speed"] for e in entries if e["wind_speed"] is not None]
                conditions = [e["weather_code"] for e in entries if e["weather_code"] is not None]
                dominant = next((c for c in condition_priority if c in conditions), "clear")
                daily_data.append({
                    "time": datetime.combine(day_date, datetime.min.time()).replace(tzinfo=dt_util.UTC),
                    "temperature_max": max(temps) if temps else None,
                    "temperature_min": min(temps) if temps else None,
                    "precipitation": sum(precips) if precips else None,
                    "wind_speed": max(winds) if winds else None,
                    "weather_code": dominant,
                })
            self.daily_forecast_data = daily_data
            _LOGGER.debug("Built %d daily forecast entries", len(daily_data))

    def _extract_parameter_value(self, ranges: Dict, parameter: str, time_index: int) -> Optional[float]:
        """Extract parameter value from EDR ranges data."""
        if parameter not in ranges:
            return None
        
        param_data = ranges[parameter]
        if "values" not in param_data:
            return None
        
        values = param_data["values"]
        if time_index >= len(values):
            return None
        
        value = values[time_index]
        if value is None:
            return None
        
        # Convert temperature from Kelvin to Celsius if needed
        if parameter == "temperature-2m" and value > 200:
            value = value - 273.15
        
        # Convert dew point from Kelvin to Celsius if needed
        if parameter == "dew-point-temperature-2m" and value > 200:
            value = value - 273.15
        
        # Convert cloud cover from fraction to percentage if needed
        if parameter == "fraction-of-cloud-cover" and value <= 1:
            value = value * 100
        
        return float(value)
