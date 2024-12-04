# Comet WiFi Thermostat Integration

## Overview

This custom integration allows you to control your Comet WiFi thermostats through Home Assistant.

## Installation

### Via HACS

1. Add this repository to HACS as a custom integration.
2. Install the **Comet WiFi Thermostat** integration.
3. Restart Home Assistant.

### Manual Installation

1. Copy the comet_wifi folder to custom_components in your Home Assistant configuration directory.
2. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Configuration > Devices & Services**.
2. Click **Add Integration** and search for **Comet WiFi Thermostat**.
3. Follow the prompts to complete the setup.

## MQTT Bridging (Optional)

To maintain the official app functionality:

1. Ensure MQTT bridging is enabled during the integration setup.
2. The integration will configure MQTT bridging automatically.

## Dashboard Setup

1. Create a new Lovelace dashboard or view.
2. Add **Thermostat** cards for your devices.

## Notes

- Ensure your network allows connections to the Eurotronic MQTT servers.
- The integration requires the iohttp, paho-mqtt, and getmac Python packages.

## Support

For issues or feature requests, please open an issue on GitHub.

---

**Note:** Replace yourgithubusername in manifest.json and this README.md with your actual GitHub username before uploading.
