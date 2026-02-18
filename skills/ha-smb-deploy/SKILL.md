---
name: ha-smb-deploy
description: Deploy a Home Assistant custom integration from Linux/WSL2 to a Home Assistant SMB share using CIFS mount, with automatic backup and rsync sync. Use this when user wants safe repeated deployment to /config/custom_components over SMB.
---

# HA SMB Deploy (Linux)

Use this skill to deploy an integration from a local repo into Home Assistant via SMB on Linux/WSL2.

## When to use

- User is on Linux or WSL2
- Home Assistant config is reachable as SMB share (for example `//homeassistant/config`)
- User wants repeatable deploy with backup before overwrite

## Files in this skill

- Script: `scripts/deploy_ha_smb.sh`

## Quick usage

If share is already mounted in `/tmp/homeassistant_config`:

```bash
bash skills/ha-smb-deploy/scripts/deploy_ha_smb.sh \
  --component energy_control_pro \
  --source-root ./custom_components \
  --assume-mounted
```

If share is not mounted yet:

```bash
bash skills/ha-smb-deploy/scripts/deploy_ha_smb.sh \
  --component energy_control_pro \
  --source-root ./custom_components \
  --share //homeassistant/config
```

## Behavior

1. Validates required tools (`mount`, `rsync`, `cp`).
2. Uses existing mount if present; otherwise mounts SMB share in mountpoint.
3. Creates timestamped backup of existing target component if present.
4. Syncs source component to `/config/custom_components/<component>` with CIFS-safe `rsync --delete --inplace` and excludes `__pycache__`/`*.pyc`.
5. Leaves share mounted (faster repeated deploys). Optional unmount flag available.

## Notes

- Default mountpoint is `/tmp/homeassistant_config`.
- Use `--assume-mounted` when you already mounted SMB manually and want zero `sudo` operations from the script.
- By default, mount mode is guest. For authenticated shares, pass `--username` and `--password`.
- For Home Assistant OS shares, SMB add-on must be configured and reachable from Linux host.
- After deploy, restart Home Assistant or reload the integration as needed.
