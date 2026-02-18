"""Pure optimization decision engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LoadConfig:
    """Static config for one controllable load."""

    entity_id: str
    min_surplus_w: int
    min_on_time_min: int
    cooldown_min: int
    priority: int


@dataclass(frozen=True)
class LoadRuntime:
    """Runtime state for one controllable load."""

    is_on: bool
    last_on: datetime | None
    last_off: datetime | None


@dataclass(frozen=True)
class EngineAction:
    """Action decision returned by engine."""

    action: str
    entity_id: str
    reason: str


def _cooldown_passed(now: datetime, runtime: LoadRuntime, cooldown_min: int) -> bool:
    if runtime.last_off is None:
        return True
    return (now - runtime.last_off).total_seconds() >= max(0, cooldown_min) * 60


def _min_on_time_passed(now: datetime, runtime: LoadRuntime, min_on_time_min: int) -> bool:
    if runtime.last_on is None:
        return True
    return (now - runtime.last_on).total_seconds() >= max(0, min_on_time_min) * 60


def decide_turn_on(
    *,
    now: datetime,
    surplus_w: int,
    export_duration_min: int,
    min_surplus_duration_min: int,
    loads: list[LoadConfig],
    runtimes: dict[str, LoadRuntime],
) -> EngineAction | None:
    """Pick highest-priority OFF load eligible to turn on."""
    if export_duration_min < max(1, min_surplus_duration_min):
        return None

    candidates = sorted(loads, key=lambda item: item.priority)
    for load in candidates:
        runtime = runtimes[load.entity_id]
        if runtime.is_on:
            continue
        if surplus_w < max(0, load.min_surplus_w):
            continue
        if not _cooldown_passed(now, runtime, load.cooldown_min):
            continue
        return EngineAction(
            action="turn_on",
            entity_id=load.entity_id,
            reason=f"surplus {surplus_w}W for {export_duration_min} min",
        )
    return None


def decide_turn_off(
    *,
    now: datetime,
    grid_import_w: int,
    import_duration_min: int,
    import_threshold_w: int,
    duration_threshold_min: int,
    loads: list[LoadConfig],
    runtimes: dict[str, LoadRuntime],
) -> EngineAction | None:
    """Pick lowest-priority ON load eligible to turn off."""
    if grid_import_w < max(0, import_threshold_w):
        return None
    if import_duration_min < max(1, duration_threshold_min):
        return None

    candidates = sorted(loads, key=lambda item: item.priority, reverse=True)
    for load in candidates:
        runtime = runtimes[load.entity_id]
        if not runtime.is_on:
            continue
        if not _min_on_time_passed(now, runtime, load.min_on_time_min):
            continue
        return EngineAction(
            action="turn_off",
            entity_id=load.entity_id,
            reason=f"import {grid_import_w}W for {import_duration_min} min",
        )
    return None
