"""Support for DMI Weather EDR."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, cast

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LATITUDE as CONF_LAT,
    CONF_LONGITUDE as CONF_LON,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    WEATHER_CONDITIONS,
)
from .dmi_api import DMIWeatherAPI

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=DEFAULT_UPDATE_INTERVAL)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the DMI Weather EDR weather platform."""
    name = config_entry.data[CONF_NAME]
    latitude = config_entry.data[CONF_LATITUDE]
    longitude = config_entry.data[CONF_LONGITUDE]
    update_interval = config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    api = DMIWeatherAPI(hass, latitude, longitude)
    entity = DMIWeatherEntity(name, api, update_interval)

    async_add_entities([entity], False)

    # Schedule initial data fetch immediately as a background task (non-blocking)
    hass.async_create_task(entity.async_update())


class DMIWeatherEntity(WeatherEntity):
    """Representation of a DMI Weather entity."""

    _attr_attribution = "Data provided by Danish Meteorological Institute's (DMI) Open Data API"
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY

    def __init__(self, name: str, api: DMIWeatherAPI, update_interval_minutes: int) -> None:
        """Initialize the DMI Weather EDR entity."""
        self._api = api
        self._attr_name = name
        self._attr_unique_id = f"dmi_edr_{api.latitude}_{api.longitude}"
        self._update_interval = timedelta(minutes=update_interval_minutes)
        self._last_update: datetime | None = None

    async def async_update(self) -> None:
        """Update current weather data."""
        now = dt_util.utcnow()
        if self._last_update and (now - self._last_update) < self._update_interval:
            _LOGGER.debug("Skipping update — next fetch in %s", self._update_interval - (now - self._last_update))
            return
        try:
            await self._api.update()
            self._last_update = dt_util.utcnow()
            self._attr_available = True
            _LOGGER.debug("Entity updated — next fetch at %s", (now + self._update_interval).strftime("%H:%M UTC"))
        except Exception as err:
            _LOGGER.error("Error updating DMI EDR weather: %s", err)
            self._attr_available = False

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        if not self._api.current_data:
            return None
        
        return self._api.current_data.get("weather_code")

    @property
    def native_temperature(self) -> float | None:
        """Return the temperature."""
        if not self._api.current_data:
            return None
        return self._api.current_data.get("temperature")

    @property
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        if not self._api.current_data:
            return None
        return self._api.current_data.get("pressure")

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        if not self._api.current_data:
            return None
        return self._api.current_data.get("wind_speed")

    @property
    def wind_bearing(self) -> float | None:
        """Return the wind bearing."""
        if not self._api.current_data:
            return None
        return self._api.current_data.get("wind_direction")

    @property
    def native_visibility(self) -> float | None:
        """Return the visibility."""
        if not self._api.current_data:
            return None
        visibility = self._api.current_data.get("visibility")
        if visibility is not None:
            return visibility / 1000  # Convert to km
        return None

    @property
    def humidity(self) -> float | None:
        """Return the humidity."""
        if not self._api.current_data:
            return None
        return self._api.current_data.get("humidity")

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed."""
        if not self._api.current_data:
            return None
        return self._api.current_data.get("wind_gust")

    @property
    def cloud_coverage(self) -> float | None:
        """Return the cloud coverage."""
        if not self._api.current_data:
            return None
        return self._api.current_data.get("cloud_cover")

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        if not self._api.daily_forecast_data:
            return None

        forecast_list = []
        for forecast in self._api.daily_forecast_data:
            forecast_dict = {
                ATTR_FORECAST_TIME: forecast.get("time"),
                ATTR_FORECAST_NATIVE_TEMP: forecast.get("temperature_max"),
                ATTR_FORECAST_NATIVE_TEMP_LOW: forecast.get("temperature_min"),
                ATTR_FORECAST_NATIVE_PRECIPITATION: forecast.get("precipitation"),
                ATTR_FORECAST_WIND_SPEED: forecast.get("wind_speed"),
                ATTR_FORECAST_WIND_BEARING: forecast.get("wind_direction"),
            }
            
            weather_code = forecast.get("weather_code")
            if weather_code is not None:
                forecast_dict[ATTR_FORECAST_CONDITION] = weather_code

            forecast_list.append(Forecast(**forecast_dict))

        return forecast_list

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast."""
        if not self._api.hourly_forecast_data:
            return None

        forecast_list = []
        for forecast in self._api.hourly_forecast_data:
            forecast_dict = {
                ATTR_FORECAST_TIME: forecast.get("time"),
                ATTR_FORECAST_NATIVE_TEMP: forecast.get("temperature"),
                ATTR_FORECAST_NATIVE_PRECIPITATION: forecast.get("precipitation"),
                ATTR_FORECAST_WIND_SPEED: forecast.get("wind_speed"),
                ATTR_FORECAST_WIND_BEARING: forecast.get("wind_direction"),
            }
            
            weather_code = forecast.get("weather_code")
            if weather_code is not None:
                forecast_dict[ATTR_FORECAST_CONDITION] = weather_code

            forecast_list.append(Forecast(**forecast_dict))

        return forecast_list
