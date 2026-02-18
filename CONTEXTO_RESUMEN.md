# CONTEXTO RESUMEN DETALLADO (Energy Control Pro)

Fecha de actualización: 2026-02-15
Repo: `/home/springerd/projects/ha-addon`

## TESTS (RESUMEN RÁPIDO)

Estado: creados, no ejecutados en este entorno del asistente por falta de `pytest` en runtime.

Archivos de test existentes:
- `tests/test_balance.py`
- `tests/test_simulation_profiles.py`
- `tests/test_coordinator_sanity.py` (opcional, hace `importorskip("homeassistant")`)

Cobertura implementada:
1. `solar > load` (export)
2. `solar < load` (import)
3. `solar == load` (balanceado)
4. `sunny_day` produce más solar que `cloudy_day` a misma hora
5. `winter_day` produce menos solar que `sunny_day` a misma hora
6. Noche -> `solar = 0`

Comando para ejecutarlos:
```bash
python3 -m pytest
```

## 1) Estado general del proyecto

Se ha construido una integración custom de Home Assistant (`energy_control_pro`) preparada para HACS, con:
- Config flow + options flow.
- Simulación por perfiles.
- Modo real con mapeo de entidades.
- Sensores de potencia derivados (incluyendo import/export de red).
- Alertas simples con `persistent_notification.create`.
- Dashboard demo importable (cards core).
- Skill local para despliegue por SMB en Linux/WSL2 (`.sh`).
- Refactor de lógica pura para permitir tests unitarios sin HA.

## 2) Estructura relevante actual

- `hacs.json`
- `README.md`
- `dashboards/energy_control_pro_overview.yaml`
- `skills/ha-smb-deploy/SKILL.md`
- `skills/ha-smb-deploy/scripts/deploy_ha_smb.sh`
- `custom_components/energy_control_pro/`
  - `manifest.json`
  - `__init__.py`
  - `const.py`
  - `config_flow.py`
  - `coordinator.py`
  - `logic.py` (nuevo: lógica pura)
  - `sensor.py`
  - `translations/en.json`
- `tests/`
  - `test_balance.py`
  - `test_simulation_profiles.py`
  - `test_coordinator_sanity.py` (opcional, con `importorskip("homeassistant")`)
- `pyproject.toml` (config mínima de pytest)

## 3) Funcionalidad implementada

### 3.1 Configuración (Config Flow + Options)

Archivo: `custom_components/energy_control_pro/config_flow.py`

La integración crea la entry con:
- `data={}` (mínimo fijo)
- `options=user_input`

Opciones configurables:
- `simulation` (bool)
- `profile` (`sunny_day`, `cloudy_day`, `winter_day`)
- `solar_power_entity` (entity_id de sensor en W)
- `load_power_entity` (entity_id de sensor en W)
- `import_alert_w`
- `import_alert_minutes`
- `export_alert_w`
- `export_alert_minutes`

Validación implementada:
- Si `simulation=false`, son obligatorios `solar_power_entity` y `load_power_entity`.
- Error mostrado: `real_entities_required`.

Se añadió `async_get_options_flow` + `OptionsFlowHandler`.

### 3.2 Recarga al cambiar opciones

Archivo: `custom_components/energy_control_pro/__init__.py`

- Se usa update listener para recargar la entry al modificar options:
  - `entry.add_update_listener(async_reload_entry)`
- Implementado `async_reload_entry`.

### 3.3 Coordinator

Archivo: `custom_components/energy_control_pro/coordinator.py`

Lee primero `entry.options` con fallback a `entry.data`.

Dos modos:

1. **Simulación (`simulation=true`)**
- Usa `simulate(profile, now=...)` de `logic.py`.
- Luego calcula balance con `calculate_balance(...)`.

2. **Modo real (`simulation=false`)**
- Lee estados de `solar_power_entity` y `load_power_entity`.
- Requisitos:
  - entidad existente
  - estado disponible
  - valor numérico
  - unidad en W (si viene unidad, debe ser `W`)
- Si falla, lanza `UpdateFailed`.

Alertas simples implementadas en coordinator:
- Umbral import alto (`import_alert_w`) + duración (`import_alert_minutes`)
- Umbral export alto (`export_alert_w`) + duración (`export_alert_minutes`)
- Acción: `persistent_notification.create`
- Comportamiento:
  - dispara una notificación por episodio
  - rearma cuando baja del umbral
  - `notification_id` fijo por tipo:
    - `energy_control_pro_high_grid_import`
    - `energy_control_pro_high_grid_export`

### 3.4 Lógica pura separada

Archivo: `custom_components/energy_control_pro/logic.py`

Funciones puras (sin dependencia HA):
- `simulate(profile, now, ...) -> tuple[solar_w, load_w]`
- `calculate_balance(solar_w, load_w) -> dict`

Balance implementado:
- `surplus_w = solar_w - load_w`
- `grid_import_w = max(0, -surplus_w)`
- `grid_export_w = max(0, surplus_w)`

### 3.5 Sensores expuestos

Archivo: `custom_components/energy_control_pro/sensor.py`

Actualmente expone:
- `solar_w`
- `load_w`
- `surplus_w`
- `grid_import_w`
- `grid_export_w`

### 3.6 Traducciones

Archivo: `custom_components/energy_control_pro/translations/en.json`

Actualizado con:
- Nuevos campos de options/config.
- Error `real_entities_required`.

### 3.7 Dashboard demo importable

Archivo: `dashboards/energy_control_pro_overview.yaml`

Incluye solo cards core:
- Entities card: Solar / Load / Grid Import / Grid Export / Surplus.
- History graph 24h: Solar / Load / Grid Import / Grid Export.
- Markdown status: Importing / Exporting / Balanced.

### 3.8 Skill de despliegue SMB en Linux/WSL2

Ruta:
- `skills/ha-smb-deploy/SKILL.md`
- `skills/ha-smb-deploy/scripts/deploy_ha_smb.sh`

Ajustes hechos:
- Default mountpoint: `/tmp/homeassistant_config`
- Soporta `--assume-mounted` (no intenta montar)
- Backup automático antes de sincronizar
- `rsync` adaptado a CIFS (`--inplace`) y excluye `__pycache__`, `*.pyc`

Comando usado con éxito (cuando el share ya estaba montado):
```bash
bash skills/ha-smb-deploy/scripts/deploy_ha_smb.sh \
  --component energy_control_pro \
  --source-root ./custom_components \
  --assume-mounted
```

## 4) Estado de tests

Se creó base con pytest:
- `tests/test_balance.py` (3 tests)
- `tests/test_simulation_profiles.py` (3 tests)
- `tests/test_coordinator_sanity.py` (opcional)
- `pyproject.toml` para pytest

Cobertura actual definida:
1. Export case (solar > load)
2. Import case (solar < load)
3. Balanced case (solar == load)
4. sunny > cloudy a misma hora
5. winter < sunny a misma hora
6. noche -> solar = 0

Problema en este entorno de ejecución del asistente:
- No hay `pytest` disponible (`No module named pytest`).
- Instalación fue interrumpida/denegada en sandbox.
- Por tanto, tests no se pudieron ejecutar aquí.

## 5) Estado de despliegue y pruebas en HA

- Se desplegó en una fase previa (cuando lo pediste), con backup generado.
- Regla de trabajo acordada después:
  - **No desplegar/instalar nada sin orden explícita.**

Para probar en HA (cuando quieras):
1. Reiniciar HA o recargar integración.
2. Verificar sensores:
   - `sensor.energy_control_pro_solar_w`
   - `sensor.energy_control_pro_load_w`
   - `sensor.energy_control_pro_surplus_w`
   - `sensor.energy_control_pro_grid_import_w`
   - `sensor.energy_control_pro_grid_export_w`
3. En options:
   - Probar `simulation=true/false`
   - En `simulation=false`, mapear entidades reales en W.
4. Probar alertas con umbrales bajos (ej. 500W, 1 min).

## 6) Decisiones técnicas relevantes

- Separación de lógica pura en `logic.py` para facilitar unit testing.
- Cálculo de balance centralizado en una función única reutilizada.
- Config dinámica movida a `options` para evitar borrar/reinstalar integración.
- Modo real inicial simplificado a 2 entidades (solar/load), con cálculo derivado del resto.
- Alertas básicas incluidas antes de automatismos avanzados.

## 7) Pendientes recomendados (orden sugerido)

1. Ejecutar tests en entorno local con pytest.
2. Ajustar mensajes/UX de errores en modo real si hace falta.
3. Añadir test de unidad para validación de unidad no-W (si se quiere permitir kW con conversión en futuro).
4. (Opcional) Limpiar notificaciones persistentes automáticamente al volver a normal.
5. (Opcional) Añadir más métricas (autoconsumo, ratio export/import, etc.).

## 8) Comandos útiles de continuación

### Tests
```bash
python3 -m pytest
```

Si falta pytest:
```bash
sudo apt-get update
sudo apt-get install -y python3-pytest
python3 -m pytest
```

### Deploy manual cuando el SMB ya está montado
```bash
bash skills/ha-smb-deploy/scripts/deploy_ha_smb.sh \
  --component energy_control_pro \
  --source-root ./custom_components \
  --assume-mounted
```

### Verificación de sintaxis rápida
```bash
python3 -m compileall custom_components/energy_control_pro tests
```

## 9) Nota para retomar en otro chat

Frase corta sugerida para continuar rápido:

"Tenemos `energy_control_pro` con options flow, modo real (solar/load), import/export, alertas persistentes, dashboard YAML y tests creados. Quiero que primero ejecutes/arregles tests y luego preparemos release/HACS." 
