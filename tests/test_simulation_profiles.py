from datetime import datetime

from custom_components.energy_control_pro.const import (
    PROFILE_CLOUDY_DAY,
    PROFILE_SUNNY_DAY,
    PROFILE_WINTER_DAY,
)
from custom_components.energy_control_pro.logic import simulate


def test_sunny_day_produces_more_solar_than_cloudy_day_at_same_hour() -> None:
    now = datetime(2026, 6, 21, 12, 0, 0)

    sunny_solar, _ = simulate(
        PROFILE_SUNNY_DAY,
        now,
        cloud_noise=0.0,
        appliance_noise=0.0,
    )
    cloudy_solar, _ = simulate(
        PROFILE_CLOUDY_DAY,
        now,
        cloud_noise=0.0,
        appliance_noise=0.0,
    )

    assert sunny_solar > cloudy_solar


def test_winter_day_produces_less_solar_than_sunny_day_at_same_hour() -> None:
    now = datetime(2026, 6, 21, 12, 0, 0)

    winter_solar, _ = simulate(
        PROFILE_WINTER_DAY,
        now,
        cloud_noise=0.0,
        appliance_noise=0.0,
    )
    sunny_solar, _ = simulate(
        PROFILE_SUNNY_DAY,
        now,
        cloud_noise=0.0,
        appliance_noise=0.0,
    )

    assert winter_solar < sunny_solar


def test_night_time_solar_is_zero_for_all_profiles() -> None:
    night = datetime(2026, 6, 21, 2, 0, 0)

    for profile in (PROFILE_SUNNY_DAY, PROFILE_CLOUDY_DAY, PROFILE_WINTER_DAY):
        solar_w, _ = simulate(
            profile,
            night,
            cloud_noise=0.0,
            appliance_noise=0.0,
        )
        assert solar_w == 0
