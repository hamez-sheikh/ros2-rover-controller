from pathlib import Path

import pytest

from pinproof.hardware import (
    NetlistError,
    find_net,
    load_netlist,
    mcu_nodes_on_net,
    mcu_pad_map,
)

from conftest import FIXTURES

GOOD = FIXTURES / "good" / "hardware" / "controller.xml"


def test_loads_components_and_nets():
    netlist = load_netlist(GOOD)
    assert "U1" in netlist.components
    assert netlist.components["U1"]["value"] == "ESP32-S3-WROOM-1-N8"
    assert "SDA" in netlist.nets
    assert "GND" in netlist.nets


def test_sda_lands_on_pad_11():
    netlist = load_netlist(GOOD)
    nodes = mcu_nodes_on_net(netlist, "SDA", "U1")
    assert [n.pin for n in nodes] == ["11"]
    assert nodes[0].pinfunction == "IO18"


def test_pad_map_covers_power_pins():
    netlist = load_netlist(GOOD)
    pads = mcu_pad_map(netlist, "U1")
    assert pads["1"] == ["GND"]
    assert pads["40"] == ["GND"]
    assert "SDA" in pads["11"]


def test_find_net_exact_and_hierarchical(tmp_path: Path):
    netlist = load_netlist(GOOD)
    assert find_net(netlist, "SDA") == "SDA"
    # Hierarchical suffix: exactly one candidate resolves...
    netlist.nets["/sensors/IMU_INT"] = []
    assert find_net(netlist, "IMU_INT") == "/sensors/IMU_INT"
    # ...but two candidates is ambiguous -> None, never a guess.
    netlist.nets["/radio/IMU_INT"] = []
    assert find_net(netlist, "IMU_INT") is None
    assert find_net(netlist, "NO_SUCH_NET") is None


def test_missing_file_raises_usage_error(tmp_path: Path):
    with pytest.raises(NetlistError):
        load_netlist(tmp_path / "nope.xml")


def test_malformed_xml_raises_usage_error(tmp_path: Path):
    bad = tmp_path / "bad.xml"
    bad.write_text("<export><nets>")
    with pytest.raises(NetlistError):
        load_netlist(bad)


def test_wrong_root_element_raises(tmp_path: Path):
    bad = tmp_path / "notnetlist.xml"
    bad.write_text("<html></html>")
    with pytest.raises(NetlistError, match="expected <export>"):
        load_netlist(bad)
