"""The pinproof command-line interface.

Exit codes (SCOPE.md §2):
    0  no proven mismatch (PASS and/or UNKNOWN only)
    1  at least one FAIL (supported evidence proves a mismatch)
    2  usage error (missing/malformed inputs) — says nothing about pins
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .compare import run_scan
from .config import ConfigError, load_config, load_rulepack
from .firmware import FirmwareProject, FirmwareProjectError, load_project, resolve_symbol
from .hardware import NetlistError, load_netlist, mcu_pad_map
from .reporting import print_report, report_to_json

app = typer.Typer(
    name="pinproof",
    help="Deterministic firmware-to-schematic pin consistency checker (Week 1 evidence prototype).",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)

USAGE_ERROR_EXIT = 2


def _usage_error(message: str) -> "typer.Exit":
    err_console.print(f"[bold red]error:[/bold red] {message}")
    return typer.Exit(code=USAGE_ERROR_EXIT)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"pinproof {__version__}")
        raise typer.Exit()


@app.callback()
def _main_callback(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True,
        help="Print version and exit.",
    ),
) -> None:
    """PinProof: PASS / FAIL / UNKNOWN with evidence, never a guess."""


@app.command("inspect-hardware")
def inspect_hardware(
    netlist: Path = typer.Option(..., "--netlist", help="KiCad XML netlist file."),
    mcu_ref: str = typer.Option("U1", "--mcu-ref", help="Schematic reference of the MCU module."),
    as_json: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Show every net connected to the MCU module, pad by pad."""
    try:
        parsed = load_netlist(netlist)
    except NetlistError as exc:
        raise _usage_error(str(exc))

    if mcu_ref not in parsed.components:
        raise _usage_error(
            f"reference {mcu_ref!r} not found in netlist components "
            f"(found: {', '.join(sorted(parsed.components)) or 'none'})"
        )

    pads = mcu_pad_map(parsed, mcu_ref)
    if as_json:
        console.print_json(json.dumps({
            "netlist": str(parsed.source_path),
            "design_source": parsed.design_source,
            "mcu_ref": mcu_ref,
            "component": parsed.components[mcu_ref],
            "pads": pads,
        }))
        return

    comp = parsed.components[mcu_ref]
    console.print(
        f"[bold]{mcu_ref}[/bold] = {comp.get('value', '?')} "
        f"({comp.get('footprint') or 'no footprint field'}) "
        f"in {parsed.source_path.name}"
    )
    table = Table(header_style="bold")
    table.add_column("pad")
    table.add_column("net(s)")
    for pad in sorted(pads, key=lambda p: (len(p), p)):
        table.add_row(pad, ", ".join(pads[pad]))
    console.print(table)
    console.print(f"[dim]{len(pads)} pads of {mcu_ref} appear in nets.[/dim]")


@app.command("inspect-firmware")
def inspect_firmware(
    project: Path = typer.Option(..., "--project", help="PlatformIO project directory."),
    symbol: Optional[str] = typer.Option(None, "--symbol", help="Resolve one symbol and show its chain."),
    as_json: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Show the pin declarations PinProof can (and cannot) extract."""
    try:
        fw: FirmwareProject = load_project(project)
    except FirmwareProjectError as exc:
        raise _usage_error(str(exc))

    if symbol is not None:
        claim = resolve_symbol(fw, symbol)
        if as_json:
            console.print_json(claim.model_dump_json())
            return
        status = f"GPIO{claim.gpio}" if claim.resolved else f"unresolved ({claim.unresolved_reason})"
        console.print(f"[bold]{symbol}[/bold] → {status}")
        for step in claim.resolution_chain:
            console.print(f"  {step}")
        return

    if as_json:
        payload = {
            "project": str(fw.root),
            "board": fw.board,
            "environments": fw.environments,
            "scanned_files": [str(p) for p in fw.scanned_files],
            "symbols": {
                name: [d.model_dump(mode="json") for d in decls]
                for name, decls in sorted(fw.symbols.items())
            },
        }
        console.print_json(json.dumps(payload, default=str))
        return

    console.print(
        f"[bold]{fw.root.name}[/bold] · board: {fw.board or '?'} · "
        f"envs: {', '.join(fw.environments) or '?'} · "
        f"{len(fw.scanned_files)} files scanned"
    )
    if fw.board and "esp32-s3" not in fw.board.lower() and "esp32s3" not in fw.board.lower():
        console.print(
            f"[yellow]warning:[/yellow] board {fw.board!r} does not look like an "
            "ESP32-S3 — Week 1 only supports ESP32-S3-WROOM-1-N8."
        )
    table = Table(header_style="bold")
    table.add_column("symbol")
    table.add_column("value expr")
    table.add_column("where")
    table.add_column("method")
    for name in sorted(fw.symbols):
        for decl in fw.symbols[name]:
            table.add_row(name, decl.value_expr, f"{decl.file}:{decl.line}", decl.method)
    console.print(table)


@app.command("scan")
def scan(
    config_path: Path = typer.Option(..., "--config", help="Path to pinproof.yaml."),
    rulepack_path: Optional[Path] = typer.Option(
        None, "--rulepack", help="Explicit rulepack file (overrides discovery)."
    ),
    as_json: bool = typer.Option(False, "--json", help="Machine-readable report."),
) -> None:
    """Check every role in the contract. Exits 1 only on a proven mismatch."""
    try:
        config = load_config(config_path)
        rulepack = load_rulepack(
            config.project.module,
            config_path=config.config_path,
            explicit_path=rulepack_path or config.project.rulepack_path,
        )
        netlist = load_netlist(config.project.netlist)
        fw = load_project(config.project.firmware)
    except (ConfigError, NetlistError, FirmwareProjectError) as exc:
        raise _usage_error(str(exc))

    if config.project.mcu_ref not in netlist.components:
        raise _usage_error(
            f"MCU ref {config.project.mcu_ref!r} not found in netlist "
            f"{config.project.netlist} "
            f"(found: {', '.join(sorted(netlist.components)) or 'none'})"
        )

    report = run_scan(config, netlist, fw, rulepack)

    if as_json:
        # Plain stdout, not the rich console: rich soft-wraps long lines,
        # which would corrupt machine-readable output.
        print(report_to_json(report))
    else:
        print_report(report, console)

    raise typer.Exit(code=report.exit_code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
