"""Select platform for Energy Control Pro."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STRATEGIES
from .coordinator import EnergyControlProCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up optimization strategy select."""
    coordinator: EnergyControlProCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EnergyControlProStrategySelect(coordinator, entry)])


class EnergyControlProStrategySelect(
    CoordinatorEntity[EnergyControlProCoordinator],
    SelectEntity,
):
    """Runtime strategy selector."""

    _attr_has_entity_name = True
    _attr_name = "Energy Control Pro Strategy"
    _attr_options = list(STRATEGIES)
    _attr_icon = "mdi:sitemap-outline"

    def __init__(self, coordinator: EnergyControlProCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_strategy"

    @property
    def current_option(self) -> str | None:
        return str(self.coordinator.data.get("strategy", STRATEGIES[0]))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_strategy(option)
