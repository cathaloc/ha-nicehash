"""
NiceHash Rig Sensors
"""
from datetime import datetime
import logging

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity import Entity

from .const import (
    CURRENCY_BTC,
    DEVICE_STATUS_UNKNOWN,
    FORMAT_DATETIME,
    ICON_CURRENCY_BTC,
    ICON_EXCAVATOR,
    ICON_PULSE,
    ICON_THERMOMETER,
    NICEHASH_ATTRIBUTION,
)
from .coordinators import MiningRigsDataUpdateCoordinator
from .nicehash import MiningRig

_LOGGER = logging.getLogger(__name__)


class RigSensor(Entity):
    """
    Mining rig sensor
    """

    def __init__(self, coordinator: MiningRigsDataUpdateCoordinator, rig: MiningRig):
        """Initialize the sensor"""
        self.coordinator = coordinator
        self._rig_id = rig.id
        self._rig_name = rig.name

    @property
    def name(self):
        """Sensor name"""
        return self._rig_name

    @property
    def icon(self):
        """Sensor icon"""
        return ICON_EXCAVATOR

    @property
    def should_poll(self):
        """No need to poll, Coordinator notifies entity of updates"""
        return False

    @property
    def available(self):
        """Whether sensor is available"""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications"""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update entity"""
        await self.coordinator.async_request_refresh()

    def _get_rig(self):
        try:
            mining_rigs = self.coordinator.data.get("miningRigs")
            return MiningRig(mining_rigs.get(self._rig_id))
        except Exception as e:
            _LOGGER.error(f"Unable to get mining rig ({self._rig_id})\n{e}")


class RigTemperatureSensor(RigSensor):
    """
    Displays highest temperature of active mining rig devices
    """

    _temps = []
    _num_devices = 0
    _highest_temp = 0

    @property
    def name(self):
        """Sensor name"""
        return f"{self._rig_name} Temperature"

    @property
    def unique_id(self):
        """Unique entity id"""
        return f"{self._rig_id}:temperature"

    @property
    def state(self):
        """Sensor state"""
        self._highest_temp = 0
        rig = self._get_rig()
        if rig:
            self._temps = rig.temperatures
            self._num_devices = rig.num_devices
            self._highest_temp = max(rig.temperatures)

        return self._highest_temp

    @property
    def icon(self):
        """Sensor icon"""
        return ICON_THERMOMETER

    @property
    def unit_of_measurement(self):
        """Sensor unit of measurement"""
        # Not Celsius because then HA might convert to Fahrenheit
        return "C"

    @property
    def device_state_attributes(self):
        """Sensor device state attributes"""
        return {
            ATTR_ATTRIBUTION: NICEHASH_ATTRIBUTION,
            "highest_temperature": self._highest_temp,
            "temperatures": self._temps,
            "total_devices": self._num_devices,
        }


class RigStatusSensor(RigSensor):
    """
    Displays status of a mining rig
    """

    _status = DEVICE_STATUS_UNKNOWN
    _status_time = None

    @property
    def name(self):
        """Sensor name"""
        return f"{self._rig_name} Status"

    @property
    def unique_id(self):
        """Unique entity id"""
        return f"{self._rig_id}:status"

    @property
    def state(self):
        """Sensor state"""
        rig = self._get_rig()
        if rig:
            status = rig.status
            self._status_time = datetime.fromtimestamp(rig.status_time / 1000.0)
        else:
            status = DEVICE_STATUS_UNKNOWN
            self._status_time = None
            status = DEVICE_STATUS_UNKNOWN

        self._status = status[0].upper() + status.lower()[1:]
        return self._status

    @property
    def icon(self):
        """Sensor icon"""
        return ICON_PULSE

    @property
    def unit_of_measurement(self):
        """Sensor unit of measurement"""
        return None

    @property
    def device_state_attributes(self):
        """Sensor device state attributes"""
        status_time = None
        if self._status_time:
            status_time = self._status_time.strftime(FORMAT_DATETIME)

        return {
            ATTR_ATTRIBUTION: NICEHASH_ATTRIBUTION,
            "status": self._status,
            "status_time": status_time,
        }


class RigProfitabilitySensor(RigSensor):
    """
    Displays profitability of a mining rig
    """

    _profitability = 0
    _unpaid_amount = 0

    @property
    def name(self):
        """Sensor name"""
        return f"{self._rig_name} Profitability"

    @property
    def unique_id(self):
        """Unique entity id"""
        return f"{self._rig_id}:profitability"

    @property
    def state(self):
        """Sensor state"""
        rig = self._get_rig()
        if rig:
            self._profitability = rig.profitability
            self._unpaid_amount = rig.unpaid_amount
        else:
            self._profitability = 0
            self._unpaid_amount = 0

        return self._profitability

    @property
    def icon(self):
        """Sensor icon"""
        return ICON_CURRENCY_BTC

    @property
    def unit_of_measurement(self):
        """Sensor unit of measurement"""
        return CURRENCY_BTC

    @property
    def device_state_attributes(self):
        """Sensor device state attributes"""
        return {
            ATTR_ATTRIBUTION: NICEHASH_ATTRIBUTION,
            "profitability": self._profitability,
            "unpaid_amount": self._unpaid_amount,
        }
