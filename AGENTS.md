## Overview

This repository contains a custom [Home Assistant](https://www.home-assistant.io/) integration called `deskbee`. The code lives under `custom_components/deskbee/` and is intended to run inside a Home Assistant container, not as a standalone Python application.

This file is written for agentic coding tools and humans working on this repo. It explains how to run the integration, how to run tests, and what style/conventions to follow when editing or adding code.

The goals are:
- Keep the repository compatible with standard Home Assistant expectations.
- Make it easy to run the integration locally while developing.
- Maintain a consistent, readable Python style across files.

## Runtime, Build, and Dev Environment

- Runtime: Home Assistant (Docker container).
- Primary dev flow: run Home Assistant in a container with the repo mounted into `/config`.
- Dev container configuration: `.devcontainer/devcontainer.json`.

### Starting Home Assistant For Development

You can start Home Assistant for local development in two equivalent ways.

1. Using the command from `README.md` (run from repo root):

```bash
podman run --rm \
  --name ha-deskbee-dev \
  -p 8123:8123 \
  -v "$(pwd)/.config":/config \
  -v "$(pwd)/.config/tests/configuration.yaml":/config/configuration.yaml \
  -v "$(pwd)/custom_components":/config/custom_components \
  ghcr.io/home-assistant/home-assistant:stable
```

2. Using the helper script in `tests/run.sh` (preferred to avoid typos):

```bash
cd /Users/prki/workspace/ha_deskbee
bash tests/run.sh
```

Both start a Home Assistant container, bind-mounting this repo so that edits to `custom_components/deskbee` are reflected immediately.

### Tests and Manual Verification

There is currently no automated unit test suite wired up (no `pytest`, `tox`, or similar configs). The existing `tests` directory is used to run a Home Assistant instance with a minimal configuration to exercise the integration.

Manual test procedure:

1. Start Home Assistant using `tests/run.sh` or the README command.
2. Open `http://localhost:8123` in a browser.
3. Complete onboarding if needed (uses `.config` in this repo as the HA config dir).
4. Confirm that the `Deskbee` integration is discovered and that the demo sensor `sensor.deskbee_demo_reservation_status` is available.
5. Verify that the sensor value changes over time (it embeds the current hour and minute).

### Running a Single Test

Because there is no unit test suite yet, "running a single test" currently means one of:
- Manually validating a specific behavior in the HA UI (for example, reloading the integration and confirming logs and entity state), or
- Adding targeted checks/logs in the relevant file, restarting the container, and verifying the behavior.

If you introduce automated tests (for example, `pytest` against helper modules), prefer:

- Project-wide tests: `pytest` from the repo root.
- Single file: `pytest path/to/test_file.py`.
- Single test function: `pytest path/to/test_file.py::TestClassName::test_case_name`.

Document any new test commands you add here.

### Linting and Formatting Commands

There are currently no configured linters or formatters (no `pyproject.toml`, `setup.cfg`, or `ruff`/`flake8`/`black` config). If you add them, prefer:

- `ruff` for linting/import order.
- `black` for formatting.

Suggested (but not yet wired) commands:

```bash
python -m ruff custom_components tests
python -m black custom_components tests
```

If you introduce these tools, update this section to specify the exact commands and any config files.

## Cursor / Copilot Rules

- There are currently **no** repository-level Cursor rules (no `.cursor/rules/` and no `.cursorrules*`).
- There are currently **no** repository-level GitHub Copilot instructions (no `.github/copilot-instructions.md`).

If such files are added in the future, agents should:
- Treat those rule files as authoritative over anything in this document that conflicts.
- Surface any important constraints (for example, forbidden dependencies or architectural rules) in PR descriptions and code comments when relevant.

## Python Code Style

The codebase follows a simple, Home Assistant–aligned Python style. When in doubt, prefer consistency with the existing files under `custom_components/deskbee`.

### Language Level and Typing

- Use `from __future__ import annotations` at the top of each Python file (as seen in `__init__.py`, `config_flow.py`, `sensor.py`).
- Use standard type hints throughout:
  - `dict[str, Any]` instead of `Dict[str, Any]`.
  - `list[str]` instead of `List[str]`.
  - `FlowResult`, `HomeAssistant`, `ConfigEntry`, etc., from Home Assistant types where available.
- Prefer explicit types for function parameters and return values, especially in integration entry points.

### Imports

- Group imports in this order:
  1. Standard library (for example, `from datetime import datetime`).
  2. Third-party packages (for example, `import voluptuous as vol`).
  3. Home Assistant imports (for example, `from homeassistant.core import HomeAssistant`).
  4. Local package imports (for example, `from .const import DOMAIN`).
- Within each group, sort imports alphabetically by module name.
- Use explicit imports instead of `import *`.
- Use relative imports for modules within `custom_components/deskbee`.

### Formatting

- Follow a `black`-like style, even if not enforced yet:
  - 88–100 character line length max; wrap arguments and long strings.
  - Use double quotes for docstrings; single or double quotes for regular strings, but be consistent in a file.
  - One import per line.
- Leave one blank line between groups of imports and between top-level functions/classes.
- Use meaningful docstrings on all public functions and classes that hook into Home Assistant (for example, `async_setup_entry`, entities, config flows).

### Naming Conventions

- Modules and packages: `snake_case` (for example, `config_flow.py`, `sensor.py`).
- Classes: `PascalCase` (for example, `DeskbeeConfigFlow`, `DeskbeeDemoReservationSensor`).
- Functions and methods: `snake_case` (for example, `async_setup_entry`, `async_unload_entry`).
- Constants: `UPPER_SNAKE_CASE` (for example, `DOMAIN` in `const.py`).
- Attributes:
  - Use `_attr_*` attributes for Home Assistant entity properties when possible (for example, `_attr_name`, `_attr_unique_id`).
  - Use leading underscore for "private" helpers inside a module.

### Error Handling and Logging

- Prefer failing fast and logging meaningful messages over silently swallowing errors.
- For integration logic that may fail (for example, API calls to Deskbee), use Home Assistant’s logger instead of `print`.
- Typical pattern (once you add real I/O):

```python
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


async def _fetch_reservations(...) -> list[Reservation]:
    try:
        return await client.get_reservations(...)
    except DeskbeeError as err:
        _LOGGER.error("Error fetching Deskbee reservations: %s", err)
        raise
```

- When raising errors in config flows, use the Home Assistant patterns (for example, `self.async_show_form` with `errors={...}`) instead of generic exceptions.

### Async Patterns

- Home Assistant integration entry points are async; follow the existing signatures:
  - `async_setup(hass: HomeAssistant, config: dict) -> bool`
  - `async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool`
  - `async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool`
- Do not perform blocking I/O in these functions; use async clients or run blocking work in executors when necessary.
- Avoid creating background tasks without tracking them; use HA helpers if persistent tasks or coordinators are needed.

### Entities and State

- Use `SensorEntity` and other HA base classes as shown in `sensor.py`.
- Prefer `_attr_*` attributes for fixed properties like name and unique ID.
- When adding real data fetching:
  - Implement `async_update` or use a `DataUpdateCoordinator`.
  - Keep update intervals and throttling consistent with HA best practices.

## File/Module Guidelines

- `custom_components/deskbee/__init__.py`:
  - Contains integration setup/teardown logic.
  - Should remain small and focused on wiring platforms and shared data into `hass.data[DOMAIN]`.
- `custom_components/deskbee/config_flow.py`:
  - Owns user-facing configuration flows and options.
  - Avoid heavy logic here; prefer delegating to helpers or clients.
- `custom_components/deskbee/sensor.py`:
  - Owns entity classes and any wiring specific to the `sensor` platform.
  - Add new sensor entities here (or in submodules) as the integration grows.

When adding new functionality, keep responsibilities separated along these lines.

## Expectations For New Contributions

When adding or modifying code in this repository, agents should:

1. Keep changes minimal and focused; avoid large unrelated refactors.
2. Preserve existing behavior of the integration unless explicitly changing it.
3. Maintain the async, non-blocking design expected by Home Assistant.
4. Ensure the integration still loads successfully in Home Assistant using `tests/run.sh`.
5. Update this `AGENTS.md` file if you introduce new tools, commands, or conventions.

If something in this document appears to contradict active Cursor/Copilot rules, Home Assistant documentation, or new configuration files, treat those newer/closer-to-source documents as authoritative and adjust this file accordingly.
