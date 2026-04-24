#!/usr/bin/env bash
# Idempotent refresh helper for .homeassistant runtime folder.
# Use when you want to re-copy the default configuration or re-create the symlink.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
RUNTIME_DIR="$REPO_ROOT/.homeassistant"
DEV_CONFIG="$REPO_ROOT/.devcontainer/configuration.yaml"

echo "[refresh_homeassistant_runtime] repo_root=$REPO_ROOT"

if [ -d "$RUNTIME_DIR" ]; then
  echo "[refresh_homeassistant_runtime] $RUNTIME_DIR exists"
else
  echo "[refresh_homeassistant_runtime] $RUNTIME_DIR missing, creating"
  mkdir -p "$RUNTIME_DIR"
fi

# Ensure custom_components directory exists
mkdir -p "$RUNTIME_DIR/custom_components"

# Copy configuration.yaml only if upstream devcontainer copy exists and target doesn't
if [ -f "$DEV_CONFIG" ]; then
  if [ ! -f "$RUNTIME_DIR/configuration.yaml" ]; then
    echo "[refresh_homeassistant_runtime] copying $DEV_CONFIG -> $RUNTIME_DIR/configuration.yaml"
    cp "$DEV_CONFIG" "$RUNTIME_DIR/configuration.yaml"
  else
    echo "[refresh_homeassistant_runtime] configuration.yaml already exists in $RUNTIME_DIR — skipping copy"
  fi
else
  echo "[refresh_homeassistant_runtime] no $DEV_CONFIG to copy"
fi

## Create symlink for geist_pdu component (points to repo's geist_pdu)
# Safety: never remove repository files. Only remove a runtime copy if its resolved
# path is inside the runtime directory.
if [ -e "$RUNTIME_DIR/custom_components/geist_pdu" ] && [ ! -L "$RUNTIME_DIR/custom_components/geist_pdu" ]; then
  real_target=$(realpath "$RUNTIME_DIR/custom_components/geist_pdu" 2>/dev/null || true)
  real_runtime=$(realpath "$RUNTIME_DIR" 2>/dev/null || true)
  if [ -n "$real_target" ] && [ -n "$real_runtime" ] && [[ "$real_target" == "$real_runtime"* ]]; then
    echo "[refresh_homeassistant_runtime] migrating geist_pdu from directory to symlink..."
    rm -rf "$RUNTIME_DIR/custom_components/geist_pdu"
  else
    echo "[refresh_homeassistant_runtime] WARNING: $RUNTIME_DIR/custom_components/geist_pdu exists outside runtime; skipping removal"
  fi
fi

if [ -L "$RUNTIME_DIR/custom_components/geist_pdu" ]; then
  echo "[refresh_homeassistant_runtime] geist_pdu symlink already exists"
else
  echo "[refresh_homeassistant_runtime] creating symlink for geist_pdu"
  ln -s "$REPO_ROOT/custom_components/geist_pdu" "$RUNTIME_DIR/custom_components/geist_pdu"
fi

# Remove old blanket custom_components symlink if it exists (migration from old setup).
if [ -L "$RUNTIME_DIR/custom_components" ]; then
  echo "[refresh_homeassistant_runtime] removing old blanket custom_components symlink..."
  rm "$RUNTIME_DIR/custom_components"
  mkdir -p "$RUNTIME_DIR/custom_components"
fi

echo "[refresh_homeassistant_runtime] done"
