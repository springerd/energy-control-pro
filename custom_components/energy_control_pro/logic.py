"""Pure calculation helpers for Energy Control Pro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
import random

from .const import PROFILE_CLOUDY_DAY, PROFILE_SUNNY_DAY, PROFILE_WINTER_DAY


@dataclass(frozen=True)
class ProfileTuning:
    """Tuning values for generation/load simulation."""

    solar_peak_w: float
    day_length_h: float
    cloud_variability: float
    load_base_w: float
    load_evening_boost_w: float


PROFILE_TUNING: dict[str, ProfileTuning] = {
    PROFILE_SUNNY_DAY: ProfileTuning(
        solar_peak_w=6200,
        day_length_h=14,
        cloud_variability=0.06,
        load_base_w=950,
        load_evening_boost_w=850,
    ),
    PROFILE_CLOUDY_DAY: ProfileTuning(
        solar_peak_w=3600,
        day_length_h=12,
        cloud_variability=0.20,
        load_base_w=1050,
        load_evening_boost_w=800,
    ),
    PROFILE_WINTER_DAY: ProfileTuning(
        solar_peak_w=2400,
        day_length_h=9,
        cloud_variability=0.15,
        load_base_w=1250,
        load_evening_boost_w=1000,
    ),
}

ENERGY_STATE_IMPORTING = "importing"
ENERGY_STATE_EXPORTING = "exporting"
ENERGY_STATE_BALANCED = "balanced"


def simulate(
    profile: str,
    now: datetime,
    *,
    cloud_noise: float | None = None,
    appliance_noise: float | None = None,
    profile_tuning: dict[str, ProfileTuning] | None = None,
) -> tuple[int, int]:
    """Simulate solar/load power in W for a profile at a specific instant."""
    tuning_map = profile_tuning or PROFILE_TUNING
    tuning = tuning_map.get(profile, tuning_map[PROFILE_SUNNY_DAY])

    sunrise = 12 - (tuning.day_length_h / 2)
    sunset = 12 + (tuning.day_length_h / 2)
    hour = now.hour + (now.minute / 60) + (now.second / 3600)

    if sunrise <= hour <= sunset:
        phase = (hour - sunrise) / max((sunset - sunrise), 0.1)
        daylight_factor = math.sin(math.pi * phase)
    else:
        daylight_factor = 0.0

    cloud_noise_val = (
        cloud_noise
        if cloud_noise is not None
        else random.uniform(-tuning.cloud_variability, tuning.cloud_variability)
    )
    solar_w = max(0, int(tuning.solar_peak_w * daylight_factor * (1 + cloud_noise_val)))

    morning_peak = 250 * math.exp(-((hour - 7.5) ** 2) / 3.0)
    evening_peak = tuning.load_evening_boost_w * math.exp(-((hour - 19.0) ** 2) / 4.5)
    appliance_noise_val = (
        appliance_noise if appliance_noise is not None else random.uniform(-120, 180)
    )
    load_w = max(
        200,
        int(tuning.load_base_w + morning_peak + evening_peak + appliance_noise_val),
    )

    return solar_w, load_w


def calculate_balance(solar_w: int, load_w: int) -> dict[str, int]:
    """Calculate surplus/import/export values from solar and load power."""
    surplus_w = solar_w - load_w
    grid_import_w = max(0, -surplus_w)
    grid_export_w = max(0, surplus_w)

    return {
        "solar_w": solar_w,
        "load_w": load_w,
        "surplus_w": surplus_w,
        "grid_import_w": grid_import_w,
        "grid_export_w": grid_export_w,
    }


def derive_energy_state(
    grid_import_w: int,
    grid_export_w: int,
    threshold_w: int,
) -> str:
    """Classify current state with a noise threshold in W."""
    threshold = max(0, threshold_w)
    if grid_import_w > threshold:
        return ENERGY_STATE_IMPORTING
    if grid_export_w > threshold:
        return ENERGY_STATE_EXPORTING
    return ENERGY_STATE_BALANCED


def update_state_durations(
    now: datetime,
    energy_state: str,
    import_start: datetime | None,
    export_start: datetime | None,
) -> tuple[datetime | None, datetime | None, int, int]:
    """Update import/export timers based on current energy state."""
    import_duration_min = 0
    export_duration_min = 0

    if energy_state == ENERGY_STATE_IMPORTING:
        if import_start is None:
            import_start = now
        import_duration_min = int((now - import_start).total_seconds() // 60)
        export_start = None
    elif energy_state == ENERGY_STATE_EXPORTING:
        if export_start is None:
            export_start = now
        export_duration_min = int((now - export_start).total_seconds() // 60)
        import_start = None
    else:
        import_start = None
        export_start = None

    return import_start, export_start, import_duration_min, export_duration_min


def should_trigger_export_alert(
    *,
    grid_export_w: int,
    export_threshold_w: int,
    export_duration_min: int,
    duration_threshold_min: int,
    export_alert_sent: bool,
) -> bool:
    """Return True when export alert should be sent now."""
    return (
        not export_alert_sent
        and grid_export_w > max(0, export_threshold_w)
        and export_duration_min >= max(1, duration_threshold_min)
    )


def should_trigger_import_alert(
    *,
    grid_import_w: int,
    solar_w: int,
    import_threshold_w: int,
    import_alert_sent: bool,
) -> bool:
    """Return True when import-with-solar alert should be sent now."""
    return (
        not import_alert_sent
        and grid_import_w > max(0, import_threshold_w)
        and solar_w > 300
    )


def reset_export_alert_if_not_exporting(
    *,
    export_alert_sent: bool,
    energy_state: str,
) -> bool:
    """Reset export alert flag once export event ends."""
    if energy_state != ENERGY_STATE_EXPORTING:
        return False
    return export_alert_sent
