# DMI Weather Integration for Home Assistant

> **Based on** the original work by [@crusell](https://github.com/crusell): [DMI_HA_Plugin](https://github.com/crusell/DMI_HA_Plugin). This project continues development from that foundation with additional improvements and HACS support.

A fast and efficient Home Assistant integration for Danish Meteorological Institute (DMI) weather data using the EDR (Environmental Data Retrieval) API.

This integration provides:
- **Current weather conditions** with temperature, humidity, pressure, wind, and more
- **24-hour hourly forecasts** with detailed weather parameters
- **5-day daily forecasts** with high/low temperatures
- **Purpose-built** for weather data retrieval

---

## 📦 Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click the three-dot menu (top right) → **Custom Repositories**
3. Add this repository:
```
   https://github.com/your-username/dmi_hacs
```
4. Set category to: **Integration**
5. Click **Add**
6. Search for **DMI Weather** in HACS Integrations
7. Click **Install**
8. Restart Home Assistant if prompted
9. Go to **Settings → Devices & Services → Add Integration** and search for **DMI Weather**

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/dmi_weather` folder into `config/custom_components/`
3. Restart Home Assistant
4. Add the integration via **Settings → Devices & Services**

---

## ⚙️ Configuration

After installation:

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **DMI Weather** and click on it
3. Enter your location details:
   - **Name**: A friendly name for your weather entity (e.g., `Copenhagen Weather`)
   - **Latitude**: The latitude of your location (e.g., `55.6761`)
   - **Longitude**: The longitude of your location (e.g., `12.5683`)
4. Save — the weather entity is created immediately, no restart required

To update settings, go to **Settings → Devices & Services → DMI Weather → Configure**.

---

## 🌤️ Sensor Behavior

Once configured, the integration creates a weather entity that reports current conditions and forecasts.

### Current Weather

| Parameter         | Unit    | Description                        |
| ----------------- | ------- | ---------------------------------- |
| Temperature       | °C      | Current air temperature            |
| Humidity          | %       | Relative humidity                  |
| Pressure          | hPa     | Atmospheric pressure               |
| Wind Speed        | m/s     | Wind speed                         |
| Wind Direction    | degrees | Wind bearing                       |
| Weather Condition | —       | Clear, cloudy, rain, snow, etc.    |
| Visibility        | km      | Horizontal visibility              |

### Daily Forecast

- Maximum and minimum temperatures
- Precipitation amount
- Wind speed and direction
- Weather conditions

### Example: Current Weather State

```yaml
state: "sunny"
attributes:
  temperature: 18.4
  humidity: 62
  pressure: 1013
  wind_speed: 4.2
  wind_bearing: 210
  visibility: 25
```

---

## 🗃️ Data Source

This integration uses the **DMI HARMONIE DINI IG** weather model, which provides:

- High-resolution weather forecasts
- Coverage for Denmark and surrounding areas
- Updates every 6 hours
- Data available for up to 5 days ahead

For more information about the DMI Open Data API, visit: https://www.dmi.dk/friedata/dokumentation-paa-engelsk

---

## 🔧 Troubleshooting

### Common Issues

1. **No data available**
   - Verify your coordinates are within the DMI coverage area (Denmark and surrounding regions)
   - Try slightly different coordinates if the exact location returns no data

2. **API errors**
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

---

## 🔗 Related Projects

- [@crusell](https://github.com/crusell)'s original [DMI_HA_Plugin](https://github.com/crusell/DMI_HA_Plugin) — the foundation this project is built upon
- [Home Assistant](https://www.home-assistant.io/) — the excellent smart home framework

---

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests

---

## 📄 License

MIT License — see `LICENSE` file for details

---

## 🙏 Acknowledgments

- [@crusell](https://github.com/crusell) for the original [DMI_HA_Plugin](https://github.com/crusell/DMI_HA_Plugin)
- Danish Meteorological Institute (DMI) for providing the Open Data API
- Home Assistant community for the excellent framework
