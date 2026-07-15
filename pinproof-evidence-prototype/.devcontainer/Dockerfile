# Ubuntu 24.04 (noble) base, per the project's target environment.
# Python 3.12 is added by the devcontainer "python" feature (see devcontainer.json).
#
# KiCad and PlatformIO are deliberately NOT installed by default:
#   - KiCad adds several GB and 5-10+ minutes to every cold Codespace create
#     (verified July 2026); the checker only needs the exported XML netlist,
#     which is committed in fixtures/.
#   - PlatformIO is only needed if you want to actually compile fixture
#     firmware, which the Week 1 checker never requires.
# Opt in with:  bash .devcontainer/install-optional-tools.sh
FROM mcr.microsoft.com/devcontainers/base:noble

RUN apt-get update && apt-get install -y --no-install-recommends \
        zip \
    && rm -rf /var/lib/apt/lists/*
