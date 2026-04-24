# Geist PDU Integration — Development Context

## Project Goals
Implement a modern Home Assistant integration for Geist rack-mount PDUs.

## Core Mandates
- **Bronze IQS Compliance:** Strictly follow the rules in `BRONZE_IQS_RULES.md`.
- **Modern Patterns:** 
  - Use `DataUpdateCoordinator` for polling (30s default).
  - Store coordinator in `entry.runtime_data`.
  - Use `_attr_has_entity_name = True` for all entities.
- **Async First:** All network communication must be non-blocking (use `aiohttp` via `async_get_clientsession`).
- **Immediate State:** On service calls/toggles, update the coordinator data immediately using `async_set_updated_data`.

## Git Workflow
- **No Direct Push to `main`:** All changes must use a feature branch and PR.
- **Feature Branch:** `git checkout -b <branch>`, commit, push to origin, open PR.

## Architecture & Implementation Patterns
- **Coordinator Pattern:** Entities should inherit from `CoordinatorEntity`. The coordinator handles API drift correction.
- **Config Flow:**
  - Validate connections in `async_step_user` before creating entry (`test-before-configure`).
  - Set a stable `unique_id` (e.g., the host or serial number) and call `_abort_if_unique_id_configured`.
  - Follow the "Grocy pattern": proceed immediately to `async_step_options` if additional setup is needed.
- **Options Flow:** Implement `OptionsFlow` for runtime-configurable settings (e.g., polling interval).
- **Translations:** Maintain `strings.json` and `translations/en.json` for all UI elements and error keys.

## Development Environment
- **Container Path:** `/workspaces/ha-geist-pdu`
- **Python Venv:** `/opt/venv` (inside container)

## Common Commands
Run these from the host to interact with the container:
```bash
# Run HA Test Environment (starts HA with component loaded)
docker exec -it <container_name> bash .devcontainer/scripts/setup_ha_test_env.sh

# Lint check & Auto-fix
docker exec <container_name> /opt/venv/bin/ruff check custom_components/geist_pdu/
docker exec <container_name> /opt/venv/bin/ruff check --fix custom_components/geist_pdu/

# Run Tests
docker exec <container_name> /opt/venv/bin/pytest
```

## Implementation Notes
- The Geist PDU typically supports SNMP or a Web API (JSON/XML). Preference is for the Web API.
- Initial sensors: Voltage, Current, and Power per phase/outlet.
