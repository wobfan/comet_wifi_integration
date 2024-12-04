import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVAC_MODE_HEAT, SUPPORT_TARGET_TEMPERATURE
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import callback

from getmac import get_mac_address
import socket
import struct
import fcntl
from scapy.all import ARP, Ether, srp

from .const import DOMAIN, MAC_PREFIXES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Comet WiFi thermostats."""
    mqtt_client = hass.components.mqtt

    devices = await hass.async_add_executor_job(discover_devices)

    entities = []
    for device in devices:
        entities.append(CometWifiThermostat(hass, mqtt_client, device, config_entry.data))

    async_add_entities(entities)


def get_local_ip_range():
    """Determine the local IP address range."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    interfaces = ["eth0", "eth1", "wlan0", "wlan1"]
    for iface in interfaces:
        try:
            local_ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', iface[:15].encode('utf-8'))
            )[20:24])
            ip_range = local_ip.rsplit('.', 1)[0] + '.0/24'
            return ip_range
        except Exception:
            continue
    # If all interfaces fail, use default
    _LOGGER.warning("Could not determine local IP range, using default 192.168.1.0/24")
    return '192.168.1.0/24'


def discover_devices():
    """Discover Comet WiFi devices via MAC address pattern recognition."""
    _LOGGER.info("Discovering Comet WiFi devices on the local network...")
    ip_range = get_local_ip_range()
    _LOGGER.debug(f"Scanning IP range: {ip_range}")

    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=3, verbose=False)[0]

    devices = []
    for sent, received in result:
        mac = received.hwsrc.upper().replace(":", "")
        if any(mac.startswith(prefix) for prefix in MAC_PREFIXES):
            devices.append({
                'name': f"Comet Thermostat {mac[-6:]}",
                'mac': mac,
            })

    _LOGGER.info(f"Found {len(devices)} Comet devices.")
    return devices


class CometWifiThermostat(ClimateEntity):
    """Representation of a Comet WiFi Thermostat."""

    def __init__(self, hass, mqtt_client, device_info, config):
        self.hass = hass
        self.mqtt_client = mqtt_client
        self._name = device_info['name']
        self._unique_id = device_info['mac']
        self._target_temperature = 20.0
        self._current_temperature = 20.0
        self._hvac_mode = HVAC_MODE_HEAT
        self._supported_features = SUPPORT_TARGET_TEMPERATURE
        self._device_info = device_info
        self._config = config

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._unique_id)},
            name=self._name,
            manufacturer="Eurotronic",
            model="Comet WiFi",
        )

        # Subscribe to MQTT topics
        self._subscribe_topics()

    def _subscribe_topics(self):
        """Subscribe to MQTT topics to receive updates."""
        topic = f"03/00002F71/{self._unique_id}/V/#"

        @callback
        def message_received(msg):
            """Handle new MQTT messages."""
            try:
                if msg.topic.endswith("/V/A1"):
                    # Current Temperature
                    value = int(msg.payload[1:], 16) / 2
                    self._current_temperature = value
                elif msg.topic.endswith("/V/A0"):
                    # Target Temperature
                    value = int(msg.payload[1:], 16) / 2
                    self._target_temperature = value
                self.async_write_ha_state()
            except Exception as e:
                _LOGGER.error(f"Failed to parse MQTT message: {e}")

        self.mqtt_client.async_subscribe(topic, message_received)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def current_temperature(self):
        return self._current_temperature

    @property
    def supported_features(self):
        return self._supported_features

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            temperature = kwargs[ATTR_TEMPERATURE]
            self._target_temperature = temperature
            await self._publish_temperature(temperature)
            self.async_write_ha_state()

    async def _publish_temperature(self, temperature):
        temp_hex = "#" + "%0x" % int(float(temperature) * 2)
        topic = f"03/00002F71/{self._unique_id}/S/A0"

        await self.mqtt_client.async_publish(
            topic=topic,
            payload=temp_hex,
            qos=2,
            retain=False,
        )
