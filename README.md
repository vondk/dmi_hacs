# DMI Weather Integration for Home Assistant

> **Based on** the original work by [@crusell](https://github.com/crusell): [DMI_HA_Plugin](https://github.com/crusell/DMI_HA_Plugin). This project continues development from that foundation with additional improvements and HACS support.

A fast and efficient Home Assistant integration for Danish Meteorological Institute (DMI) weather data using the EDR (Environmental Data Retrieval) API.

This integration provides:
- **Current weather conditions** with temperature, humidity, pressure, wind, and more
- **24-hour hourly forecasts** with detailed weather parameters
- **5-day daily forecasts** with high/low temperatures
- **Purpose-built** for weather data retrieval

## Installation

### Method 1: Manual Installation (Recommended)

1. Download or clone this repository
2. Copy the `custom_components/dmi_weather` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "DMI Weather" and add it

### Method 2: HACS Installation

1. Add this repository to HACS as a custom repository
2. Install the integration through HACS
3. Restart Home Assistant
4. Add the integration through the UI

## Configuration

### Step 1: Add Integration

1. In Home Assistant, go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "DMI Weather"
3. Click on **DMI Weather**

### Step 2: Enter Configuration

1. **Name**: A friendly name for your weather entity (e.g., "Rydebäck Weather")
2. **Latitude**: The latitude of your location (e.g., 55.9667 for Rydebäck, Sweden)
3. **Longitude**: The longitude of your location (e.g., 12.7667 for Rydebäck, Sweden)

### Example Configuration for Rydebäck, Sweden

- **Name**: Rydebäck Weather
- **Latitude**: 55.9667
- **Longitude**: 12.7667

## Usage

Once configured, the integration will create a weather entity that provides:

### Current Weather
- Temperature (in Celsius)
- Humidity (percentage)
- Pressure (hPa)
- Wind speed (m/s)
- Wind direction (degrees)
- Weather condition (clear, cloudy, rain, etc.)
- Visibility (km)

### Daily Forecast
- Maximum and minimum temperatures
- Precipitation amount
- Wind speed and direction
- Weather conditions

## Data Source

This integration uses the DMI HARMONIE DINI IG weather model, which provides:
- High-resolution weather forecasts
- Coverage for Denmark and surrounding areas
- Updates every 6 hours
- Data available for up to 5 days ahead

For more information about the DMI Open Data API, visit: https://www.dmi.dk/friedata/dokumentation-paa-engelsk

## Troubleshooting

### Common Issues

1. **No data available**: 
   - Verify your coordinates are within the DMI coverage area
   - Try different coordinates if available
2. **API errors**: 
   - Check your internet connection
   - Check DMI API status

### Debug Logging

To enable debug logging, enable it in the UI under the device, or add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.dmi_weather: debug
```

## Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests

## License

This project is licensed under the MIT License.

## Acknowledgments

- [@crusell](https://github.com/crusell) for the original [DMI_HA_Plugin](https://github.com/crusell/DMI_HA_Plugin) which this project is built upon
- Danish Meteorological Institute (DMI) for providing the Open Data API
- Home Assistant community for the excellent framework