"""Console and JSON reporting.

The report's job is to make every verdict *auditable*: a reader must be able
to open the named files at the named lines/pads and re-derive the verdict by
hand. If a verdict can't be audited that way, it shouldn't be printed.
"""

from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import RoleResult, ScanReport, Verdict

VERDICT_STYLE = {
    Verdict.PASS: "bold green",
    Verdict.FAIL: "bold red",
    Verdict.UNKNOWN: "bold yellow",
}

VERDICT_MARK = {
    Verdict.PASS: "✔ PASS",
    Verdict.FAIL: "✖ FAIL",
    Verdict.UNKNOWN: "? UNKNOWN",
}


def print_report(report: ScanReport, console: Console) -> None:
    header = (
        f"pinproof v{report.tool_version} · module {report.module} ({report.mcu_ref}) · "
        f"rulepack {report.rulepack_id} v{report.rulepack_version}"
    )
    console.print(Panel(header, style="dim"))

    for result in report.results:
        _print_role(result, console)

    counts = report.counts
    summary = Text()
    summary.append(f"PASS {counts['PASS']}", style="green")
    summary.append("  ·  ")
    summary.append(f"FAIL {counts['FAIL']}", style="red")
    summary.append("  ·  ")
    summary.append(f"UNKNOWN {counts['UNKNOWN']}", style="yellow")
    summary.append(f"   →   exit code {report.exit_code}")
    console.print(summary)
    if counts["UNKNOWN"]:
        console.print(
            "[yellow]UNKNOWN means missing or unsupported evidence — it is not a pass. "
            "See docs/LIMITATIONS.md.[/yellow]"
        )


def _print_role(result: RoleResult, console: Console) -> None:
    style = VERDICT_STYLE[result.verdict]
    title = Text()
    title.append(VERDICT_MARK[result.verdict], style=style)
    title.append(f"  role: {result.role}")

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column(style="dim", no_wrap=True)
    table.add_column(overflow="fold")

    if result.reason:
        table.add_row("reason", result.reason)
    if result.detail:
        table.add_row("detail", result.detail)

    hw = result.hardware
    if hw is not None:
        gpio = f"GPIO{hw.gpio}" if hw.gpio is not None else "(no GPIO mapping)"
        table.add_row(
            "hardware",
            f"net {hw.net!r} → {hw.mcu_ref} pad {hw.pad}"
            + (f" ({hw.pad_name})" if hw.pad_name else "")
            + f" → {gpio}",
        )
    elif result.hardware_endpoints:
        for ep in result.hardware_endpoints:
            table.add_row(
                "hardware",
                f"net {ep.net!r} → {ep.mcu_ref} pad {ep.pad}"
                + (f" ({ep.pad_name})" if ep.pad_name else " (pad not in rulepack)"),
            )

    fw = result.firmware
    if fw is not None:
        if fw.resolved:
            table.add_row("firmware", f"{fw.symbol} = GPIO{fw.gpio}")
        else:
            table.add_row("firmware", f"{fw.symbol} — unresolved ({fw.unresolved_reason})")
        for step in fw.resolution_chain:
            table.add_row("", step)
        for decl in fw.conflicting:
            table.add_row("conflict", f"{decl.matched_text}  ({decl.file}:{decl.line})")

    console.print(Panel(table, title=title, title_align="left", border_style=style.split()[-1]))


def report_to_json(report: ScanReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2, default=str)
