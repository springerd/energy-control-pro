from datetime import datetime, timedelta

from custom_components.energy_control_pro.optimization.engine import (
    LoadConfig,
    LoadRuntime,
    decide_turn_off,
    decide_turn_on,
)


def test_surplus_stable_turns_on_highest_priority_load() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [
        LoadConfig("switch.load_b", min_surplus_w=800, min_on_time_min=5, cooldown_min=5, priority=2),
        LoadConfig("switch.load_a", min_surplus_w=900, min_on_time_min=5, cooldown_min=5, priority=1),
    ]
    runtimes = {
        "switch.load_a": LoadRuntime(is_on=False, last_on=None, last_off=None),
        "switch.load_b": LoadRuntime(is_on=False, last_on=None, last_off=None),
    }

    action = decide_turn_on(
        now=now,
        surplus_w=1200,
        export_duration_min=12,
        min_surplus_duration_min=10,
        loads=loads,
        runtimes=runtimes,
    )

    assert action is not None
    assert action.action == "turn_on"
    assert action.entity_id == "switch.load_a"


def test_import_stable_turns_off_lowest_priority_load() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [
        LoadConfig("switch.load_a", min_surplus_w=800, min_on_time_min=5, cooldown_min=5, priority=1),
        LoadConfig("switch.load_b", min_surplus_w=800, min_on_time_min=5, cooldown_min=5, priority=3),
    ]
    runtimes = {
        "switch.load_a": LoadRuntime(is_on=True, last_on=now - timedelta(minutes=10), last_off=None),
        "switch.load_b": LoadRuntime(is_on=True, last_on=now - timedelta(minutes=10), last_off=None),
    }

    action = decide_turn_off(
        now=now,
        grid_import_w=1500,
        import_duration_min=11,
        import_threshold_w=800,
        duration_threshold_min=10,
        loads=loads,
        runtimes=runtimes,
    )

    assert action is not None
    assert action.action == "turn_off"
    assert action.entity_id == "switch.load_b"


def test_min_on_time_blocks_turn_off() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [LoadConfig("switch.load_a", min_surplus_w=800, min_on_time_min=15, cooldown_min=5, priority=1)]
    runtimes = {
        "switch.load_a": LoadRuntime(is_on=True, last_on=now - timedelta(minutes=5), last_off=None),
    }

    action = decide_turn_off(
        now=now,
        grid_import_w=1500,
        import_duration_min=12,
        import_threshold_w=800,
        duration_threshold_min=10,
        loads=loads,
        runtimes=runtimes,
    )

    assert action is None


def test_cooldown_blocks_turn_on() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [LoadConfig("switch.load_a", min_surplus_w=800, min_on_time_min=5, cooldown_min=20, priority=1)]
    runtimes = {
        "switch.load_a": LoadRuntime(is_on=False, last_on=None, last_off=now - timedelta(minutes=5)),
    }

    action = decide_turn_on(
        now=now,
        surplus_w=1500,
        export_duration_min=12,
        min_surplus_duration_min=10,
        loads=loads,
        runtimes=runtimes,
    )

    assert action is None


def test_does_not_turn_off_before_min_on_time() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [LoadConfig("switch.load_a", min_surplus_w=800, min_on_time_min=20, cooldown_min=5, priority=1)]
    runtimes = {
        "switch.load_a": LoadRuntime(is_on=True, last_on=now - timedelta(minutes=3), last_off=None),
    }
    action = decide_turn_off(
        now=now,
        grid_import_w=1200,
        import_duration_min=15,
        import_threshold_w=800,
        duration_threshold_min=10,
        loads=loads,
        runtimes=runtimes,
    )
    assert action is None


def test_does_not_turn_on_during_cooldown() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [LoadConfig("switch.load_a", min_surplus_w=600, min_on_time_min=5, cooldown_min=15, priority=1)]
    runtimes = {
        "switch.load_a": LoadRuntime(is_on=False, last_on=None, last_off=now - timedelta(minutes=2)),
    }
    action = decide_turn_on(
        now=now,
        surplus_w=1500,
        export_duration_min=12,
        min_surplus_duration_min=10,
        loads=loads,
        runtimes=runtimes,
    )
    assert action is None


def test_does_not_repeat_turn_on_when_already_on() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [LoadConfig("switch.load_a", min_surplus_w=600, min_on_time_min=5, cooldown_min=5, priority=1)]
    runtimes = {
        "switch.load_a": LoadRuntime(is_on=True, last_on=now - timedelta(minutes=6), last_off=None),
    }
    action = decide_turn_on(
        now=now,
        surplus_w=2000,
        export_duration_min=15,
        min_surplus_duration_min=10,
        loads=loads,
        runtimes=runtimes,
    )
    assert action is None


def test_priority_turns_on_highest_priority_first() -> None:
    now = datetime(2026, 2, 15, 12, 0, 0)
    loads = [
        LoadConfig("switch.load_3", min_surplus_w=700, min_on_time_min=5, cooldown_min=5, priority=3),
        LoadConfig("switch.load_1", min_surplus_w=700, min_on_time_min=5, cooldown_min=5, priority=1),
        LoadConfig("switch.load_2", min_surplus_w=700, min_on_time_min=5, cooldown_min=5, priority=2),
    ]
    runtimes = {
        "switch.load_1": LoadRuntime(is_on=False, last_on=None, last_off=None),
        "switch.load_2": LoadRuntime(is_on=False, last_on=None, last_off=None),
        "switch.load_3": LoadRuntime(is_on=False, last_on=None, last_off=None),
    }
    action = decide_turn_on(
        now=now,
        surplus_w=1000,
        export_duration_min=12,
        min_surplus_duration_min=10,
        loads=loads,
        runtimes=runtimes,
    )
    assert action is not None
    assert action.entity_id == "switch.load_1"
