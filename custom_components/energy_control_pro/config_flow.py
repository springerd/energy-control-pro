"""Config flow for Energy Control Pro."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DURATION_THRESHOLD_MIN,
    CONF_EXPORT_THRESHOLD_W,
    CONF_IMPORT_THRESHOLD_W,
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
    CONF_LOAD_POWER_ENTITY,
    CONF_OPTIMIZATION_ENABLED,
    CONF_PROFILE,
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
    DEFAULT_STRATEGY,
    DOMAIN,
    PROFILE_SUNNY_DAY,
    PROFILES,
    STRATEGIES,
)

DEFAULT_PROFILE = PROFILE_SUNNY_DAY


def _normalize_entity_value(value: Any) -> str | None:
    """Normalize entity selector values from forms/options."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value)


def _sanitize_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize and sanitize raw form input for storage/validation."""
    cleaned = dict(user_input)
    cleaned[CONF_SOLAR_POWER_ENTITY] = _normalize_entity_value(
        cleaned.get(CONF_SOLAR_POWER_ENTITY)
    )
    cleaned[CONF_LOAD_POWER_ENTITY] = _normalize_entity_value(
        cleaned.get(CONF_LOAD_POWER_ENTITY)
    )
    cleaned[CONF_LOAD_1_ENTITY] = _normalize_entity_value(cleaned.get(CONF_LOAD_1_ENTITY))
    cleaned[CONF_LOAD_2_ENTITY] = _normalize_entity_value(cleaned.get(CONF_LOAD_2_ENTITY))
    cleaned[CONF_LOAD_3_ENTITY] = _normalize_entity_value(cleaned.get(CONF_LOAD_3_ENTITY))
    return cleaned


class EnergyControlProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy Control Pro."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "EnergyControlProOptionsFlowHandler":
        """Get the options flow for this handler."""
        return EnergyControlProOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            cleaned_input = _sanitize_user_input(user_input)
            if _real_mode_missing_entities(cleaned_input):
                errors["base"] = "real_entities_required"
            else:
                validation_error = _validate_real_mode_entities(self.hass, cleaned_input)
                if validation_error:
                    errors["base"] = validation_error
                else:
                    await self.async_set_unique_id(DOMAIN)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Energy Control Pro",
                        data={},
                        options=cleaned_input,
                    )

        schema = _build_schema(
            simulation_default=True,
            profile_default=DEFAULT_PROFILE,
            solar_entity_default=None,
            load_entity_default=None,
            import_threshold_w_default=DEFAULT_IMPORT_THRESHOLD_W,
            export_threshold_w_default=DEFAULT_EXPORT_THRESHOLD_W,
            duration_threshold_min_default=DEFAULT_DURATION_THRESHOLD_MIN,
            optimization_enabled_default=DEFAULT_OPTIMIZATION_ENABLED,
            strategy_default=DEFAULT_STRATEGY,
            load_1_entity_default=None,
            load_1_min_surplus_w_default=DEFAULT_LOAD_MIN_SURPLUS_W,
            load_1_min_on_time_min_default=DEFAULT_LOAD_MIN_ON_TIME_MIN,
            load_1_cooldown_min_default=DEFAULT_LOAD_COOLDOWN_MIN,
            load_1_priority_default=1,
            load_2_entity_default=None,
            load_2_min_surplus_w_default=DEFAULT_LOAD_MIN_SURPLUS_W,
            load_2_min_on_time_min_default=DEFAULT_LOAD_MIN_ON_TIME_MIN,
            load_2_cooldown_min_default=DEFAULT_LOAD_COOLDOWN_MIN,
            load_2_priority_default=2,
            load_3_entity_default=None,
            load_3_min_surplus_w_default=DEFAULT_LOAD_MIN_SURPLUS_W,
            load_3_min_on_time_min_default=DEFAULT_LOAD_MIN_ON_TIME_MIN,
            load_3_cooldown_min_default=DEFAULT_LOAD_COOLDOWN_MIN,
            load_3_priority_default=3,
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class EnergyControlProOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Energy Control Pro."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage Energy Control Pro options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            cleaned_input = _sanitize_user_input(user_input)
            if _real_mode_missing_entities(cleaned_input):
                errors["base"] = "real_entities_required"
            else:
                validation_error = _validate_real_mode_entities(self.hass, cleaned_input)
                if validation_error:
                    errors["base"] = validation_error
                else:
                    return self.async_create_entry(title="", data=cleaned_input)

        simulation_default = self._config_entry.options.get(
            CONF_SIMULATION,
            self._config_entry.data.get(CONF_SIMULATION, True),
        )
        profile_default = self._config_entry.options.get(
            CONF_PROFILE,
            self._config_entry.data.get(CONF_PROFILE, DEFAULT_PROFILE),
        )
        solar_entity_default = _normalize_entity_value(self._config_entry.options.get(
            CONF_SOLAR_POWER_ENTITY,
            self._config_entry.data.get(CONF_SOLAR_POWER_ENTITY),
        ))
        load_entity_default = _normalize_entity_value(self._config_entry.options.get(
            CONF_LOAD_POWER_ENTITY,
            self._config_entry.data.get(CONF_LOAD_POWER_ENTITY),
        ))
        import_threshold_w_default = int(
            self._config_entry.options.get(
                CONF_IMPORT_THRESHOLD_W,
                self._config_entry.data.get(CONF_IMPORT_THRESHOLD_W, DEFAULT_IMPORT_THRESHOLD_W),
            )
        )
        export_threshold_w_default = int(
            self._config_entry.options.get(
                CONF_EXPORT_THRESHOLD_W,
                self._config_entry.data.get(CONF_EXPORT_THRESHOLD_W, DEFAULT_EXPORT_THRESHOLD_W),
            )
        )
        duration_threshold_min_default = int(
            self._config_entry.options.get(
                CONF_DURATION_THRESHOLD_MIN,
                self._config_entry.data.get(CONF_DURATION_THRESHOLD_MIN, DEFAULT_DURATION_THRESHOLD_MIN),
            )
        )
        optimization_enabled_default = bool(
            self._config_entry.options.get(
                CONF_OPTIMIZATION_ENABLED,
                self._config_entry.data.get(CONF_OPTIMIZATION_ENABLED, DEFAULT_OPTIMIZATION_ENABLED),
            )
        )
        strategy_default = str(
            self._config_entry.options.get(
                CONF_STRATEGY,
                self._config_entry.data.get(CONF_STRATEGY, DEFAULT_STRATEGY),
            )
        )
        load_1_entity_default = _normalize_entity_value(self._config_entry.options.get(
            CONF_LOAD_1_ENTITY,
            self._config_entry.data.get(CONF_LOAD_1_ENTITY),
        ))
        load_1_min_surplus_w_default = int(
            self._config_entry.options.get(
                CONF_LOAD_1_MIN_SURPLUS_W,
                self._config_entry.data.get(CONF_LOAD_1_MIN_SURPLUS_W, DEFAULT_LOAD_MIN_SURPLUS_W),
            )
        )
        load_1_min_on_time_min_default = int(
            self._config_entry.options.get(
                CONF_LOAD_1_MIN_ON_TIME_MIN,
                self._config_entry.data.get(CONF_LOAD_1_MIN_ON_TIME_MIN, DEFAULT_LOAD_MIN_ON_TIME_MIN),
            )
        )
        load_1_cooldown_min_default = int(
            self._config_entry.options.get(
                CONF_LOAD_1_COOLDOWN_MIN,
                self._config_entry.data.get(CONF_LOAD_1_COOLDOWN_MIN, DEFAULT_LOAD_COOLDOWN_MIN),
            )
        )
        load_1_priority_default = int(
            self._config_entry.options.get(
                CONF_LOAD_1_PRIORITY,
                self._config_entry.data.get(CONF_LOAD_1_PRIORITY, 1),
            )
        )
        load_2_entity_default = _normalize_entity_value(self._config_entry.options.get(
            CONF_LOAD_2_ENTITY,
            self._config_entry.data.get(CONF_LOAD_2_ENTITY),
        ))
        load_2_min_surplus_w_default = int(
            self._config_entry.options.get(
                CONF_LOAD_2_MIN_SURPLUS_W,
                self._config_entry.data.get(CONF_LOAD_2_MIN_SURPLUS_W, DEFAULT_LOAD_MIN_SURPLUS_W),
            )
        )
        load_2_min_on_time_min_default = int(
            self._config_entry.options.get(
                CONF_LOAD_2_MIN_ON_TIME_MIN,
                self._config_entry.data.get(CONF_LOAD_2_MIN_ON_TIME_MIN, DEFAULT_LOAD_MIN_ON_TIME_MIN),
            )
        )
        load_2_cooldown_min_default = int(
            self._config_entry.options.get(
                CONF_LOAD_2_COOLDOWN_MIN,
                self._config_entry.data.get(CONF_LOAD_2_COOLDOWN_MIN, DEFAULT_LOAD_COOLDOWN_MIN),
            )
        )
        load_2_priority_default = int(
            self._config_entry.options.get(
                CONF_LOAD_2_PRIORITY,
                self._config_entry.data.get(CONF_LOAD_2_PRIORITY, 2),
            )
        )
        load_3_entity_default = _normalize_entity_value(self._config_entry.options.get(
            CONF_LOAD_3_ENTITY,
            self._config_entry.data.get(CONF_LOAD_3_ENTITY),
        ))
        load_3_min_surplus_w_default = int(
            self._config_entry.options.get(
                CONF_LOAD_3_MIN_SURPLUS_W,
                self._config_entry.data.get(CONF_LOAD_3_MIN_SURPLUS_W, DEFAULT_LOAD_MIN_SURPLUS_W),
            )
        )
        load_3_min_on_time_min_default = int(
            self._config_entry.options.get(
                CONF_LOAD_3_MIN_ON_TIME_MIN,
                self._config_entry.data.get(CONF_LOAD_3_MIN_ON_TIME_MIN, DEFAULT_LOAD_MIN_ON_TIME_MIN),
            )
        )
        load_3_cooldown_min_default = int(
            self._config_entry.options.get(
                CONF_LOAD_3_COOLDOWN_MIN,
                self._config_entry.data.get(CONF_LOAD_3_COOLDOWN_MIN, DEFAULT_LOAD_COOLDOWN_MIN),
            )
        )
        load_3_priority_default = int(
            self._config_entry.options.get(
                CONF_LOAD_3_PRIORITY,
                self._config_entry.data.get(CONF_LOAD_3_PRIORITY, 3),
            )
        )

        schema = _build_schema(
            simulation_default=bool(simulation_default),
            profile_default=str(profile_default),
            solar_entity_default=solar_entity_default,
            load_entity_default=load_entity_default,
            import_threshold_w_default=import_threshold_w_default,
            export_threshold_w_default=export_threshold_w_default,
            duration_threshold_min_default=duration_threshold_min_default,
            optimization_enabled_default=optimization_enabled_default,
            strategy_default=strategy_default,
            load_1_entity_default=load_1_entity_default,
            load_1_min_surplus_w_default=load_1_min_surplus_w_default,
            load_1_min_on_time_min_default=load_1_min_on_time_min_default,
            load_1_cooldown_min_default=load_1_cooldown_min_default,
            load_1_priority_default=load_1_priority_default,
            load_2_entity_default=load_2_entity_default,
            load_2_min_surplus_w_default=load_2_min_surplus_w_default,
            load_2_min_on_time_min_default=load_2_min_on_time_min_default,
            load_2_cooldown_min_default=load_2_cooldown_min_default,
            load_2_priority_default=load_2_priority_default,
            load_3_entity_default=load_3_entity_default,
            load_3_min_surplus_w_default=load_3_min_surplus_w_default,
            load_3_min_on_time_min_default=load_3_min_on_time_min_default,
            load_3_cooldown_min_default=load_3_cooldown_min_default,
            load_3_priority_default=load_3_priority_default,
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


def _real_mode_missing_entities(user_input: dict[str, Any]) -> bool:
    """Return True when real mode is selected without required entities."""
    if user_input.get(CONF_SIMULATION, True):
        return False

    return not user_input.get(CONF_SOLAR_POWER_ENTITY) or not user_input.get(CONF_LOAD_POWER_ENTITY)


def _validate_real_mode_entities(hass: HomeAssistant, user_input: dict[str, Any]) -> str | None:
    """Validate mapped entities when simulation is disabled."""
    if user_input.get(CONF_SIMULATION, True):
        return None

    for key in (CONF_SOLAR_POWER_ENTITY, CONF_LOAD_POWER_ENTITY):
        entity_id = str(user_input.get(key, "") or "")
        state = hass.states.get(entity_id)
        if state is None:
            return "real_entity_not_found"
        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return "real_entity_unavailable"
        try:
            float(state.state)
        except (TypeError, ValueError):
            return "real_entity_not_numeric"

        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit and unit not in (UnitOfPower.WATT, UnitOfPower.KILO_WATT):
            return "real_entity_unit_not_w"

    return None


def _build_schema(
    *,
    simulation_default: bool,
    profile_default: str,
    solar_entity_default: str | None,
    load_entity_default: str | None,
    import_threshold_w_default: int,
    export_threshold_w_default: int,
    duration_threshold_min_default: int,
    optimization_enabled_default: bool,
    strategy_default: str,
    load_1_entity_default: str | None,
    load_1_min_surplus_w_default: int,
    load_1_min_on_time_min_default: int,
    load_1_cooldown_min_default: int,
    load_1_priority_default: int,
    load_2_entity_default: str | None,
    load_2_min_surplus_w_default: int,
    load_2_min_on_time_min_default: int,
    load_2_cooldown_min_default: int,
    load_2_priority_default: int,
    load_3_entity_default: str | None,
    load_3_min_surplus_w_default: int,
    load_3_min_on_time_min_default: int,
    load_3_cooldown_min_default: int,
    load_3_priority_default: int,
) -> vol.Schema:
    """Build shared schema for config and options forms."""
    schema: dict[Any, Any] = {
        vol.Required(CONF_SIMULATION, default=simulation_default): bool,
        vol.Required(
            CONF_PROFILE,
            default=profile_default,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(PROFILES),
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="profile",
            )
        ),
        vol.Required(
            CONF_IMPORT_THRESHOLD_W,
            default=import_threshold_w_default,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=20000, step=100, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_EXPORT_THRESHOLD_W,
            default=export_threshold_w_default,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=20000, step=100, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_DURATION_THRESHOLD_MIN,
            default=duration_threshold_min_default,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(CONF_OPTIMIZATION_ENABLED, default=optimization_enabled_default): bool,
        vol.Required(CONF_STRATEGY, default=strategy_default): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(STRATEGIES),
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="strategy",
            )
        ),
    }

    solar_key = (
        vol.Optional(CONF_SOLAR_POWER_ENTITY)
        if solar_entity_default is None
        else vol.Optional(CONF_SOLAR_POWER_ENTITY, default=solar_entity_default)
    )
    load_key = (
        vol.Optional(CONF_LOAD_POWER_ENTITY)
        if load_entity_default is None
        else vol.Optional(CONF_LOAD_POWER_ENTITY, default=load_entity_default)
    )

    schema[solar_key] = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["sensor"],
            multiple=False,
        )
    )
    schema[load_key] = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["sensor"],
            multiple=False,
        )
    )

    load_1_key = (
        vol.Optional(CONF_LOAD_1_ENTITY)
        if load_1_entity_default is None
        else vol.Optional(CONF_LOAD_1_ENTITY, default=load_1_entity_default)
    )
    load_2_key = (
        vol.Optional(CONF_LOAD_2_ENTITY)
        if load_2_entity_default is None
        else vol.Optional(CONF_LOAD_2_ENTITY, default=load_2_entity_default)
    )
    load_3_key = (
        vol.Optional(CONF_LOAD_3_ENTITY)
        if load_3_entity_default is None
        else vol.Optional(CONF_LOAD_3_ENTITY, default=load_3_entity_default)
    )
    switch_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["switch", "input_boolean"], multiple=False)
    )
    schema[load_1_key] = switch_selector
    schema[load_2_key] = switch_selector
    schema[load_3_key] = switch_selector

    schema[vol.Required(CONF_LOAD_1_MIN_SURPLUS_W, default=load_1_min_surplus_w_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=20000, step=100, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_1_MIN_ON_TIME_MIN, default=load_1_min_on_time_min_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_1_COOLDOWN_MIN, default=load_1_cooldown_min_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_1_PRIORITY, default=load_1_priority_default)] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=3, step=1, mode=selector.NumberSelectorMode.BOX)
    )

    schema[vol.Required(CONF_LOAD_2_MIN_SURPLUS_W, default=load_2_min_surplus_w_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=20000, step=100, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_2_MIN_ON_TIME_MIN, default=load_2_min_on_time_min_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_2_COOLDOWN_MIN, default=load_2_cooldown_min_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_2_PRIORITY, default=load_2_priority_default)] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=3, step=1, mode=selector.NumberSelectorMode.BOX)
    )

    schema[vol.Required(CONF_LOAD_3_MIN_SURPLUS_W, default=load_3_min_surplus_w_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=20000, step=100, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_3_MIN_ON_TIME_MIN, default=load_3_min_on_time_min_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_3_COOLDOWN_MIN, default=load_3_cooldown_min_default)] = (
        selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    )
    schema[vol.Required(CONF_LOAD_3_PRIORITY, default=load_3_priority_default)] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=3, step=1, mode=selector.NumberSelectorMode.BOX)
    )

    return vol.Schema(schema)
