"""The comparison engine: role contract -> PASS / FAIL / UNKNOWN with evidence.

Decision table (SCOPE.md §2). The invariants that matter most:

* FAIL requires *supported* evidence on BOTH sides. It is the only verdict
  that makes the process exit nonzero.
* Missing or unsupported evidence is ALWAYS surfaced as UNKNOWN with a
  machine-readable reason. UNKNOWN is never upgraded to PASS.
"""

from __future__ import annotations

from . import __version__
from .firmware import FirmwareProject, resolve_symbol
from .hardware import endpoint_from_node, find_net, mcu_nodes_on_net
from .models import (
    REASON_AMBIGUOUS_NET_ENDPOINTS,
    REASON_NET_NOT_FOUND,
    REASON_NET_NOT_ON_MODULE,
    REASON_PAD_NOT_GPIO,
    REASON_RULEPACK_MISSING_PAD,
    Netlist,
    PinproofConfig,
    RoleContract,
    RoleResult,
    Rulepack,
    ScanReport,
    Verdict,
)


def evaluate_role(
    contract: RoleContract,
    netlist: Netlist,
    firmware: FirmwareProject,
    rulepack: Rulepack,
    mcu_ref: str,
) -> RoleResult:
    result = RoleResult(role=contract.role, verdict=Verdict.UNKNOWN)

    # ---- Firmware side -------------------------------------------------
    claim = resolve_symbol(firmware, contract.firmware_symbol)
    result.firmware = claim

    # ---- Hardware side -------------------------------------------------
    resolved_net = find_net(netlist, contract.net)
    if resolved_net is None:
        result.reason = REASON_NET_NOT_FOUND
        result.detail = (
            f"net {contract.net!r} not found in netlist "
            f"{netlist.source_path.name} (checked exact and unique "
            f"hierarchical-suffix matches)"
        )
        return result

    nodes = mcu_nodes_on_net(netlist, resolved_net, mcu_ref)
    endpoints = [endpoint_from_node(n, resolved_net, mcu_ref, rulepack) for n in nodes]
    result.hardware_endpoints = endpoints

    if not nodes:
        result.reason = REASON_NET_NOT_ON_MODULE
        result.detail = f"net {resolved_net!r} exists but has no node on {mcu_ref}"
        return result

    if len(endpoints) > 1:
        # Week 1 is conservative: a net touching the module on several pads
        # is reported for a human, not adjudicated by the tool.
        result.reason = REASON_AMBIGUOUS_NET_ENDPOINTS
        result.detail = (
            f"net {resolved_net!r} touches {mcu_ref} on multiple pads: "
            + ", ".join(e.pad for e in endpoints)
        )
        return result

    endpoint = endpoints[0]
    result.hardware = endpoint

    if endpoint.pad_name is None:
        result.reason = REASON_RULEPACK_MISSING_PAD
        result.detail = (
            f"{mcu_ref} pad {endpoint.pad} is not in rulepack "
            f"{rulepack.rulepack} v{rulepack.version} (mapping is labeled "
            f"{rulepack.status!r})"
        )
        return result

    if endpoint.gpio is None:
        result.reason = REASON_PAD_NOT_GPIO
        result.detail = (
            f"net {resolved_net!r} lands on {mcu_ref} pad {endpoint.pad} "
            f"({endpoint.pad_name}), which the rulepack maps to no GPIO "
            f"(kind: {rulepack.pads[endpoint.pad].kind})"
        )
        return result

    # ---- Firmware verdict gate ------------------------------------------
    if not claim.resolved:
        result.reason = claim.unresolved_reason
        result.detail = _firmware_unknown_detail(claim)
        return result

    # ---- Both sides supported: compare ----------------------------------
    if claim.gpio == endpoint.gpio:
        result.verdict = Verdict.PASS
        result.reason = (
            f"firmware {contract.firmware_symbol} = GPIO{claim.gpio} matches "
            f"net {resolved_net!r} -> {mcu_ref} pad {endpoint.pad} "
            f"({endpoint.pad_name}) = GPIO{endpoint.gpio}"
        )
    else:
        result.verdict = Verdict.FAIL
        result.reason = (
            f"firmware {contract.firmware_symbol} = GPIO{claim.gpio} but "
            f"net {resolved_net!r} reaches {mcu_ref} pad {endpoint.pad} "
            f"({endpoint.pad_name}) = GPIO{endpoint.gpio}"
        )
    return result


def _firmware_unknown_detail(claim) -> str:
    parts = []
    if claim.declaration is not None:
        parts.append(
            f"symbol {claim.symbol!r} declared at "
            f"{claim.declaration.file}:{claim.declaration.line}"
        )
    else:
        parts.append(f"symbol {claim.symbol!r} has no supported declaration")
    if claim.resolution_chain:
        parts.append("resolution: " + " ; ".join(claim.resolution_chain))
    if claim.conflicting:
        locs = ", ".join(f"{d.file}:{d.line}" for d in claim.conflicting)
        parts.append(f"conflicting declarations at: {locs}")
    return " | ".join(parts)


def run_scan(
    config: PinproofConfig,
    netlist: Netlist,
    firmware: FirmwareProject,
    rulepack: Rulepack,
) -> ScanReport:
    report = ScanReport(
        tool_version=__version__,
        rulepack_id=rulepack.rulepack,
        rulepack_version=rulepack.version,
        config_path=config.config_path,
        mcu_ref=config.project.mcu_ref,
        module=config.project.module,
    )
    for contract in config.roles:
        report.results.append(
            evaluate_role(contract, netlist, firmware, rulepack, config.project.mcu_ref)
        )
    return report
