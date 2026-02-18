"""Sensor platform for Energy Control Pro."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import EnergyControlProCoordinator
from .const import DOMAIN


@dataclass(frozen=True)
class EnergyControlProSensorDescription(SensorEntityDescription):
    """Describes Energy Control Pro sensor entity."""


SENSOR_DESCRIPTIONS: tuple[EnergyControlProSensorDescription, ...] = (
    EnergyControlProSensorDescription(
        key="solar_w",
        name="Solar Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:solar-power",
    ),
    EnergyControlProSensorDescription(
        key="load_w",
        name="Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:home-lightning-bolt",
    ),
    EnergyControlProSensorDescription(
        key="surplus_w",
        name="Surplus Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:transmission-tower-export",
    ),
    EnergyControlProSensorDescription(
        key="grid_import_w",
        name="Grid Import Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:transmission-tower-import",
    ),
    EnergyControlProSensorDescription(
        key="grid_export_w",
        name="Grid Export Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:transmission-tower-export",
    ),
    EnergyControlProSensorDescription(
        key="energy_state",
        name="Energy State",
        icon="mdi:flash",
    ),
    EnergyControlProSensorDescription(
        key="export_duration_min",
        name="Export Duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
    ),
    EnergyControlProSensorDescription(
        key="import_duration_min",
        name="Import Duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
    ),
    EnergyControlProSensorDescription(
        key="last_action",
        name="Energy Control Pro Last Action",
        icon="mdi:clipboard-text-clock-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Energy Control Pro sensors from a config entry."""
    coordinator: EnergyControlProCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        EnergyControlProSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class EnergyControlProSensor(
    CoordinatorEntity[EnergyControlProCoordinator],
    SensorEntity,
):
    """Representation of an Energy Control Pro sensor."""

    entity_description: EnergyControlProSensorDescription
    _attr_has_entity_name = True
    def __init__(
        self,
        coordinator: EnergyControlProCoordinator,
        entry: ConfigEntry,
        description: EnergyControlProSensorDescription,
    ) -> None:
        """Initialize sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> int | str | None:
        """Return the current sensor value."""
        return self.coordinator.data.get(self.entity_description.key)
