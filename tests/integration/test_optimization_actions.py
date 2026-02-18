from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")
pytest.importorskip("homeassistant")
pytestmark = pytest.mark.integration

from custom_components.energy_control_pro.coordinator import EnergyControlProCoordinator
from custom_components.energy_control_pro.const import (
    CONF_DURATION_THRESHOLD_MIN,
    CONF_EXPORT_THRESHOLD_W,
    CONF_IMPORT_THRESHOLD_W,
    CONF_LOAD_1_ENTITY,
    CONF_LOAD_1_MIN_ON_TIME_MIN,
    CONF_LOAD_1_MIN_SURPLUS_W,
    CONF_LOAD_1_PRIORITY,
    CONF_OPTIMIZATION_ENABLED,
    CONF_PROFILE,
    CONF_SIMULATION,
    CONF_STRATEGY,
    PROFILE_SUNNY_DAY,
    STRATEGY_MAXIMIZE_SELF_CONSUMPTION,
)


@pytest.mark.asyncio
async def test_optimization_turns_on_load_when_exporting_stable(hass) -> None:  # type: ignore[no-untyped-def]
    hass.services.async_call = AsyncMock()
    hass.states.async_set("switch.test_load_1", "off")

    coordinator = EnergyControlProCoordinator(
        hass,
        SimpleNamespace(
            options={
                CONF_SIMULATION: True,
                CONF_PROFILE: PROFILE_SUNNY_DAY,
                CONF_OPTIMIZATION_ENABLED: True,
                CONF_STRATEGY: STRATEGY_MAXIMIZE_SELF_CONSUMPTION,
                CONF_IMPORT_THRESHOLD_W: 800,
                CONF_EXPORT_THRESHOLD_W: 5000,  # avoid export alert side effects
                CONF_DURATION_THRESHOLD_MIN: 1,
                CONF_LOAD_1_ENTITY: "switch.test_load_1",
                CONF_LOAD_1_MIN_SURPLUS_W: 1000,
                CONF_LOAD_1_MIN_ON_TIME_MIN: 5,
                CONF_LOAD_1_PRIORITY: 1,
            },
            data={},
        ),
    )
    coordinator._simulate_values = lambda profile, now: {  # type: ignore[method-assign]
        "solar_w": 3000,
        "load_w": 1000,
        "surplus_w": 2000,
        "grid_import_w": 0,
        "grid_export_w": 2000,
    }
    coordinator._export_start = datetime.now() - timedelta(minutes=2)

    await coordinator._async_update_data()

    hass.services.async_call.assert_any_call(
        "homeassistant",
        "turn_on",
        {"entity_id": "switch.test_load_1"},
        blocking=False,
    )


@pytest.mark.asyncio
async def test_optimization_turns_off_load_when_importing_stable(hass) -> None:  # type: ignore[no-untyped-def]
    hass.services.async_call = AsyncMock()
    hass.states.async_set("switch.test_load_1", "on")

    coordinator = EnergyControlProCoordinator(
        hass,
        SimpleNamespace(
            options={
                CONF_SIMULATION: True,
                CONF_PROFILE: PROFILE_SUNNY_DAY,
                CONF_OPTIMIZATION_ENABLED: True,
                CONF_STRATEGY: STRATEGY_MAXIMIZE_SELF_CONSUMPTION,
                CONF_IMPORT_THRESHOLD_W: 800,
                CONF_EXPORT_THRESHOLD_W: 5000,
                CONF_DURATION_THRESHOLD_MIN: 1,
                CONF_LOAD_1_ENTITY: "switch.test_load_1",
                CONF_LOAD_1_MIN_SURPLUS_W: 1000,
                CONF_LOAD_1_MIN_ON_TIME_MIN: 1,
                CONF_LOAD_1_PRIORITY: 1,
            },
            data={},
        ),
    )
    coordinator._simulate_values = lambda profile, now: {  # type: ignore[method-assign]
        "solar_w": 0,
        "load_w": 1500,
        "surplus_w": -1500,
        "grid_import_w": 1500,
        "grid_export_w": 0,
    }
    coordinator._import_start = datetime.now() - timedelta(minutes=2)
    coordinator._load_last_on["switch.test_load_1"] = datetime.now() - timedelta(minutes=3)

    await coordinator._async_update_data()

    hass.services.async_call.assert_any_call(
        "homeassistant",
        "turn_off",
        {"entity_id": "switch.test_load_1"},
        blocking=False,
    )


@pytest.mark.asyncio
async def test_optimization_off_does_not_call_services(hass) -> None:  # type: ignore[no-untyped-def]
    hass.services.async_call = AsyncMock()
    hass.states.async_set("switch.test_load_1", "off")

    coordinator = EnergyControlProCoordinator(
        hass,
        SimpleNamespace(
            options={
                CONF_SIMULATION: True,
                CONF_PROFILE: PROFILE_SUNNY_DAY,
                CONF_OPTIMIZATION_ENABLED: False,
                CONF_STRATEGY: STRATEGY_MAXIMIZE_SELF_CONSUMPTION,
                CONF_IMPORT_THRESHOLD_W: 800,
                CONF_EXPORT_THRESHOLD_W: 5000,
                CONF_DURATION_THRESHOLD_MIN: 1,
                CONF_LOAD_1_ENTITY: "switch.test_load_1",
                CONF_LOAD_1_MIN_SURPLUS_W: 1000,
                CONF_LOAD_1_MIN_ON_TIME_MIN: 5,
                CONF_LOAD_1_PRIORITY: 1,
            },
            data={},
        ),
    )
    coordinator._simulate_values = lambda profile, now: {  # type: ignore[method-assign]
        "solar_w": 3200,
        "load_w": 1000,
        "surplus_w": 2200,
        "grid_import_w": 0,
        "grid_export_w": 2200,
    }
    coordinator._export_start = datetime.now() - timedelta(minutes=2)

    await coordinator._async_update_data()

    calls = [
        call for call in hass.services.async_call.await_args_list
        if call.args and call.args[0] == "homeassistant"
    ]
    assert calls == []


@pytest.mark.asyncio
async def test_restart_does_not_trigger_immediate_action_without_conditions(hass) -> None:  # type: ignore[no-untyped-def]
    hass.services.async_call = AsyncMock()
    hass.states.async_set("switch.test_load_1", "off")

    entry = SimpleNamespace(
        options={
            CONF_SIMULATION: True,
            CONF_PROFILE: PROFILE_SUNNY_DAY,
            CONF_OPTIMIZATION_ENABLED: True,
            CONF_STRATEGY: STRATEGY_MAXIMIZE_SELF_CONSUMPTION,
            CONF_IMPORT_THRESHOLD_W: 800,
            CONF_EXPORT_THRESHOLD_W: 800,
            CONF_DURATION_THRESHOLD_MIN: 2,
            CONF_LOAD_1_ENTITY: "switch.test_load_1",
            CONF_LOAD_1_MIN_SURPLUS_W: 1200,
            CONF_LOAD_1_MIN_ON_TIME_MIN: 5,
            CONF_LOAD_1_PRIORITY: 1,
        },
        data={},
    )

    first = EnergyControlProCoordinator(hass, entry)
    first._simulate_values = lambda profile, now: {  # type: ignore[method-assign]
        "solar_w": 900,
        "load_w": 900,
        "surplus_w": 0,
        "grid_import_w": 0,
        "grid_export_w": 0,
    }
    await first._async_update_data()

    second = EnergyControlProCoordinator(hass, entry)
    second._simulate_values = lambda profile, now: {  # type: ignore[method-assign]
        "solar_w": 900,
        "load_w": 900,
        "surplus_w": 0,
        "grid_import_w": 0,
        "grid_export_w": 0,
    }
    await second._async_update_data()

    calls = [
        call for call in hass.services.async_call.await_args_list
        if call.args and call.args[0] == "homeassistant"
    ]
    assert calls == []
