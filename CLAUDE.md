# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A custom [Home Assistant](https://www.home-assistant.io/) integration called `deskbee`. All integration code lives under `custom_components/deskbee/`. It is not a standalone Python application — it runs inside a Home Assistant container.

## Running Home Assistant for Development

Start HA with the repo mounted so edits take effect immediately (no rebuild needed):

```bash
docker compose up
```

Or with podman directly:

```bash
podman run --rm \
  --name ha-deskbee-dev \
  -p 8123:8123 \
  -v "$(pwd)/.config":/config \
  -v "$(pwd)/config/configuration.yaml":/config/configuration.yaml \
  -v "$(pwd)/custom_components":/config/custom_components \
  ghcr.io/home-assistant/home-assistant:stable
```

HA UI is available at `http://localhost:8123`. The `.config/` directory is the HA config dir; `config/configuration.yaml` overrides the main config and enables `custom_components.deskbee` debug logging.

## No Automated Test Suite

There is no `pytest`, `tox`, or linter configured yet. Manual verification:

1. Start HA using the command above.
2. Confirm `sensor.deskbee_demo_reservation_status` is available in the UI.
3. Verify the sensor value updates (it embeds current hour:minute).

If `pytest` is added later: `pytest` (all tests) or `pytest path/to/test_file.py::test_name` (single test).

Preferred tools if linting is added: `ruff` for linting, `black` for formatting.

## Architecture

| File | Responsibility |
|---|---|
| `__init__.py` | Entry point: `async_setup_entry` / `async_unload_entry`, wires sensor platform, stores per-entry data in `hass.data[DOMAIN]` |
| `config_flow.py` | `DeskbeeConfigFlow` — collects `CONF_ACCESS_TOKEN` from the user via UI; API validation is stubbed out |
| `sensor.py` | `DeskbeeDemoReservationSensor` — placeholder sensor returning a timestamp string; will be replaced with real Deskbee reservation data |
| `const.py` | `DOMAIN = "deskbee"` |

The integration currently exposes one demo sensor. Real implementation will add an API client, likely a `DataUpdateCoordinator`, and expand `sensor.py`.

## Code Conventions

- `from __future__ import annotations` at the top of every file.
- Use `dict[str, Any]` / `list[str]` (not `Dict`/`List` from `typing`).
- Imports ordered: stdlib → third-party → `homeassistant.*` → local (`.const`, etc.).
- Relative imports within the package (e.g. `from .const import DOMAIN`).
- Entity fixed properties via `_attr_*` (e.g. `_attr_name`, `_attr_unique_id`).
- All HA entry points are `async`; no blocking I/O in async context.
- Logging via `logging.getLogger(__name__)`, not `print`.
- Config flow errors via `self.async_show_form(..., errors={...})`, not bare exceptions.