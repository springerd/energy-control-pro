from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("homeassistant")

from custom_components.energy_control_pro.coordinator import EnergyControlProCoordinator
from custom_components.energy_control_pro.const import CONF_PROFILE, CONF_SIMULATION, PROFILE_SUNNY_DAY


class _DummyServices:
    async def async_call(self, domain, service, data, blocking=False):  # noqa: ANN001, ANN201
        return None


@pytest.mark.asyncio
async def test_async_update_data_returns_expected_keys_in_simulation_mode() -> None:
    coordinator = EnergyControlProCoordinator.__new__(EnergyControlProCoordinator)
    coordinator._entry = SimpleNamespace(  # type: ignore[attr-defined]
        options={CONF_SIMULATION: True, CONF_PROFILE: PROFILE_SUNNY_DAY},
        data={},
    )
    coordinator._import_start = None  # type: ignore[attr-defined]
    coordinator._export_start = None  # type: ignore[attr-defined]
    coordinator._import_alert_sent = False  # type: ignore[attr-defined]
    coordinator._export_alert_sent = False  # type: ignore[attr-defined]
    coordinator._load_last_on = {}  # type: ignore[attr-defined]
    coordinator._load_last_off = {}  # type: ignore[attr-defined]
    coordinator._optimization_enabled = False  # type: ignore[attr-defined]
    coordinator._strategy = "maximize_self_consumption"  # type: ignore[attr-defined]
    coordinator._last_action = "No actions yet"  # type: ignore[attr-defined]
    coordinator.hass = SimpleNamespace(services=_DummyServices())  # type: ignore[attr-defined]

    data = await coordinator._async_update_data()

    assert set(data.keys()) == {
        "solar_w",
        "load_w",
        "surplus_w",
        "grid_import_w",
        "grid_export_w",
        "energy_state",
        "import_duration_min",
        "export_duration_min",
        "optimization_enabled",
        "strategy",
        "last_action",
    }
