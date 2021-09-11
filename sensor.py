"""Sensors for Environment Canada (EC)."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    CONF_NAME,
    LENGTH_KILOMETERS,
    LENGTH_METERS,
    LENGTH_MILES,
    PERCENTAGE,
    PRESSURE_INHG,
    PRESSURE_PA,
    SPEED_MILES_PER_HOUR,
    TEMP_CELSIUS,
)
from homeassistant.util.distance import convert as convert_distance
from homeassistant.util.pressure import convert as convert_pressure

from . import ECBaseEntity
from .const import (
    CONF_LANGUAGE,
    CONF_STATION,
    DEFAULT_NAME,
    DOMAIN,
    SENSOR_TYPES,
)

ALERTS = [
    ("advisories", "Advisory"),
    ("endings", "Ending"),
    ("statements", "Statement"),
    ("warnings", "Warning"),
    ("watches", "Watch"),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the EC weather platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        ECSensor(
            coordinator, config_entry.data, description, hass.config.units.is_metric
        )
        for description in SENSOR_TYPES
    )
    async_add_entities(
        ECAlertSensor(coordinator, config_entry.data, alert) for alert in ALERTS
    )


class ECSensor(ECBaseEntity, SensorEntity):
    """An EC Sensor Entity."""

    def __init__(self, coordinator, config, description, is_metric):
        """Initialise the platform with a data instance."""
        name = f"{config.get(CONF_NAME, DEFAULT_NAME)} {description.name}"
        super().__init__(coordinator, config, name)

        self._entity_description = description
        self._is_metric = is_metric
        if is_metric:
            self._attr_native_unit_of_measurement = (
                description.native_unit_of_measurement
            )
        else:
            self._attr_native_unit_of_measurement = description.unit_convert
        self._attr_device_class = description.device_class

    @property
    def native_value(self):
        """Return the state."""
        key = self._entity_description.key
        value = self.get_value(key)
        if value is None:
            return None

        if key == "pressure":
            value = value * 10  # Convert kPa to hPa

        if self._is_metric:
            return value

        unit_of_measurement = self._entity_description.unit_convert
        if unit_of_measurement == SPEED_MILES_PER_HOUR:
            value = round(convert_distance(value, LENGTH_KILOMETERS, LENGTH_MILES))
        elif unit_of_measurement == LENGTH_MILES:
            value = round(convert_distance(value, LENGTH_METERS, LENGTH_MILES))
        elif unit_of_measurement == PRESSURE_INHG:
            value = round(convert_pressure(value, PRESSURE_PA, PRESSURE_INHG), 2)
        elif unit_of_measurement == TEMP_CELSIUS:
            value = round(value, 1)
        elif unit_of_measurement == PERCENTAGE:
            value = round(value)
        return value

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._config[CONF_STATION]}-{self._config[CONF_LANGUAGE]}-{self._entity_description.key}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return True  # FIX ME
        # return False

    @property
    def icon(self):
        """Return the icon."""
        return self._entity_description.icon

class ECAlertSensor(ECBaseEntity, SensorEntity):
    """An EC Sensor Entity for Alerts."""

    def __init__(self, coordinator, config, alert_name):
        """Initialise the platform with a data instance."""
        name = f"{config.get(CONF_NAME, DEFAULT_NAME)} {alert_name[1]} Alerts"
        super().__init__(coordinator, config, name)

        self._alert_name = alert_name
        self._alert_attrs = None

    @property
    def native_value(self):
        """Return the state."""
        value = self._coordinator.data.alerts.get(self._alert_name[0], {}).get("value")

        self._alert_attrs = {}
        for index, alert in enumerate(value, start=1):
            self._alert_attrs[f"alert {index}"] = alert.get("title")
            self._alert_attrs[f"alert_time {index}"] = alert.get("date")

        return len(value)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return self._alert_attrs

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._config[CONF_STATION]}-{self._config[CONF_LANGUAGE]}-{self._alert_name[0]}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return True  # FIX ME
        # return False
