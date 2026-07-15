# Limitations — read before trusting a verdict

PinProof Week 1 is a falsification prototype. These boundaries are deliberate;
several are load-bearing for honesty (see SCOPE.md §6).

## Extraction boundaries

- **Firmware parsing is line-level and heuristic.** No preprocessor, no
  `#include` following, no AST. Consequences:
  - `#ifdef` branches are all scanned as if active; two branches defining the
    same symbol differently surface as `ambiguous-declaration` (UNKNOWN) even
    though a real compile would pick one. This is conservative by design.
  - Multi-line declarations and function-like macros are ignored.
  - Declarations inside multi-line `/* ... */` comments may still be picked up
    (only single-line comment stripping is implemented).
- **Supported value grammar is tiny on purpose:** integer literal,
  `GPIO_NUM_<n>`, a whitelisted single cast, and identifier aliases (depth ≤ 8,
  cycle-detected). Arithmetic, arrays, function calls, ternaries → UNKNOWN.
- **Hardware side trusts the netlist.** PinProof does not read `.kicad_sch`
  directly; if your netlist export is stale, the verdict is about the stale
  netlist. Re-export before trusting a run
  (`kicad-cli sch export netlist --format kicadxml ...`).
- **Net-name resolution** matches exact names, then a *unique* hierarchical
  suffix (`/sensors/SDA` for contract net `SDA`). Two candidate suffixed nets →
  UNKNOWN, not a guess.
- **One module, one ref.** ESP32-S3-WROOM-1-N8 at the contract's `mcu_ref`.
  A net touching the module on multiple pads → `ambiguous-net-endpoints`
  (UNKNOWN) rather than tool adjudication.

## Rulepack risk (the most important one)

The pad→GPIO table in `rulepacks/esp32-s3-wroom-1-n8.yaml` was transcribed by
hand from the Espressif datasheet (provenance recorded in the file). Only the
pads used by the fixtures (4, 10, 11, 23) have been verified end-to-end through
the tool. **A wrong rulepack row produces a confidently wrong verdict** — the
one failure mode this design cannot detect by itself. Before relying on a
verdict involving another pad, check that row against the datasheet once.

## False-confidence review (what could make PinProof lie?)

| Threat | Mitigation status |
|---|---|
| Wrong rulepack row → wrong PASS/FAIL | Provenance + status field + this warning; independent re-verification is on the backlog |
| Stale netlist export → verdict about old hardware | Documented; future: read `.kicad_sch` directly or check timestamps |
| Firmware heuristic mis-parses an exotic declaration as a supported one | Grammar is narrow and anchored (whole-line regexes); every claim prints its `file:line` + matched method so a human can audit in seconds |
| `#ifdef`-selected values | Conservative UNKNOWN via ambiguity, see above |
| Contract typo (wrong net name) | Fails safe: `net-not-found` → UNKNOWN, never PASS |

## Security notes

- **XML:** netlists are parsed with `xml.etree.ElementTree`, which does not
  resolve external entities (Python's stdlib expat has DTD/entity limits), but
  PinProof still assumes **local, trusted input files** — do not point it at
  hostile XML from strangers; a maliciously deep document can still consume
  memory/CPU. If the tool ever runs server-side, switch to `defusedxml`.
- **YAML:** contracts and rulepacks are loaded exclusively with
  `yaml.safe_load` — no object construction, no code execution.
- **No network:** the tool makes zero network calls; the only files written
  are what you redirect yourself. Reading untrusted *firmware* files is safe
  in the sense that they are only regex-scanned, never executed or compiled.
- **CI use:** the GitHub Action pattern is `pinproof scan --config ... ` in a
  job with no secrets exposed; the tool needs none.

## Not limitations, decisions

No LLM, no cloud, no autofix, no second MCU family, no Altium: see SCOPE.md §4.
