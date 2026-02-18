"""Constants for Energy Control Pro."""

from __future__ import annotations

DOMAIN = "energy_control_pro"

CONF_SIMULATION = "simulation"
CONF_PROFILE = "profile"
CONF_SOLAR_POWER_ENTITY = "solar_power_entity"
CONF_LOAD_POWER_ENTITY = "load_power_entity"
CONF_IMPORT_THRESHOLD_W = "import_threshold_w"
CONF_EXPORT_THRESHOLD_W = "export_threshold_w"
CONF_DURATION_THRESHOLD_MIN = "duration_threshold_min"
CONF_OPTIMIZATION_ENABLED = "optimization_enabled"
CONF_STRATEGY = "strategy"
CONF_LOAD_1_ENTITY = "load_1_entity"
CONF_LOAD_1_MIN_SURPLUS_W = "load_1_min_surplus_w"
CONF_LOAD_1_MIN_ON_TIME_MIN = "load_1_min_on_time_min"
CONF_LOAD_1_COOLDOWN_MIN = "load_1_cooldown_min"
CONF_LOAD_1_PRIORITY = "load_1_priority"
CONF_LOAD_2_ENTITY = "load_2_entity"
CONF_LOAD_2_MIN_SURPLUS_W = "load_2_min_surplus_w"
CONF_LOAD_2_MIN_ON_TIME_MIN = "load_2_min_on_time_min"
CONF_LOAD_2_COOLDOWN_MIN = "load_2_cooldown_min"
CONF_LOAD_2_PRIORITY = "load_2_priority"
CONF_LOAD_3_ENTITY = "load_3_entity"
CONF_LOAD_3_MIN_SURPLUS_W = "load_3_min_surplus_w"
CONF_LOAD_3_MIN_ON_TIME_MIN = "load_3_min_on_time_min"
CONF_LOAD_3_COOLDOWN_MIN = "load_3_cooldown_min"
CONF_LOAD_3_PRIORITY = "load_3_priority"

DEFAULT_IMPORT_THRESHOLD_W = 800
DEFAULT_EXPORT_THRESHOLD_W = 800
DEFAULT_DURATION_THRESHOLD_MIN = 10
DEFAULT_STATE_THRESHOLD_W = 100
DEFAULT_OPTIMIZATION_ENABLED = False
DEFAULT_STRATEGY = "maximize_self_consumption"

DEFAULT_LOAD_MIN_SURPLUS_W = 1200
DEFAULT_LOAD_MIN_ON_TIME_MIN = 10
DEFAULT_LOAD_COOLDOWN_MIN = 10

STRATEGY_MAXIMIZE_SELF_CONSUMPTION = "maximize_self_consumption"
STRATEGY_AVOID_GRID_IMPORT = "avoid_grid_import"
STRATEGY_BALANCED = "balanced"
STRATEGIES: tuple[str, ...] = (
    STRATEGY_MAXIMIZE_SELF_CONSUMPTION,
    STRATEGY_AVOID_GRID_IMPORT,
    STRATEGY_BALANCED,
)

LOAD_SLOTS: tuple[dict[str, str], ...] = (
    {
        "entity": CONF_LOAD_1_ENTITY,
        "min_surplus_w": CONF_LOAD_1_MIN_SURPLUS_W,
        "min_on_time_min": CONF_LOAD_1_MIN_ON_TIME_MIN,
        "cooldown_min": CONF_LOAD_1_COOLDOWN_MIN,
        "priority": CONF_LOAD_1_PRIORITY,
    },
    {
        "entity": CONF_LOAD_2_ENTITY,
        "min_surplus_w": CONF_LOAD_2_MIN_SURPLUS_W,
        "min_on_time_min": CONF_LOAD_2_MIN_ON_TIME_MIN,
        "cooldown_min": CONF_LOAD_2_COOLDOWN_MIN,
        "priority": CONF_LOAD_2_PRIORITY,
    },
    {
        "entity": CONF_LOAD_3_ENTITY,
        "min_surplus_w": CONF_LOAD_3_MIN_SURPLUS_W,
        "min_on_time_min": CONF_LOAD_3_MIN_ON_TIME_MIN,
        "cooldown_min": CONF_LOAD_3_COOLDOWN_MIN,
        "priority": CONF_LOAD_3_PRIORITY,
    },
)

PROFILE_SUNNY_DAY = "sunny_day"
PROFILE_CLOUDY_DAY = "cloudy_day"
PROFILE_WINTER_DAY = "winter_day"

PROFILES: tuple[str, ...] = (
    PROFILE_SUNNY_DAY,
    PROFILE_CLOUDY_DAY,
    PROFILE_WINTER_DAY,
)
