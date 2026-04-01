#!/usr/bin/env sh

set -eu

# Usage:
#   ./install.sh OWNER/REPO
# or set GITHUB_REPO=OWNER/REPO and run without arguments.

REPO="${1:-${GITHUB_REPO:-}}"

if [ -z "$REPO" ]; then
  echo "Usage: $0 <github_owner/repo> or set GITHUB_REPO environment variable" >&2
  exit 1
fi

ZIP_NAME="deskbee.zip"
DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${ZIP_NAME}"

echo "Downloading latest Deskbee release from ${DOWNLOAD_URL}..." >&2

TMP_ZIP="$(mktemp)"

if command -v curl >/dev/null 2>&1; then
  curl -fL "$DOWNLOAD_URL" -o "$TMP_ZIP"
elif command -v wget >/dev/null 2>&1; then
  wget -O "$TMP_ZIP" "$DOWNLOAD_URL"
else
  echo "Error: neither curl nor wget is available. Install one of them and try again." >&2
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "Error: unzip is required to extract the integration archive." >&2
  exit 1
fi

echo "Unpacking Deskbee integration into $(pwd)..." >&2
unzip -o "$TMP_ZIP" >/dev/null

rm -f "$TMP_ZIP"

echo "Deskbee integration installed. If you ran this from your Home Assistant config/custom_components directory, you should now have a 'deskbee' folder here." >&2
