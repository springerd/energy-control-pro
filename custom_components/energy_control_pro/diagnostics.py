"""Diagnostics support for Energy Control Pro."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    runtime = {}
    if coordinator is not None:
        runtime = {
            "optimization_enabled": getattr(coordinator, "_optimization_enabled", None),
            "strategy": getattr(coordinator, "_strategy", None),
            "last_action": getattr(coordinator, "_last_action", None),
            "load_last_on": {
                k: v.isoformat() for k, v in getattr(coordinator, "_load_last_on", {}).items()
            },
            "load_last_off": {
                k: v.isoformat() for k, v in getattr(coordinator, "_load_last_off", {}).items()
            },
        }

    return {
        "entry_data": entry.data,
        "entry_options": entry.options,
        "runtime": runtime,
        "coordinator_data": coordinator.data if coordinator is not None else None,
    }
