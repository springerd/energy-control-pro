"""Switch platform for Energy Control Pro."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EnergyControlProCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up optimization switch."""
    coordinator: EnergyControlProCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EnergyControlProOptimizationSwitch(coordinator, entry)])


class EnergyControlProOptimizationSwitch(
    CoordinatorEntity[EnergyControlProCoordinator],
    SwitchEntity,
):
    """Global optimization switch."""

    _attr_has_entity_name = True
    _attr_name = "Energy Control Pro Optimization"
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator: EnergyControlProCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_optimization"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("optimization_enabled", False))

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003
        await self.coordinator.async_set_optimization_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003
        await self.coordinator.async_set_optimization_enabled(False)
