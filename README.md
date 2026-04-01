# Deskbee Home Assistant Integration

This repository contains a custom Home Assistant integration for Deskbee.

## Current Status

- Minimal "hello world" integration that exposes a demo sensor:
  - `sensor.deskbee_demo_reservation_status`

## Installation (Development)

Start dev container:

```bash
podman run --rm \
  --name ha-deskbee-dev \
  -p 8123:8123 \
  -v "$(pwd)/.config":/config \
  -v "$(pwd)/.config/tests/configuration.yaml":/config/configuration.yaml \
  -v "$(pwd)/custom_components":/config/custom_components \
  ghcr.io/home-assistant/home-assistant:stable
```

Then:
- Open http://localhost:8123 in your browser.
- Initialize configuration and first account (done if .config exists)
- Check custom component is mounted correctly
  - Settings -> Devices & services
  - Search for "Deskbee"
- 