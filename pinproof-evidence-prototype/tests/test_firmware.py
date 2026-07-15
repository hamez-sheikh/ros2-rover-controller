from pathlib import Path

import pytest

from pinproof.firmware import (
    FirmwareProjectError,
    load_project,
    resolve_symbol,
)
from pinproof.models import (
    REASON_ALIAS_CYCLE,
    REASON_ALIAS_DEPTH_EXCEEDED,
    REASON_AMBIGUOUS_DECLARATION,
    REASON_MISSING_FIRMWARE_SYMBOL,
    REASON_UNSUPPORTED_EXPRESSION,
)

from conftest import FIXTURES


def make_project(tmp_path: Path, header: str) -> Path:
    root = tmp_path / "fw"
    (root / "src").mkdir(parents=True)
    (root / "include").mkdir()
    (root / "platformio.ini").write_text(
        "[env:esp32s3]\nplatform = espressif32\nboard = esp32-s3-devkitc-1\nframework = arduino\n"
    )
    (root / "include" / "pins.h").write_text(header)
    (root / "src" / "main.cpp").write_text('#include "pins.h"\nvoid setup(){}\nvoid loop(){}\n')
    return root


def test_good_fixture_resolves_alias_chain():
    project = load_project(FIXTURES / "good" / "firmware")
    claim = resolve_symbol(project, "PIN_SENSOR_SDA")
    assert claim.resolved and claim.gpio == 18
    # chain: PIN_SENSOR_SDA -> SDA_GPIO -> 18, with file:line provenance
    assert len(claim.resolution_chain) == 2
    assert "pins.h" in claim.resolution_chain[0]


def test_gpio_num_constexpr():
    project = load_project(FIXTURES / "good" / "firmware")
    claim = resolve_symbol(project, "PIN_STATUS_LED")
    assert claim.resolved and claim.gpio == 4
    assert claim.declaration.method == "constexpr-int"


def test_plain_define():
    project = load_project(FIXTURES / "good" / "firmware")
    claim = resolve_symbol(project, "PIN_SENSOR_SCL")
    assert claim.resolved and claim.gpio == 17


def test_missing_symbol(tmp_path):
    project = load_project(make_project(tmp_path, "#define OTHER 5\n"))
    claim = resolve_symbol(project, "PIN_X")
    assert not claim.resolved
    assert claim.unresolved_reason == REASON_MISSING_FIRMWARE_SYMBOL


def test_unsupported_arithmetic(tmp_path):
    project = load_project(make_project(tmp_path, "#define PIN_X (2 + 3)\n"))
    claim = resolve_symbol(project, "PIN_X")
    assert not claim.resolved
    assert claim.unresolved_reason == REASON_UNSUPPORTED_EXPRESSION


def test_unsupported_runtime_expression():
    project = load_project(FIXTURES / "unsupported_expression" / "firmware")
    claim = resolve_symbol(project, "PIN_SENSOR_SDA")
    assert not claim.resolved
    assert claim.unresolved_reason == REASON_UNSUPPORTED_EXPRESSION
    assert "SDA_PIN_OPTIONS" in claim.resolution_chain[0]


def test_alias_cycle(tmp_path):
    project = load_project(make_project(tmp_path, "#define A B\n#define B A\n"))
    claim = resolve_symbol(project, "A")
    assert not claim.resolved
    assert claim.unresolved_reason == REASON_ALIAS_CYCLE


def test_alias_depth_exceeded(tmp_path):
    chain = "\n".join(f"#define A{i} A{i + 1}" for i in range(12)) + "\n#define A12 5\n"
    project = load_project(make_project(tmp_path, chain))
    claim = resolve_symbol(project, "A0")
    assert not claim.resolved
    assert claim.unresolved_reason == REASON_ALIAS_DEPTH_EXCEEDED


def test_conflicting_declarations(tmp_path):
    project = load_project(make_project(tmp_path, "#define PIN_X 5\n#define PIN_X 6\n"))
    claim = resolve_symbol(project, "PIN_X")
    assert not claim.resolved
    assert claim.unresolved_reason == REASON_AMBIGUOUS_DECLARATION
    assert len(claim.conflicting) == 2


def test_duplicate_but_agreeing_declarations(tmp_path):
    project = load_project(make_project(tmp_path, "#define PIN_X 5\n#define PIN_X 5\n"))
    claim = resolve_symbol(project, "PIN_X")
    assert claim.resolved and claim.gpio == 5


def test_function_like_macro_ignored(tmp_path):
    project = load_project(make_project(tmp_path, "#define PIN_OF(x) (x)\n#define PIN_X 7\n"))
    assert "PIN_OF" not in project.symbols
    assert resolve_symbol(project, "PIN_X").gpio == 7


def test_comments_stripped(tmp_path):
    project = load_project(make_project(tmp_path, "#define PIN_X 9 // was 8 on rev A\n"))
    claim = resolve_symbol(project, "PIN_X")
    assert claim.resolved and claim.gpio == 9


def test_cast_wrapper(tmp_path):
    project = load_project(make_project(tmp_path, "constexpr int PIN_X = (gpio_num_t)21;\n"))
    claim = resolve_symbol(project, "PIN_X")
    assert claim.resolved and claim.gpio == 21


def test_missing_platformio_ini(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(FirmwareProjectError):
        load_project(tmp_path / "empty")


def test_board_recorded():
    project = load_project(FIXTURES / "good" / "firmware")
    assert project.board == "esp32-s3-devkitc-1"
    assert project.environments == ["esp32s3"]
