"""Typed data models for PinProof.

Every model here is deliberately small and explicit. The whole Week 1 point is
that evidence stays attached to every claim, so most models carry provenance
fields (file, line, extraction method, source document).
"""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Verdict(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


# Machine-readable UNKNOWN reasons (see SCOPE.md §2 and §5).
REASON_UNSUPPORTED_EXPRESSION = "unsupported-expression"
REASON_MISSING_FIRMWARE_SYMBOL = "missing-firmware-symbol"
REASON_NET_NOT_FOUND = "net-not-found"
REASON_NET_NOT_ON_MODULE = "net-not-on-module"
REASON_RULEPACK_MISSING_PAD = "rulepack-missing-pad"
REASON_PAD_NOT_GPIO = "pad-not-gpio"
REASON_ALIAS_CYCLE = "alias-cycle"
REASON_ALIAS_DEPTH_EXCEEDED = "alias-depth-exceeded"
REASON_AMBIGUOUS_DECLARATION = "ambiguous-declaration"
REASON_AMBIGUOUS_NET_ENDPOINTS = "ambiguous-net-endpoints"


# --------------------------------------------------------------------------
# Hardware side
# --------------------------------------------------------------------------

class NetNode(BaseModel):
    """One <node> inside a <net> in the KiCad XML netlist."""

    ref: str
    pin: str  # KiCad calls the physical pad number "pin" in the XML netlist
    pinfunction: Optional[str] = None
    pintype: Optional[str] = None


class Netlist(BaseModel):
    """Minimal in-memory view of a KiCad XML netlist."""

    source_path: Path
    design_source: Optional[str] = None
    design_tool: Optional[str] = None
    components: dict[str, dict[str, str]] = Field(default_factory=dict)  # ref -> fields
    nets: dict[str, list[NetNode]] = Field(default_factory=dict)  # net name -> nodes


class HardwareEndpoint(BaseModel):
    """Where a schematic net lands on the MCU module, with rulepack mapping."""

    mcu_ref: str
    net: str
    pad: str
    pad_name: Optional[str] = None  # from the rulepack, e.g. "IO18"
    gpio: Optional[int] = None       # logical GPIO per the rulepack


# --------------------------------------------------------------------------
# Firmware side
# --------------------------------------------------------------------------

class RawDeclaration(BaseModel):
    """A single supported-looking declaration found in firmware source."""

    symbol: str
    value_expr: str
    file: Path
    line: int
    method: str  # "define" | "const-int" | "constexpr-int"
    matched_text: str


class FirmwareClaim(BaseModel):
    """The resolved (or explicitly unresolved) value of one firmware symbol."""

    symbol: str
    gpio: Optional[int] = None
    resolved: bool = False
    unresolved_reason: Optional[str] = None  # a REASON_* constant
    # The declaration where the search started (the contract symbol itself).
    declaration: Optional[RawDeclaration] = None
    # Human-readable chain, e.g.
    # ["PIN_SENSOR_SDA -> SDA_GPIO  (include/pins.h:12, define)",
    #  "SDA_GPIO -> 18  (include/pins.h:9, define)"]
    resolution_chain: list[str] = Field(default_factory=list)
    # For ambiguous-declaration: all competing locations.
    conflicting: list[RawDeclaration] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Rulepack (module pad -> GPIO mapping)
# --------------------------------------------------------------------------

class PadMapping(BaseModel):
    name: str                 # e.g. "IO18", "GND", "EN"
    gpio: Optional[int] = None  # None for power/control pads
    kind: str = "gpio"        # "gpio" | "power" | "control" | "no-connect"
    note: Optional[str] = None


class Rulepack(BaseModel):
    rulepack: str
    version: str
    module: str
    status: str
    provenance: list[dict] = Field(default_factory=list)
    pads: dict[str, PadMapping] = Field(default_factory=dict)  # pad number -> mapping
    strapping_gpios: list[int] = Field(default_factory=list)
    source_path: Optional[Path] = None


# --------------------------------------------------------------------------
# Contract (pinproof.yaml)
# --------------------------------------------------------------------------

class RoleContract(BaseModel):
    role: str
    net: str
    firmware_symbol: str


class ProjectSection(BaseModel):
    netlist: Path
    firmware: Path
    mcu_ref: str = "U1"
    module: str
    rulepack_path: Optional[Path] = None  # explicit override, else discovered


class PinproofConfig(BaseModel):
    pinproof: int
    project: ProjectSection
    roles: list[RoleContract]
    config_path: Optional[Path] = None


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------

class RoleResult(BaseModel):
    role: str
    verdict: Verdict
    reason: Optional[str] = None      # REASON_* for UNKNOWN, prose for PASS/FAIL
    hardware: Optional[HardwareEndpoint] = None
    hardware_endpoints: list[HardwareEndpoint] = Field(default_factory=list)
    firmware: Optional[FirmwareClaim] = None
    detail: Optional[str] = None      # extra human-readable context


class ScanReport(BaseModel):
    tool_version: str
    rulepack_id: Optional[str] = None
    rulepack_version: Optional[str] = None
    config_path: Optional[Path] = None
    mcu_ref: str
    module: str
    results: list[RoleResult] = Field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        c = {v.value: 0 for v in Verdict}
        for r in self.results:
            c[r.verdict.value] += 1
        return c

    @property
    def exit_code(self) -> int:
        """0 = no proven mismatch; 1 = at least one FAIL. Never nonzero for UNKNOWN."""
        return 1 if any(r.verdict is Verdict.FAIL for r in self.results) else 0
