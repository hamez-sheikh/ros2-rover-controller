"""Comparison-engine tests, including seeded mutations of the good fixture.

The mutation tests are the heart of the falsification exercise: we take a
known-good project, break it in one precise way, and assert the checker
produces exactly the verdict the SCOPE.md decision table demands — never a
silent PASS.
"""

from pathlib import Path

from pinproof.compare import run_scan
from pinproof.config import load_config, load_rulepack
from pinproof.firmware import load_project
from pinproof.hardware import load_netlist
from pinproof.models import (
    REASON_AMBIGUOUS_NET_ENDPOINTS,
    REASON_MISSING_FIRMWARE_SYMBOL,
    REASON_NET_NOT_FOUND,
    REASON_NET_NOT_ON_MODULE,
    REASON_PAD_NOT_GPIO,
    REASON_RULEPACK_MISSING_PAD,
    Verdict,
)

from conftest import FIXTURES


def scan_dir(fixture_dir: Path):
    config = load_config(fixture_dir / "pinproof.yaml")
    rulepack = load_rulepack(config.project.module, config_path=config.config_path)
    netlist = load_netlist(config.project.netlist)
    firmware = load_project(config.project.firmware)
    return run_scan(config, netlist, firmware, rulepack)


def result_for(report, role):
    return next(r for r in report.results if r.role == role)


# ---------------------------------------------------------------- checked-in fixtures

def test_good_fixture_all_pass():
    report = scan_dir(FIXTURES / "good")
    assert [r.verdict for r in report.results] == [Verdict.PASS] * 3
    assert report.exit_code == 0


def test_mismatch_fixture_fails_with_evidence():
    report = scan_dir(FIXTURES / "mismatch_sda")
    sda = result_for(report, "sensor_sda")
    assert sda.verdict is Verdict.FAIL
    assert report.exit_code == 1
    # evidence: both sides, with numbers
    assert sda.firmware.gpio == 18
    assert sda.hardware.pad == "23"
    assert sda.hardware.gpio == 21
    # unaffected roles still pass
    assert result_for(report, "sensor_scl").verdict is Verdict.PASS
    assert result_for(report, "status_led").verdict is Verdict.PASS


def test_unsupported_fixture_is_unknown_not_blocking():
    report = scan_dir(FIXTURES / "unsupported_expression")
    sda = result_for(report, "sensor_sda")
    assert sda.verdict is Verdict.UNKNOWN
    assert sda.firmware.unresolved_reason == "unsupported-expression"
    assert report.exit_code == 0  # UNKNOWN never blocks CI


# ---------------------------------------------------------------- seeded mutations

def test_mutation_removed_symbol_is_unknown(good_copy: Path):
    pins = good_copy / "firmware" / "include" / "pins.h"
    pins.write_text(pins.read_text().replace("#define PIN_SENSOR_SCL 17", ""))
    report = scan_dir(good_copy)
    scl = result_for(report, "sensor_scl")
    assert scl.verdict is Verdict.UNKNOWN
    assert scl.reason == REASON_MISSING_FIRMWARE_SYMBOL
    assert report.exit_code == 0


def test_mutation_rerouted_net_is_fail(good_copy: Path):
    xml = good_copy / "hardware" / "controller.xml"
    # Move SCL from pad 10 (IO17/GPIO17) to pad 12 (IO8/GPIO8).
    xml.write_text(
        xml.read_text().replace(
            '<node ref="U1" pin="10" pinfunction="IO17" pintype="bidirectional"/>',
            '<node ref="U1" pin="12" pinfunction="IO8" pintype="bidirectional"/>',
        )
    )
    report = scan_dir(good_copy)
    scl = result_for(report, "sensor_scl")
    assert scl.verdict is Verdict.FAIL
    assert scl.firmware.gpio == 17
    assert scl.hardware.gpio == 8
    assert report.exit_code == 1


def test_mutation_net_deleted_is_unknown(good_copy: Path):
    contract = good_copy / "pinproof.yaml"
    contract.write_text(contract.read_text().replace("net: LED_STATUS", "net: LED_STATUS_TYPO"))
    report = scan_dir(good_copy)
    led = result_for(report, "status_led")
    assert led.verdict is Verdict.UNKNOWN
    assert led.reason == REASON_NET_NOT_FOUND


def test_mutation_net_off_module_is_unknown(good_copy: Path):
    xml = good_copy / "hardware" / "controller.xml"
    xml.write_text(
        xml.read_text().replace(
            '<node ref="U1" pin="4" pinfunction="IO4" pintype="bidirectional"/>',
            "",
        )
    )
    report = scan_dir(good_copy)
    led = result_for(report, "status_led")
    assert led.verdict is Verdict.UNKNOWN
    assert led.reason == REASON_NET_NOT_ON_MODULE


def test_mutation_pad_missing_from_rulepack_is_unknown(good_copy: Path):
    rp = good_copy.parent / "rulepacks" / "esp32-s3-wroom-1-n8.yaml"
    rp.write_text(rp.read_text().replace('"4":  { name: IO4,  gpio: 4 }', ""))
    report = scan_dir(good_copy)
    led = result_for(report, "status_led")
    assert led.verdict is Verdict.UNKNOWN
    assert led.reason == REASON_RULEPACK_MISSING_PAD


def test_mutation_net_on_power_pad_is_unknown(good_copy: Path):
    xml = good_copy / "hardware" / "controller.xml"
    # Route LED_STATUS to pad 3 (EN) — a control pad with no GPIO mapping.
    xml.write_text(
        xml.read_text().replace(
            '<node ref="U1" pin="4" pinfunction="IO4" pintype="bidirectional"/>',
            '<node ref="U1" pin="3" pinfunction="EN" pintype="input"/>',
        )
    )
    report = scan_dir(good_copy)
    led = result_for(report, "status_led")
    assert led.verdict is Verdict.UNKNOWN
    assert led.reason == REASON_PAD_NOT_GPIO


def test_mutation_net_on_two_module_pads_is_unknown(good_copy: Path):
    xml = good_copy / "hardware" / "controller.xml"
    xml.write_text(
        xml.read_text().replace(
            '<node ref="U1" pin="4" pinfunction="IO4" pintype="bidirectional"/>',
            '<node ref="U1" pin="4" pinfunction="IO4" pintype="bidirectional"/>\n'
            '      <node ref="U1" pin="5" pinfunction="IO5" pintype="bidirectional"/>',
        )
    )
    report = scan_dir(good_copy)
    led = result_for(report, "status_led")
    assert led.verdict is Verdict.UNKNOWN
    assert led.reason == REASON_AMBIGUOUS_NET_ENDPOINTS
