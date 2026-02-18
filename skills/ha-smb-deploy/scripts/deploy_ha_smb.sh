#!/usr/bin/env bash
set -euo pipefail

COMPONENT=""
SOURCE_ROOT="./custom_components"
SHARE="//homeassistant/config"
MOUNTPOINT="/tmp/homeassistant_config"
SMB_VERSION="3.0"
USERNAME=""
PASSWORD=""
UNMOUNT_AFTER="false"
ASSUME_MOUNTED="false"

usage() {
  cat <<USAGE
Usage:
  $0 --component <name> [options]

Required:
  --component <name>          Integration folder name under custom_components

Options:
  --source-root <path>        Local custom_components root (default: ./custom_components)
  --share <//host/share>      SMB share (default: //homeassistant/config)
  --mountpoint <path>         Local mountpoint (default: /tmp/homeassistant_config)
  --smb-version <ver>         SMB version (default: 3.0)
  --username <name>           SMB username (optional)
  --password <pass>           SMB password (optional)
  --assume-mounted            Do not try to mount; require mountpoint already mounted
  --unmount-after             Unmount share after deploy
  -h, --help                  Show this help
USAGE
}

log() {
  printf '[ha-smb-deploy] %s\n' "$*"
}

fail() {
  printf '[ha-smb-deploy][ERROR] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --component)
      COMPONENT="${2:-}"
      shift 2
      ;;
    --source-root)
      SOURCE_ROOT="${2:-}"
      shift 2
      ;;
    --share)
      SHARE="${2:-}"
      shift 2
      ;;
    --mountpoint)
      MOUNTPOINT="${2:-}"
      shift 2
      ;;
    --smb-version)
      SMB_VERSION="${2:-}"
      shift 2
      ;;
    --username)
      USERNAME="${2:-}"
      shift 2
      ;;
    --password)
      PASSWORD="${2:-}"
      shift 2
      ;;
    --assume-mounted)
      ASSUME_MOUNTED="true"
      shift
      ;;
    --unmount-after)
      UNMOUNT_AFTER="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

[[ -n "$COMPONENT" ]] || { usage; fail "--component is required"; }

SOURCE_DIR="$SOURCE_ROOT/$COMPONENT"
TARGET_ROOT="$MOUNTPOINT/custom_components"
TARGET_DIR="$TARGET_ROOT/$COMPONENT"
BACKUP_ROOT="$MOUNTPOINT/custom_components_backup"
TS="$(date +%Y%m%d_%H%M%S)"

command -v mount >/dev/null 2>&1 || fail "mount command not found"
command -v rsync >/dev/null 2>&1 || fail "rsync command not found"
command -v cp >/dev/null 2>&1 || fail "cp command not found"

[[ -d "$SOURCE_DIR" ]] || fail "Source component folder does not exist: $SOURCE_DIR"

mkdir -p "$MOUNTPOINT"

if mountpoint -q "$MOUNTPOINT"; then
  log "Mountpoint already mounted: $MOUNTPOINT"
elif [[ "$ASSUME_MOUNTED" == "true" ]]; then
  fail "--assume-mounted was provided but $MOUNTPOINT is not a mounted filesystem"
else
  log "Mounting $SHARE in $MOUNTPOINT"

  MOUNT_OPTS="vers=$SMB_VERSION,iocharset=utf8,uid=$(id -u),gid=$(id -g),file_mode=0775,dir_mode=0775"
  if [[ -n "$USERNAME" ]]; then
    MOUNT_OPTS="$MOUNT_OPTS,username=$USERNAME,password=$PASSWORD"
  else
    MOUNT_OPTS="$MOUNT_OPTS,guest"
  fi

  sudo mount -t cifs "$SHARE" "$MOUNTPOINT" -o "$MOUNT_OPTS"
fi

mkdir -p "$TARGET_ROOT"

if [[ -d "$TARGET_DIR" ]]; then
  mkdir -p "$BACKUP_ROOT"
  BACKUP_DIR="$BACKUP_ROOT/${COMPONENT}_$TS"
  log "Creating backup: $BACKUP_DIR"
  cp -a "$TARGET_DIR" "$BACKUP_DIR"
fi

log "Syncing $SOURCE_DIR -> $TARGET_DIR"
mkdir -p "$TARGET_DIR"
rsync -a --delete --inplace \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "$SOURCE_DIR/" "$TARGET_DIR/"

log "Deploy complete for component: $COMPONENT"
log "Target path: $TARGET_DIR"

if [[ "$UNMOUNT_AFTER" == "true" ]]; then
  log "Unmounting $MOUNTPOINT"
  sudo umount "$MOUNTPOINT"
fi
