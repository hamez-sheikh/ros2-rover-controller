#!/usr/bin/env bash
# Optional heavyweight tools for people who want to REBUILD the fixtures,
# not just run the checker. The checker itself needs none of this.
#
# Verified July 2026:
#   - KiCad 10.0 is the current stable series (10.0.0 released 2026-03;
#     see https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/).
#   - Ubuntu PPA: ppa:kicad/kicad-10.0-releases (supports 24.04 "noble").
#     https://launchpad.net/~kicad/+archive/ubuntu/kicad-10.0-releases
#   - PlatformIO Core via pip is the documented method for containers/CI:
#     https://docs.platformio.org/en/latest/core/installation/methods/pypi.html
#     (udev rules are irrelevant in Codespaces: no USB passthrough.)
#
# WARNING: the KiCad install pulls several GB. On a default 2-core/8GB/32GB
# Codespace this is slow but works. Alternative for CI: the official image
# kicad/kicad:10.0 (https://hub.docker.com/r/kicad/kicad) has kicad-cli.
set -euo pipefail

echo "== Installing PlatformIO Core (pip method) =="
python3 -m pip install -U platformio

echo "== Installing KiCad 10 from the official PPA (several GB!) =="
sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases
sudo apt-get update
sudo apt-get install -y --install-recommends kicad

echo "== Done =="
kicad-cli version || true
pio --version || true
