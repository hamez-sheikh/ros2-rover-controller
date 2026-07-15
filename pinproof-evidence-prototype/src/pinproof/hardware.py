"""Hardware-side ingestion: parse a KiCad XML netlist.

The KiCad XML netlist is the ``<export>`` document produced by
``kicad-cli sch export netlist --format kicadxml`` (or Eeschema's BOM/netlist
export in older versions). We read only what Week 1 needs:

* ``components/comp`` -> reference, value, footprint
* ``nets/net`` -> name, and each ``node`` (ref, pin/pad number, pinfunction)

Parsing uses ``xml.etree.ElementTree`` on local, user-supplied files.
See docs/LIMITATIONS.md for the security note about untrusted XML.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .models import (
    HardwareEndpoint,
    NetNode,
    Netlist,
    PadMapping,
    Rulepack,
)


class NetlistError(Exception):
    """A usage-level problem with the netlist file (missing, malformed)."""


def load_netlist(path: Path) -> Netlist:
    """Parse a KiCad XML netlist file into a :class:`Netlist`."""
    path = Path(path)
    if not path.is_file():
        raise NetlistError(f"netlist file not found: {path}")
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise NetlistError(f"netlist is not valid XML ({path}): {exc}") from exc

    root = tree.getroot()
    if root.tag != "export":
        raise NetlistError(
            f"unexpected root element <{root.tag}> in {path}; expected <export> "
            "(is this really a KiCad XML netlist?)"
        )

    netlist = Netlist(source_path=path)

    design = root.find("design")
    if design is not None:
        source = design.findtext("source")
        tool = design.findtext("tool")
        netlist.design_source = source
        netlist.design_tool = tool

    for comp in root.iterfind("./components/comp"):
        ref = comp.get("ref")
        if not ref:
            continue
        netlist.components[ref] = {
            "value": comp.findtext("value") or "",
            "footprint": comp.findtext("footprint") or "",
        }

    for net in root.iterfind("./nets/net"):
        name = net.get("name")
        if not name:
            continue
        nodes = [
            NetNode(
                ref=node.get("ref", ""),
                pin=node.get("pin", ""),
                pinfunction=node.get("pinfunction"),
                pintype=node.get("pintype"),
            )
            for node in net.iterfind("node")
        ]
        netlist.nets[name] = nodes

    return netlist


def find_net(netlist: Netlist, net_name: str) -> Optional[str]:
    """Resolve a contract net name against the netlist.

    Match order (deterministic):
    1. exact match;
    2. exactly one net whose name ends with ``/<net_name>`` (KiCad prefixes
       hierarchical-sheet nets with the sheet path). Zero or multiple such
       candidates -> no match (the caller reports UNKNOWN, never a guess).
    """
    if net_name in netlist.nets:
        return net_name
    suffix = "/" + net_name
    candidates = [n for n in netlist.nets if n.endswith(suffix)]
    if len(candidates) == 1:
        return candidates[0]
    return None


def mcu_nodes_on_net(netlist: Netlist, net_name: str, mcu_ref: str) -> list[NetNode]:
    """All nodes of ``mcu_ref`` on the (already resolved) net name."""
    return [n for n in netlist.nets.get(net_name, []) if n.ref == mcu_ref]


def endpoint_from_node(
    node: NetNode, net_name: str, mcu_ref: str, rulepack: Rulepack
) -> HardwareEndpoint:
    """Attach the rulepack pad->GPIO mapping to a netlist node."""
    mapping: Optional[PadMapping] = rulepack.pads.get(node.pin)
    return HardwareEndpoint(
        mcu_ref=mcu_ref,
        net=net_name,
        pad=node.pin,
        pad_name=mapping.name if mapping else None,
        gpio=mapping.gpio if mapping else None,
    )


def mcu_pad_map(netlist: Netlist, mcu_ref: str) -> dict[str, list[str]]:
    """pad number -> list of net names, for every net touching ``mcu_ref``.

    Used by ``pinproof inspect-hardware``.
    """
    result: dict[str, list[str]] = {}
    for net_name, nodes in netlist.nets.items():
        for node in nodes:
            if node.ref == mcu_ref:
                result.setdefault(node.pin, []).append(net_name)
    return result
