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

## Installation (Remote / Production Home Assistant)

There are two common ways to install this integration onto a remote Home Assistant instance.

1. Manual copy of the `deskbee` folder into `custom_components`.
2. Using the `install.sh` helper script and a GitHub release.

### 1. Manual installation

1. On your Home Assistant host, locate the configuration directory:
   - For Home Assistant OS / Supervised, this is usually `/config`.
2. Under that directory, create `custom_components` if it does not exist:
   - `mkdir -p /config/custom_components`.
3. Copy the `custom_components/deskbee` directory from this repository into `/config/custom_components/deskbee`.
4. Restart Home Assistant.
5. In the UI, go to `Settings -> Devices & services -> Add integration` and search for "Deskbee".

### 2. Using install.sh and GitHub releases

This repository includes an `install.sh` script that downloads the latest GitHub release archive and extracts it into the current directory.

Prerequisites:

- Your GitHub repository for this integration has at least one release with an asset named `deskbee.zip`.
- The `deskbee.zip` archive contains the `deskbee` integration folder (for example, created from `custom_components/deskbee`).

Steps on the Home Assistant host:

1. Open a shell in the Home Assistant configuration directory, for example:
   - `cd /config/custom_components`
2. Run the installer script via `curl`:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/kospiotr/ha-deskbee/master/install.sh | bash -s -- 
   ```

3. After the script finishes, a `deskbee` directory will be present in the current folder.
4. Restart Home Assistant and add the "Deskbee" integration via the UI.
