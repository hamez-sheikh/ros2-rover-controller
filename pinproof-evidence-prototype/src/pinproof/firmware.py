"""Firmware-side ingestion: PlatformIO project scan + deliberately tiny
pin-declaration extractor.

Honesty rules (SCOPE.md §2, §6):

* We support ONLY the declaration forms listed in SCOPE.md §3. Everything
  else becomes an *explicit* UNKNOWN with a machine-readable reason — never
  a guess, never a silent PASS.
* Every extracted value keeps its provenance: file, line, extraction method,
  and (for aliases) the full resolution chain.

This is a line-oriented regex extractor, not a C parser. It does not run the
preprocessor, follow ``#include``, or understand ``#ifdef``. That boundary is
the Week 1 experiment.
"""

from __future__ import annotations

import configparser
import re
from pathlib import Path
from typing import Optional

from .models import (
    REASON_ALIAS_CYCLE,
    REASON_ALIAS_DEPTH_EXCEEDED,
    REASON_AMBIGUOUS_DECLARATION,
    REASON_MISSING_FIRMWARE_SYMBOL,
    REASON_UNSUPPORTED_EXPRESSION,
    FirmwareClaim,
    RawDeclaration,
)

MAX_ALIAS_DEPTH = 8

SOURCE_EXTENSIONS = {".h", ".hpp", ".c", ".cc", ".cpp", ".ino"}

# Directories scanned inside the PlatformIO project (plus src_dir override).
DEFAULT_SOURCE_DIRS = ("src", "include", "lib")

_IDENT = r"[A-Za-z_]\w*"

# #define NAME <expr>            (function-like macros excluded via (?!\())
DEFINE_RE = re.compile(rf"^\s*#\s*define\s+({_IDENT})(?!\()\s+(.+?)\s*$")

# [static] const|constexpr <int-ish type> NAME = <expr>;
CONST_RE = re.compile(
    rf"^\s*(?:static\s+)?(const|constexpr)\s+"
    rf"(?:unsigned\s+)?(?:int|long|short|uint8_t|uint16_t|uint32_t|int8_t|int16_t|int32_t|gpio_num_t)\s+"
    rf"({_IDENT})\s*=\s*([^;]+);"
)

# Supported value expressions:
INT_RE = re.compile(r"^\d+$")
GPIO_NUM_RE = re.compile(r"^GPIO_NUM_(\d+)$")
ALIAS_RE = re.compile(rf"^({_IDENT})$")
# A single, explicitly whitelisted cast wrapper, e.g. (gpio_num_t)18
CAST_RE = re.compile(r"^\((?:gpio_num_t|int|uint8_t)\)\s*(.+)$")


class FirmwareProjectError(Exception):
    """A usage-level problem with the firmware project (missing dir/ini)."""


class FirmwareProject:
    """A scanned PlatformIO project: symbol table + platformio.ini facts."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.board: Optional[str] = None
        self.environments: list[str] = []
        self.src_dir = "src"
        self.symbols: dict[str, list[RawDeclaration]] = {}
        self.scanned_files: list[Path] = []


def _strip_comments(line: str) -> str:
    """Remove // and single-line /* */ comments. Multi-line comments are not
    tracked; a declaration inside one may be picked up — an accepted Week 1
    limitation (documented in docs/LIMITATIONS.md)."""
    line = re.sub(r"/\*.*?\*/", " ", line)
    idx = line.find("//")
    if idx != -1:
        line = line[:idx]
    return line.rstrip()


def load_project(root: Path) -> FirmwareProject:
    """Read platformio.ini and scan source files for supported declarations."""
    root = Path(root)
    if not root.is_dir():
        raise FirmwareProjectError(f"firmware project directory not found: {root}")
    ini_path = root / "platformio.ini"
    if not ini_path.is_file():
        raise FirmwareProjectError(f"platformio.ini not found in {root}")

    project = FirmwareProject(root)

    parser = configparser.ConfigParser()
    try:
        parser.read(ini_path, encoding="utf-8")
    except configparser.Error as exc:
        raise FirmwareProjectError(f"platformio.ini is malformed: {exc}") from exc

    for section in parser.sections():
        if section.startswith("env:"):
            project.environments.append(section[len("env:"):])
            if project.board is None and parser.has_option(section, "board"):
                project.board = parser.get(section, "board")
    if parser.has_section("platformio") and parser.has_option("platformio", "src_dir"):
        project.src_dir = parser.get("platformio", "src_dir")

    scan_dirs = []
    for d in (project.src_dir, *DEFAULT_SOURCE_DIRS):
        p = root / d
        if p.is_dir() and p not in scan_dirs:
            scan_dirs.append(p)

    for directory in scan_dirs:
        for path in sorted(directory.rglob("*")):
            if path.suffix.lower() in SOURCE_EXTENSIONS and path.is_file():
                _scan_file(project, path)

    return project


def _scan_file(project: FirmwareProject, path: Path) -> None:
    project.scanned_files.append(path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_comments(raw_line)
        m = DEFINE_RE.match(line)
        if m:
            symbol, expr = m.group(1), m.group(2).strip()
            decl = RawDeclaration(
                symbol=symbol,
                value_expr=expr,
                file=path,
                line=lineno,
                method="define",
                matched_text=raw_line.strip(),
            )
            project.symbols.setdefault(symbol, []).append(decl)
            continue
        m = CONST_RE.match(line)
        if m:
            kind, symbol, expr = m.group(1), m.group(2), m.group(3).strip()
            decl = RawDeclaration(
                symbol=symbol,
                value_expr=expr,
                file=path,
                line=lineno,
                method=f"{kind}-int",
                matched_text=raw_line.strip(),
            )
            project.symbols.setdefault(symbol, []).append(decl)


def _resolve_expr(expr: str) -> tuple[Optional[int], Optional[str], Optional[str]]:
    """Resolve one expression -> (gpio, next_alias, unsupported_reason).

    Exactly one of the three return slots is non-None.
    """
    expr = expr.strip()
    # Peel a single whitelisted cast, e.g. "(gpio_num_t)18" -> "18"
    m = CAST_RE.match(expr)
    if m:
        expr = m.group(1).strip()
    if INT_RE.match(expr):
        return int(expr), None, None
    m = GPIO_NUM_RE.match(expr)
    if m:
        return int(m.group(1)), None, None
    m = ALIAS_RE.match(expr)
    if m:
        return None, m.group(1), None
    return None, None, REASON_UNSUPPORTED_EXPRESSION


def resolve_symbol(project: FirmwareProject, symbol: str) -> FirmwareClaim:
    """Resolve a contract symbol to a GPIO number, or an explicit UNKNOWN.

    Follows alias chains up to MAX_ALIAS_DEPTH with cycle detection.
    Multiple declarations of one symbol that resolve inconsistently ->
    ``ambiguous-declaration``.
    """
    claim = FirmwareClaim(symbol=symbol)

    decls = project.symbols.get(symbol)
    if not decls:
        claim.unresolved_reason = REASON_MISSING_FIRMWARE_SYMBOL
        return claim

    claim.declaration = decls[0]

    if len(decls) > 1:
        # Multiple declarations: only acceptable if every one of them
        # resolves to the same GPIO. Otherwise: ambiguous.
        values: list[Optional[int]] = []
        for d in decls:
            sub = _resolve_from_decl(project, d)
            values.append(sub.gpio if sub.resolved else None)
        if any(v is None for v in values) or len(set(values)) != 1:
            claim.unresolved_reason = REASON_AMBIGUOUS_DECLARATION
            claim.conflicting = decls
            return claim
        # All agree: fall through and produce the chain from the first one.

    resolved = _resolve_from_decl(project, decls[0])
    resolved.conflicting = decls if len(decls) > 1 else []
    return resolved


def _resolve_from_decl(project: FirmwareProject, decl: RawDeclaration) -> FirmwareClaim:
    claim = FirmwareClaim(symbol=decl.symbol, declaration=decl)
    seen: set[str] = {decl.symbol}
    current = decl
    for _ in range(MAX_ALIAS_DEPTH):
        gpio, alias, reason = _resolve_expr(current.value_expr)
        if gpio is not None:
            claim.resolution_chain.append(
                f"{current.symbol} -> {gpio}  ({_rel(project, current.file)}:{current.line}, {current.method})"
            )
            claim.gpio = gpio
            claim.resolved = True
            return claim
        if reason is not None:
            claim.resolution_chain.append(
                f"{current.symbol} -> {current.value_expr!r}  ({_rel(project, current.file)}:{current.line}, {current.method})"
            )
            claim.unresolved_reason = reason
            return claim
        # alias step
        assert alias is not None
        claim.resolution_chain.append(
            f"{current.symbol} -> {alias}  ({_rel(project, current.file)}:{current.line}, {current.method})"
        )
        if alias in seen:
            claim.unresolved_reason = REASON_ALIAS_CYCLE
            return claim
        seen.add(alias)
        next_decls = project.symbols.get(alias)
        if not next_decls:
            claim.unresolved_reason = REASON_MISSING_FIRMWARE_SYMBOL
            claim.resolution_chain.append(f"{alias} -> (no supported declaration found)")
            return claim
        if len(next_decls) > 1:
            sub_values = set()
            for d in next_decls:
                sub = _resolve_from_decl(project, d)
                sub_values.add(sub.gpio if sub.resolved else None)
            if len(sub_values) != 1 or None in sub_values:
                claim.unresolved_reason = REASON_AMBIGUOUS_DECLARATION
                claim.conflicting = next_decls
                return claim
        current = next_decls[0]
    claim.unresolved_reason = REASON_ALIAS_DEPTH_EXCEEDED
    return claim


def _rel(project: FirmwareProject, path: Path) -> str:
    try:
        return str(Path(path).relative_to(project.root))
    except ValueError:
        return str(path)
