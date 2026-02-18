from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfPower

from custom_components.energy_control_pro.config_flow import _validate_real_mode_entities
from custom_components.energy_control_pro.const import (
    CONF_LOAD_POWER_ENTITY,
    CONF_SIMULATION,
    CONF_SOLAR_POWER_ENTITY,
)
from custom_components.energy_control_pro.coordinator import EnergyControlProCoordinator


def _fake_hass_with_states(states_map: dict[str, SimpleNamespace]) -> SimpleNamespace:
    return SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: states_map.get(entity_id)))


def test_validate_real_mode_entities_accepts_kw_units() -> None:
    hass = _fake_hass_with_states(
        {
            "sensor.solar_kw": SimpleNamespace(
                state="2.4",
                attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT},
            ),
            "sensor.load_kw": SimpleNamespace(
                state="1.1",
                attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT},
            ),
        }
    )
    user_input = {
        CONF_SIMULATION: False,
        CONF_SOLAR_POWER_ENTITY: "sensor.solar_kw",
        CONF_LOAD_POWER_ENTITY: "sensor.load_kw",
    }

    assert _validate_real_mode_entities(hass, user_input) is None


@pytest.mark.asyncio
async def test_read_power_w_converts_kw_to_w() -> None:
    coordinator = EnergyControlProCoordinator.__new__(EnergyControlProCoordinator)
    coordinator.hass = _fake_hass_with_states(  # type: ignore[attr-defined]
        {
            "sensor.solar_kw": SimpleNamespace(
                state="1.75",
                attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT},
            )
        }
    )

    assert coordinator._read_power_w("sensor.solar_kw") == 1750
