"""Load and validate pinproof.yaml contracts and module rulepacks.

Both files are YAML, loaded with ``yaml.safe_load`` only (no object
construction, no code execution). All relative paths inside pinproof.yaml are
resolved against the directory containing that file, so fixtures are
self-contained and relocatable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from .models import PinproofConfig, Rulepack

SUPPORTED_CONTRACT_VERSION = 1
RULEPACK_DIR_ENV = "PINPROOF_RULEPACK_DIR"
RULEPACK_DIR_NAME = "rulepacks"
MAX_PARENT_SEARCH = 6


class ConfigError(Exception):
    """A usage-level problem with pinproof.yaml or the rulepack (exit code 2)."""


def _load_yaml(path: Path, what: str) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"{what} not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{what} is not valid YAML ({path}): {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{what} must be a YAML mapping ({path})")
    return data


def load_config(path: Path) -> PinproofConfig:
    """Load pinproof.yaml, validate it, and resolve its relative paths."""
    path = Path(path).resolve()
    data = _load_yaml(path, "pinproof.yaml contract")

    try:
        config = PinproofConfig(**data)
    except ValidationError as exc:
        raise ConfigError(f"pinproof.yaml is invalid ({path}):\n{exc}") from exc

    if config.pinproof != SUPPORTED_CONTRACT_VERSION:
        raise ConfigError(
            f"unsupported contract version {config.pinproof!r} in {path}; "
            f"this tool supports version {SUPPORTED_CONTRACT_VERSION}"
        )
    if not config.roles:
        raise ConfigError(f"pinproof.yaml defines no roles ({path})")

    base = path.parent
    config.config_path = path
    config.project.netlist = (base / config.project.netlist).resolve()
    config.project.firmware = (base / config.project.firmware).resolve()
    if config.project.rulepack_path is not None:
        config.project.rulepack_path = (base / config.project.rulepack_path).resolve()
    return config


def _module_slug(module: str) -> str:
    return module.lower().replace(" ", "-")


def find_rulepack_file(module: str, config_path: Optional[Path]) -> Path:
    """Locate ``<slug>.yaml`` for a module name.

    Search order (first hit wins, deterministic):
    1. ``$PINPROOF_RULEPACK_DIR``
    2. a ``rulepacks/`` directory next to the contract file, then walking up
       parent directories (max 6 levels) — this finds the repo's top-level
       ``rulepacks/`` from any fixture without configuration.
    3. the current working directory's ``rulepacks/``.
    """
    filename = _module_slug(module) + ".yaml"
    candidates: list[Path] = []

    env_dir = os.environ.get(RULEPACK_DIR_ENV)
    if env_dir:
        candidates.append(Path(env_dir) / filename)

    if config_path is not None:
        current = Path(config_path).resolve().parent
        for _ in range(MAX_PARENT_SEARCH):
            candidates.append(current / RULEPACK_DIR_NAME / filename)
            if current.parent == current:
                break
            current = current.parent

    candidates.append(Path.cwd() / RULEPACK_DIR_NAME / filename)

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ConfigError(
        f"no rulepack found for module {module!r} (looked for {filename} in "
        f"$PINPROOF_RULEPACK_DIR, ancestor rulepacks/ directories, and ./rulepacks/)"
    )


def load_rulepack(module: str, config_path: Optional[Path] = None,
                  explicit_path: Optional[Path] = None) -> Rulepack:
    """Load and validate the rulepack for a module."""
    path = Path(explicit_path) if explicit_path else find_rulepack_file(module, config_path)
    data = _load_yaml(path, "rulepack")
    try:
        rulepack = Rulepack(**data)
    except ValidationError as exc:
        raise ConfigError(f"rulepack is invalid ({path}):\n{exc}") from exc
    rulepack.source_path = path

    if _module_slug(rulepack.module) != _module_slug(module):
        raise ConfigError(
            f"rulepack {path} is for module {rulepack.module!r}, "
            f"but the contract asks for {module!r}"
        )
    return rulepack
