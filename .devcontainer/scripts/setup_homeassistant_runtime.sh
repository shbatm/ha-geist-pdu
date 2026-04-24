#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUNTIME_DIR="$REPO_ROOT/.homeassistant"
DEV_CONFIG="$REPO_ROOT/.devcontainer/configuration.yaml"

echo "[setup_homeassistant_runtime] repo_root=$REPO_ROOT"

mkdir -p "$RUNTIME_DIR/custom_components"

if [ -f "$DEV_CONFIG" ]; then
  if [ ! -f "$RUNTIME_DIR/configuration.yaml" ]; then
    cp "$DEV_CONFIG" "$RUNTIME_DIR/configuration.yaml"
    echo "[setup_homeassistant_runtime] copied default configuration to $RUNTIME_DIR/configuration.yaml"
  else
    echo "[setup_homeassistant_runtime] configuration.yaml already exists in $RUNTIME_DIR — skipping copy"
  fi
fi

if [ -L "$RUNTIME_DIR/custom_components/geist_pdu" ]; then
  echo "[setup_homeassistant_runtime] geist_pdu symlink already exists"
else
  ln -s "$REPO_ROOT/custom_components/geist_pdu" "$RUNTIME_DIR/custom_components/geist_pdu"
  echo "[setup_homeassistant_runtime] created symlink $RUNTIME_DIR/custom_components/geist_pdu -> $REPO_ROOT/custom_components/geist_pdu"
fi

echo "[setup_homeassistant_runtime] done"
