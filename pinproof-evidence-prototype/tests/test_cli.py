"""End-to-end CLI tests: the three demonstration cases plus usage errors."""

import json

from typer.testing import CliRunner

from pinproof.cli import app

from conftest import FIXTURES

runner = CliRunner()


def test_scan_good_exits_zero():
    result = runner.invoke(app, ["scan", "--config", str(FIXTURES / "good" / "pinproof.yaml")])
    assert result.exit_code == 0, result.output
    assert "PASS 3" in result.output
    assert "FAIL 0" in result.output


def test_scan_mismatch_exits_one_with_both_sides_of_evidence():
    result = runner.invoke(
        app, ["scan", "--config", str(FIXTURES / "mismatch_sda" / "pinproof.yaml")]
    )
    assert result.exit_code == 1, result.output
    # firmware evidence: symbol, value, file:line via the resolution chain
    assert "PIN_SENSOR_SDA" in result.output
    assert "18" in result.output
    assert "pins.h" in result.output
    # hardware evidence: net, pad, mapped GPIO
    assert "pad 23" in result.output
    assert "IO21" in result.output
    assert "GPIO21" in result.output


def test_scan_unsupported_exits_zero_but_reports_unknown():
    result = runner.invoke(
        app, ["scan", "--config", str(FIXTURES / "unsupported_expression" / "pinproof.yaml")]
    )
    assert result.exit_code == 0, result.output
    assert "UNKNOWN 1" in result.output
    assert "unsupported-expression" in result.output


def test_scan_json_output_is_valid():
    result = runner.invoke(
        app,
        ["scan", "--config", str(FIXTURES / "mismatch_sda" / "pinproof.yaml"), "--json"],
    )
    assert result.exit_code == 1
    payload = json.loads(result.output)
    verdicts = {r["role"]: r["verdict"] for r in payload["results"]}
    assert verdicts["sensor_sda"] == "FAIL"


def test_scan_missing_config_is_usage_error():
    result = runner.invoke(app, ["scan", "--config", "does/not/exist.yaml"])
    assert result.exit_code == 2


def test_scan_malformed_contract_is_usage_error(tmp_path):
    bad = tmp_path / "pinproof.yaml"
    bad.write_text("pinproof: 1\nproject: [this, is, not, a, mapping]\n")
    result = runner.invoke(app, ["scan", "--config", str(bad)])
    assert result.exit_code == 2


def test_inspect_hardware_lists_pads():
    result = runner.invoke(
        app,
        [
            "inspect-hardware",
            "--netlist", str(FIXTURES / "good" / "hardware" / "controller.xml"),
            "--mcu-ref", "U1",
        ],
    )
    assert result.exit_code == 0
    assert "SDA" in result.output
    assert "11" in result.output


def test_inspect_hardware_bad_ref_is_usage_error():
    result = runner.invoke(
        app,
        [
            "inspect-hardware",
            "--netlist", str(FIXTURES / "good" / "hardware" / "controller.xml"),
            "--mcu-ref", "U9",
        ],
    )
    assert result.exit_code == 2


def test_inspect_firmware_shows_declarations():
    result = runner.invoke(
        app, ["inspect-firmware", "--project", str(FIXTURES / "good" / "firmware")]
    )
    assert result.exit_code == 0
    assert "PIN_SENSOR_SDA" in result.output
    assert "esp32-s3-devkitc-1" in result.output


def test_inspect_firmware_single_symbol_chain():
    result = runner.invoke(
        app,
        [
            "inspect-firmware",
            "--project", str(FIXTURES / "good" / "firmware"),
            "--symbol", "PIN_SENSOR_SDA",
        ],
    )
    assert result.exit_code == 0
    assert "GPIO18" in result.output
    assert "SDA_GPIO" in result.output


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "pinproof" in result.output
