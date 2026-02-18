from datetime import datetime, timedelta

from custom_components.energy_control_pro.logic import (
    ENERGY_STATE_BALANCED,
    ENERGY_STATE_EXPORTING,
    ENERGY_STATE_IMPORTING,
    derive_energy_state,
    reset_export_alert_if_not_exporting,
    should_trigger_export_alert,
    should_trigger_import_alert,
    update_state_durations,
)


def test_energy_state_transitions_with_threshold() -> None:
    assert derive_energy_state(150, 0, threshold_w=100) == ENERGY_STATE_IMPORTING
    assert derive_energy_state(0, 180, threshold_w=100) == ENERGY_STATE_EXPORTING
    assert derive_energy_state(80, 40, threshold_w=100) == ENERGY_STATE_BALANCED


def test_duration_counter_logic() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)

    import_start, export_start, import_min, export_min = update_state_durations(
        now,
        ENERGY_STATE_IMPORTING,
        import_start=None,
        export_start=None,
    )
    assert import_start == now
    assert export_start is None
    assert import_min == 0
    assert export_min == 0

    later = now + timedelta(minutes=7, seconds=30)
    import_start, export_start, import_min, export_min = update_state_durations(
        later,
        ENERGY_STATE_IMPORTING,
        import_start=import_start,
        export_start=export_start,
    )
    assert import_min == 7
    assert export_min == 0

    switch = later + timedelta(minutes=1)
    import_start, export_start, import_min, export_min = update_state_durations(
        switch,
        ENERGY_STATE_EXPORTING,
        import_start=import_start,
        export_start=export_start,
    )
    assert import_start is None
    assert export_start == switch
    assert import_min == 0
    assert export_min == 0


def test_alert_trigger_logic() -> None:
    assert should_trigger_export_alert(
        grid_export_w=1200,
        export_threshold_w=800,
        export_duration_min=11,
        duration_threshold_min=10,
        export_alert_sent=False,
    )
    assert not should_trigger_export_alert(
        grid_export_w=1200,
        export_threshold_w=800,
        export_duration_min=9,
        duration_threshold_min=10,
        export_alert_sent=False,
    )

    assert should_trigger_import_alert(
        grid_import_w=1400,
        solar_w=450,
        import_threshold_w=800,
        import_alert_sent=False,
    )
    assert not should_trigger_import_alert(
        grid_import_w=1400,
        solar_w=250,
        import_threshold_w=800,
        import_alert_sent=False,
    )


def test_energy_state_noise_threshold_balanced() -> None:
    assert derive_energy_state(95, 100, threshold_w=100) == ENERGY_STATE_BALANCED
    assert derive_energy_state(100, 100, threshold_w=100) == ENERGY_STATE_BALANCED


def test_export_duration_resets_when_not_exporting() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    export_start = now - timedelta(minutes=9)
    _, export_start_after, _, export_duration_min = update_state_durations(
        now,
        ENERGY_STATE_BALANCED,
        import_start=None,
        export_start=export_start,
    )
    assert export_start_after is None
    assert export_duration_min == 0


def test_import_duration_resets_when_not_importing() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    import_start = now - timedelta(minutes=6)
    import_start_after, _, import_duration_min, _ = update_state_durations(
        now,
        ENERGY_STATE_BALANCED,
        import_start=import_start,
        export_start=None,
    )
    assert import_start_after is None
    assert import_duration_min == 0


def test_export_alert_sent_once_per_event() -> None:
    assert should_trigger_export_alert(
        grid_export_w=1500,
        export_threshold_w=800,
        export_duration_min=12,
        duration_threshold_min=10,
        export_alert_sent=False,
    )
    assert not should_trigger_export_alert(
        grid_export_w=1500,
        export_threshold_w=800,
        export_duration_min=13,
        duration_threshold_min=10,
        export_alert_sent=True,
    )


def test_export_alert_resets_after_export_stops() -> None:
    assert not reset_export_alert_if_not_exporting(
        export_alert_sent=True,
        energy_state=ENERGY_STATE_BALANCED,
    )
