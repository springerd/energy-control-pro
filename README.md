# Energy Control Pro

Stop exporting solar energy without noticing.

Detect sustained solar surplus and automatically control loads to maximize self-consumption, without writing YAML automations.

## Why This Exists

If you use solar panels with Home Assistant, you probably run into at least one of these:

- exporting energy to the grid without noticing,
- importing from the grid while solar is still available,
- maintaining fragile automations that are hard to tune.

Energy Control Pro centralizes detection, alerts, and load optimization in one integration.

## Quick Visual Example

Import the included dashboard and you get an at-a-glance energy view plus optimization state:

- `dashboards/energy_control_pro_overview.yaml`

You can monitor:

- live solar/load/grid balance,
- `switch.energy_control_pro_optimization` (ON/OFF),
- `sensor.energy_control_pro_last_action` (latest automation decision).

## What It Does

- Calculates solar/load/grid balance every 10 seconds.
- Detects sustained export and import conditions.
- Sends persistent Home Assistant alerts.
- Automatically controls up to 3 loads with priority logic.
- Includes anti-flapping protections (`min_on_time`, `cooldown`, duration thresholds).

## Example Scenario

Solar production: `1500W`  
Home load: `400W`  
Surplus: `1100W`

After 10 minutes above threshold, the integration can:

- turn ON `switch.boiler`,
- register `last_action` with a message like: `Turned ON switch.boiler (surplus 1100W for 10 min)`.

When solar drops and grid import stays above threshold long enough, it can:

- turn OFF `switch.boiler`,
- register `last_action` with a message like: `Turned OFF switch.boiler (import 900W for 10 min)`.

## Project Goal

The basic version remains free for the community.

## Features Implemented Today (FREE BASIC)

### 1. Energy Measurement and State

Sensors created by the integration:

- `solar_w`
- `load_w`
- `surplus_w`
- `grid_import_w`
- `grid_export_w`
- `energy_state` (`importing`, `exporting`, `balanced`)
- `import_duration_min`
- `export_duration_min`
- `last_action`

Update interval: every 10 seconds.

### 2. Simulation Mode

Included profiles:

- `sunny_day`
- `cloudy_day`
- `winter_day`

Designed to validate dashboards and automations without relying on real hardware.

### 3. Real Mode (No Simulation)

You can map real Home Assistant entities:

- `solar_power_entity` (must be in W and numeric)
- `load_power_entity` (must be in W and numeric)

The integration validates that both entities exist and use compatible units.

### 4. Persistent Alerts

Automatic notifications when:

- grid export is above threshold for a minimum duration,
- grid import happens while solar production is available.

Configurable via:

- `import_threshold_w`
- `export_threshold_w`
- `duration_threshold_min`

### 5. Load Optimization Engine

Control of up to 3 configurable loads (`switch` entities):

- `load_1_entity`, `load_2_entity`, `load_3_entity`
- `min_surplus_w`
- `min_on_time_min`
- `cooldown_min`
- `priority`

Available strategies:

- `maximize_self_consumption`
- `avoid_grid_import`
- `balanced`

Runtime entities:

- `switch.energy_control_pro_optimization`
- `select.energy_control_pro_strategy`
- `sensor.energy_control_pro_last_action`

## Installation (HACS)

1. Open HACS in Home Assistant.
2. Go to **Integrations**.
3. In **Custom repositories**, add this repository.
4. Category: **Integration**.
5. Search for **Energy Control Pro** and install it.
6. Restart Home Assistant.

## Configuration (UI, No YAML)

1. Go to **Settings -> Devices & Services**.
2. Click **Add Integration**.
3. Search for **Energy Control Pro**.
4. Configure simulation or real mode, thresholds, and optimization.

Notes:

- only one integration instance is allowed,
- all configuration is managed through the Home Assistant options flow.

## Dashboard Demo

Importable file:

- `dashboards/energy_control_pro_overview.yaml`

Includes power snapshot, 24h history, and grid status.

## Future

A Pro version may be introduced in the future, but core functionality will remain open.

## Development and Tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
pytest
```

Integration tests (Home Assistant test harness):

```bash
pytest -q -ra tests/integration
```
