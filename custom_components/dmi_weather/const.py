"""Constants for the DMI Weather integration."""

DOMAIN = "dmi_weather"

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_NAME = "name"
DEFAULT_NAME = "DMI Weather"

# DMI EDR API configuration
DMI_EDR_BASE_URL = "https://opendataapi.dmi.dk/v1/forecastedr"

# EDR API endpoints
EDR_COLLECTIONS_ENDPOINT = "/collections"
EDR_POSITION_QUERY = "/position"

# API request parameters
DEFAULT_TIMEOUT = 30
MAX_FORECAST_DAYS = 5

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30  # minutes

# Weather condition mappings for EDR data
WEATHER_CONDITIONS = {
    "clear": "clear-night",
    "partly_cloudy": "partlycloudy",
    "cloudy": "cloudy",
    "fog": "fog",
    "rain": "rainy",
    "snow": "snowy",
    "sleet": "snowy-rainy",
    "thunder": "lightning",
    "drizzle": "rainy",
    "shower": "rainy",
}

# EDR parameter mappings for HARMONIE collection
EDR_PARAMETERS = {
    "temperature": "temperature-2m",
    "pressure": "pressure-sealevel", 
    "humidity": "relative-humidity-2m",
    "wind_speed": "wind-speed-10m",
    "wind_gust": "gust-wind-speed-10m",
    "precipitation": "total-precipitation",
    "cloud_cover": "fraction-of-cloud-cover",
    "dew_point": "dew-point-temperature-2m",
    "snow_precipitation": "time-integral-of-total-solid-precipitation-flux",
    "water_vapour": "total-column-vertically-integrated-water-vapour",
}
