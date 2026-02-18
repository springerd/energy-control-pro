"""Data coordinator for Energy Control Pro."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DURATION_THRESHOLD_MIN,
    CONF_EXPORT_THRESHOLD_W,
    CONF_LOAD_1_COOLDOWN_MIN,
    CONF_LOAD_1_ENTITY,
    CONF_LOAD_1_MIN_ON_TIME_MIN,
    CONF_LOAD_1_MIN_SURPLUS_W,
    CONF_LOAD_1_PRIORITY,
    CONF_LOAD_2_COOLDOWN_MIN,
    CONF_LOAD_2_ENTITY,
    CONF_LOAD_2_MIN_ON_TIME_MIN,
    CONF_LOAD_2_MIN_SURPLUS_W,
    CONF_LOAD_2_PRIORITY,
    CONF_LOAD_3_COOLDOWN_MIN,
    CONF_LOAD_3_ENTITY,
    CONF_LOAD_3_MIN_ON_TIME_MIN,
    CONF_LOAD_3_MIN_SURPLUS_W,
    CONF_LOAD_3_PRIORITY,
    CONF_OPTIMIZATION_ENABLED,
    CONF_PROFILE,
    CONF_IMPORT_THRESHOLD_W,
    CONF_LOAD_POWER_ENTITY,
    CONF_SIMULATION,
    CONF_SOLAR_POWER_ENTITY,
    CONF_STRATEGY,
    DEFAULT_DURATION_THRESHOLD_MIN,
    DEFAULT_EXPORT_THRESHOLD_W,
    DEFAULT_LOAD_COOLDOWN_MIN,
    DEFAULT_LOAD_MIN_ON_TIME_MIN,
    DEFAULT_LOAD_MIN_SURPLUS_W,
    DEFAULT_IMPORT_THRESHOLD_W,
    DEFAULT_OPTIMIZATION_ENABLED,
    DEFAULT_STATE_THRESHOLD_W,
    DEFAULT_STRATEGY,
    STRATEGY_AVOID_GRID_IMPORT,
    PROFILE_SUNNY_DAY,
)
from .logic import (
    ENERGY_STATE_EXPORTING,
    calculate_balance,
    derive_energy_state,
    reset_export_alert_if_not_exporting,
    should_trigger_export_alert,
    should_trigger_import_alert,
    simulate,
    update_state_durations,
)
from .optimization.engine import LoadConfig, LoadRuntime, decide_turn_off, decide_turn_on

_LOGGER = logging.getLogger(__name__)


class EnergyControlProCoordinator(DataUpdateCoordinator[dict[str, int | str]]):
    """Coordinate Energy Control Pro sensor updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._entry = entry
        self._import_start: datetime | None = None
        self._export_start: datetime | None = None
        self._import_alert_sent = False
        self._export_alert_sent = False
        self._load_last_on: dict[str, datetime] = {}
        self._load_last_off: dict[str, datetime] = {}
        self._optimization_enabled = bool(
            self._entry.options.get(
                CONF_OPTIMIZATION_ENABLED,
                self._entry.data.get(CONF_OPTIMIZATION_ENABLED, DEFAULT_OPTIMIZATION_ENABLED),
            )
        )
        self._strategy = str(
            self._entry.options.get(
                CONF_STRATEGY,
                self._entry.data.get(CONF_STRATEGY, DEFAULT_STRATEGY),
            )
        )
        self._last_action = "No actions yet"
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Energy Control Pro",
            update_interval=timedelta(seconds=10),
        )

    async def _async_update_data(self) -> dict[str, int | str]:
        """Fetch or simulate current values."""
        now = datetime.now()
        simulation = self._entry.options.get(
            CONF_SIMULATION,
            self._entry.data.get(CONF_SIMULATION, True),
        )
        profile = self._entry.options.get(
            CONF_PROFILE,
            self._entry.data.get(CONF_PROFILE, PROFILE_SUNNY_DAY),
        )

        if simulation:
            data = self._simulate_values(profile, now=now)
        else:
            data = self._real_values_from_entities()

        energy_state = derive_energy_state(
            grid_import_w=int(data["grid_import_w"]),
            grid_export_w=int(data["grid_export_w"]),
            threshold_w=DEFAULT_STATE_THRESHOLD_W,
        )
        self._import_start, self._export_start, import_duration_min, export_duration_min = (
            update_state_durations(now, energy_state, self._import_start, self._export_start)
        )
        data["energy_state"] = energy_state
        data["import_duration_min"] = import_duration_min
        data["export_duration_min"] = export_duration_min
        data["optimization_enabled"] = self._optimization_enabled
        data["strategy"] = self._strategy

        await self._async_process_alerts(data)
        await self._async_run_optimization(data, now=now)
        data["last_action"] = self._last_action
        return data

    async def async_set_optimization_enabled(self, enabled: bool) -> None:
        """Update optimization runtime status."""
        self._optimization_enabled = enabled
        if not enabled:
            self._last_action = "Optimization OFF"
        self.async_set_updated_data({**(self.data or {}), "optimization_enabled": enabled})

    async def async_set_strategy(self, strategy: str) -> None:
        """Update optimization strategy runtime value."""
        self._strategy = strategy
        self.async_set_updated_data({**(self.data or {}), "strategy": strategy})

    def _real_values_from_entities(self) -> dict[str, int]:
        """Read solar/load from mapped entities and derive all metrics in W."""
        solar_entity_id = str(self._get_option(CONF_SOLAR_POWER_ENTITY, "") or "")
        load_entity_id = str(self._get_option(CONF_LOAD_POWER_ENTITY, "") or "")

        if not solar_entity_id or not load_entity_id:
            raise UpdateFailed(
                "Real mode requires solar_power_entity and load_power_entity in options"
            )

        solar_w = self._read_power_w(solar_entity_id)
        load_w = self._read_power_w(load_entity_id)
        return calculate_balance(solar_w, load_w)

    def _read_power_w(self, entity_id: str) -> int:
        """Read one power entity in W and return a non-negative integer."""
        state = self.hass.states.get(entity_id)
        if state is None:
            raise UpdateFailed(f"Entity not found: {entity_id}")

        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            raise UpdateFailed(f"Entity state unavailable: {entity_id}")

        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit and unit not in (UnitOfPower.WATT, UnitOfPower.KILO_WATT):
            raise UpdateFailed(f"Entity {entity_id} must report power in W or kW")

        try:
            value = float(state.state)
        except (TypeError, ValueError) as err:
            raise UpdateFailed(f"Entity state is not numeric: {entity_id}") from err

        if unit == UnitOfPower.KILO_WATT:
            value = value * 1000

        return max(0, int(round(value)))

    async def _async_process_alerts(self, data: dict[str, int | str]) -> None:
        """Trigger persistent notifications when thresholds stay high long enough."""
        import_threshold_w = int(
            self._get_option(CONF_IMPORT_THRESHOLD_W, DEFAULT_IMPORT_THRESHOLD_W)
        )
        export_threshold_w = int(
            self._get_option(CONF_EXPORT_THRESHOLD_W, DEFAULT_EXPORT_THRESHOLD_W)
        )
        duration_threshold_min = int(
            self._get_option(CONF_DURATION_THRESHOLD_MIN, DEFAULT_DURATION_THRESHOLD_MIN)
        )

        solar_w = int(data.get("solar_w", 0))
        import_w = int(data.get("grid_import_w", 0))
        export_w = int(data.get("grid_export_w", 0))
        energy_state = str(data.get("energy_state", "balanced"))
        import_duration_min = int(data.get("import_duration_min", 0))
        export_duration_min = int(data.get("export_duration_min", 0))

        if should_trigger_export_alert(
            grid_export_w=export_w,
            export_threshold_w=export_threshold_w,
            export_duration_min=export_duration_min,
            duration_threshold_min=duration_threshold_min,
            export_alert_sent=self._export_alert_sent,
        ):
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Energy Control Pro: Prolonged Grid Export",
                    "message": (
                        f"Grid export is above {export_threshold_w} W for "
                        f"{duration_threshold_min} minutes. "
                        f"Current: {export_w} W, duration: {export_duration_min} min."
                    ),
                    "notification_id": "energy_control_pro_prolonged_grid_export",
                },
                blocking=False,
            )
            self._export_alert_sent = True
        self._export_alert_sent = reset_export_alert_if_not_exporting(
            export_alert_sent=self._export_alert_sent,
            energy_state=energy_state,
        )

        import_condition = (
            import_w > max(0, import_threshold_w) and solar_w > 300
        )
        if should_trigger_import_alert(
            grid_import_w=import_w,
            solar_w=solar_w,
            import_threshold_w=import_threshold_w,
            import_alert_sent=self._import_alert_sent,
        ):
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Energy Control Pro: Importing While Solar Available",
                    "message": (
                        "You are importing energy while solar production is available. "
                        f"Import: {import_w} W, Solar: {solar_w} W, "
                        f"duration: {import_duration_min} min."
                    ),
                    "notification_id": "energy_control_pro_import_while_solar",
                },
                blocking=False,
            )
            self._import_alert_sent = True
        if not import_condition:
            self._import_alert_sent = False

    async def _async_run_optimization(self, data: dict[str, int | str], *, now: datetime) -> None:
        """Run load optimization cycle and perform one action at most."""
        if not self._optimization_enabled:
            return

        loads = self._load_configs()
        if not loads:
            return

        runtimes = self._build_load_runtimes(loads)
        import_threshold_w = int(self._get_option(CONF_IMPORT_THRESHOLD_W, DEFAULT_IMPORT_THRESHOLD_W))
        duration_threshold_min = int(
            self._get_option(CONF_DURATION_THRESHOLD_MIN, DEFAULT_DURATION_THRESHOLD_MIN)
        )
        surplus_w = int(data.get("surplus_w", 0))
        grid_import_w = int(data.get("grid_import_w", 0))
        export_duration_min = int(data.get("export_duration_min", 0))
        import_duration_min = int(data.get("import_duration_min", 0))

        if self._strategy == STRATEGY_AVOID_GRID_IMPORT:
            action = decide_turn_off(
                now=now,
                grid_import_w=grid_import_w,
                import_duration_min=import_duration_min,
                import_threshold_w=import_threshold_w,
                duration_threshold_min=duration_threshold_min,
                loads=loads,
                runtimes=runtimes,
            ) or decide_turn_on(
                now=now,
                surplus_w=surplus_w,
                export_duration_min=export_duration_min,
                min_surplus_duration_min=duration_threshold_min,
                loads=loads,
                runtimes=runtimes,
            )
        else:
            action = decide_turn_on(
                now=now,
                surplus_w=surplus_w,
                export_duration_min=export_duration_min,
                min_surplus_duration_min=duration_threshold_min,
                loads=loads,
                runtimes=runtimes,
            ) or decide_turn_off(
                now=now,
                grid_import_w=grid_import_w,
                import_duration_min=import_duration_min,
                import_threshold_w=import_threshold_w,
                duration_threshold_min=duration_threshold_min,
                loads=loads,
                runtimes=runtimes,
            )

        if action is None:
            return

        service = "turn_on" if action.action == "turn_on" else "turn_off"
        await self.hass.services.async_call(
            "homeassistant",
            service,
            {"entity_id": action.entity_id},
            blocking=False,
        )
        if action.action == "turn_on":
            self._load_last_on[action.entity_id] = now
        else:
            self._load_last_off[action.entity_id] = now

        self._last_action = (
            f"Turned {action.action.upper().replace('TURN_', '')} {action.entity_id} ({action.reason})"
        )
        _LOGGER.info("Optimization action: %s", self._last_action)

    def _load_configs(self) -> list[LoadConfig]:
        """Read configured load slots from options."""
        slots = (
            (
                CONF_LOAD_1_ENTITY,
                CONF_LOAD_1_MIN_SURPLUS_W,
                CONF_LOAD_1_MIN_ON_TIME_MIN,
                CONF_LOAD_1_COOLDOWN_MIN,
                CONF_LOAD_1_PRIORITY,
                1,
            ),
            (
                CONF_LOAD_2_ENTITY,
                CONF_LOAD_2_MIN_SURPLUS_W,
                CONF_LOAD_2_MIN_ON_TIME_MIN,
                CONF_LOAD_2_COOLDOWN_MIN,
                CONF_LOAD_2_PRIORITY,
                2,
            ),
            (
                CONF_LOAD_3_ENTITY,
                CONF_LOAD_3_MIN_SURPLUS_W,
                CONF_LOAD_3_MIN_ON_TIME_MIN,
                CONF_LOAD_3_COOLDOWN_MIN,
                CONF_LOAD_3_PRIORITY,
                3,
            ),
        )
        loads: list[LoadConfig] = []
        for entity_key, surplus_key, min_on_key, cooldown_key, priority_key, default_priority in slots:
            entity_id = str(self._get_option(entity_key, "") or "").strip()
            if not entity_id:
                continue
            loads.append(
                LoadConfig(
                    entity_id=entity_id,
                    min_surplus_w=int(self._get_option(surplus_key, DEFAULT_LOAD_MIN_SURPLUS_W)),
                    min_on_time_min=int(self._get_option(min_on_key, DEFAULT_LOAD_MIN_ON_TIME_MIN)),
                    cooldown_min=int(self._get_option(cooldown_key, DEFAULT_LOAD_COOLDOWN_MIN)),
                    priority=int(self._get_option(priority_key, default_priority)),
                )
            )
        return loads

    def _build_load_runtimes(self, loads: list[LoadConfig]) -> dict[str, LoadRuntime]:
        """Build runtime map for configured loads from HA states and timers."""
        runtimes: dict[str, LoadRuntime] = {}
        for load in loads:
            state = self.hass.states.get(load.entity_id)
            is_on = bool(state and state.state == "on")
            runtimes[load.entity_id] = LoadRuntime(
                is_on=is_on,
                last_on=self._load_last_on.get(load.entity_id),
                last_off=self._load_last_off.get(load.entity_id),
            )
        return runtimes

    def _get_option(self, key: str, default: int | bool | str) -> int | bool | str:
        """Return current option value, falling back to entry data/default."""
        return self._entry.options.get(key, self._entry.data.get(key, default))

    def _simulate_values(self, profile: str, *, now: datetime) -> dict[str, int]:
        """Generate realistic-ish power values for the selected profile."""
        solar_w, load_w = simulate(profile, now=now)
        return calculate_balance(solar_w, load_w)
