# PinProof — Week 1 Scope

This document is the contract for Week 1. If a piece of work is not in here, it goes to `BACKLOG.md`, not into the code.

## 1. The Week 1 question

> Can a local CLI, with no human in the loop, independently extract the same pin fact from two sources — a KiCad XML netlist (hardware truth) and PlatformIO firmware source (firmware truth) — and, when they disagree, prove the mismatch with exact evidence (file, line, net, pad, GPIO numbers on both sides)? If it cannot do this for one board, one MCU, and a deliberately narrow set of firmware patterns, the larger product hypothesis is falsified and we stop.

## 2. Verdict semantics

Every role in `pinproof.yaml` gets exactly one verdict. Verdicts are per-role; the run's exit code is derived from the worst per-role verdict.

**PASS** — Both sides produced *supported* evidence, and the effective firmware GPIO equals the GPIO reached via schematic net → U1 module pad → rulepack pad→GPIO mapping. Examples:

1. `#define PIN_SDA 8` and net `I2C_SDA` lands on the U1 pad the rulepack maps to GPIO8.
2. `constexpr int LED = GPIO_NUM_4;` matches net `STATUS_LED` on the pad mapped to GPIO4.
3. `#define UART_TX MY_TX` where `MY_TX` resolves in one alias step to `43`, and the net agrees via the rulepack.

**FAIL** — Both sides produced supported evidence and the GPIO numbers *provably differ*. FAIL is the **only** condition that produces a nonzero success/failure exit; it is the only verdict allowed to block CI. Examples:

1. Firmware says `#define PIN_SDA 8`; netlist puts `I2C_SDA` on the pad mapped to GPIO9.
2. A chained alias resolves (within depth limit, no cycle) to `5`; the contract net maps to GPIO6.
3. Two supported firmware declarations of the same symbol resolve to the same value, but that value differs from the netlist-derived GPIO.

**UNKNOWN** — We could not obtain supported evidence on at least one side, or evidence is ambiguous. UNKNOWN is **never** silently converted to PASS, and never blocks CI (exit 0), but it is always printed with a machine-readable reason. Examples:

1. `#define PIN_SDA (BASE + 2)` — arithmetic is an unsupported expression → UNKNOWN, reason `unsupported-expression`.
2. The contract names firmware symbol `PIN_SDA` but no supported declaration of it exists → UNKNOWN, reason `missing-firmware-symbol`.
3. The contract net exists but connects to no U1 pad, or the pad is absent from the rulepack → UNKNOWN, reason `net-not-on-module` / `rulepack-missing-pad`.

Ambiguity (e.g., two supported declarations resolving to *different* values, or an alias cycle) is UNKNOWN, not a guess.

| Exit code | Meaning |
|---|---|
| `0` | No FAIL verdicts. PASS and/or UNKNOWN only. |
| `1` | At least one FAIL verdict (proven mismatch). |
| `2` | Usage error: missing/unreadable input file, malformed `pinproof.yaml`, bad CLI flags. Says nothing about pins. |

## 3. In scope

- Python 3.12 local CLI named `pinproof`; runs offline, no network.
- **Hardware side:** parse ONE KiCad XML netlist; locate the configured MCU ref (`U1` in fixtures), expected to be an ESP32-S3-WROOM-1-N8 module; extract pad→net connections for it.
- **Rulepack:** a hand-authored ESP32-S3-WROOM-1 pad→GPIO table shipped with the repo (`rulepacks/`), with datasheet provenance recorded.
- **Firmware side:** scan a PlatformIO project and recognize ONLY:
  - `#define NAME <int>`
  - `#define NAME GPIO_NUM_<int>`
  - `const int NAME = <int>;`
  - `constexpr int NAME = GPIO_NUM_<int>;`
  - deterministic aliases to any of the above, single-step or chained (e.g., `#define A B`, `B` → `#define B 5`), with an explicit depth limit and cycle detection.
- **Contract:** `pinproof.yaml` mapping role → { schematic net name, firmware symbol name }. The contract never contains GPIO numbers — both numbers must be *derived*.
- **Comparison and report:** per-role verdict with evidence (firmware `file:line` and matched text; netlist net, U1 pad, rulepack GPIO), human-readable output plus exit code per the table above.
- Three checked-in fixtures (`good`, `mismatch_sda`, `unsupported_expression`), a pytest suite, and a `scripts/demo.sh` that runs all three.

## 4. Out of scope (do not build in Week 1)

- **LLMs / RAG / embeddings** — the hypothesis is about deterministic extraction; adding a model hides whether extraction works.
- **Web UI** — a CLI falsifies the hypothesis faster; UI proves nothing about it.
- **Cloud / hosting / SaaS anything** — local runs are reproducible and free; deployment is a Week-N problem.
- **Accounts / auth** — no users exist yet.
- **Altium (or any non-KiCad ECAD)** — one netlist format is enough to test the idea.
- **Arbitrary C parsing (preprocessor, AST, clang)** — the regex-level grammar above is the experiment; general parsing is a rabbit hole that delays the answer by weeks.
- **STM32 or any MCU other than ESP32-S3-WROOM-1** — a second rulepack adds work, not information.
- **Simulation / electrical checks** — different product entirely.
- **Autofix / suggested patches** — detection must be trustworthy before repair is honest to attempt.
- **Multiple netlists / multi-board projects** — one board answers the question.
- **Branding, incorporation, pricing** — nothing to brand until the hypothesis survives.

## 5. Acceptance tests

Week 1 is done when all of these hold:

1. `pinproof scan` on fixture `good` prints PASS for every role and exits `0`.
2. Fixture `mismatch_sda` exits `1`, and the report names the firmware `file:line` and value **and** the netlist net, U1 pad, and rulepack GPIO.
3. Deleting the firmware symbol from a fixture yields UNKNOWN (`missing-firmware-symbol`), not PASS, exit `0`.
4. An alias cycle (`#define A B` / `#define B A`) yields UNKNOWN with reason `alias-cycle`.
5. An alias chain deeper than the depth limit yields UNKNOWN with reason `alias-depth-exceeded`.
6. A contract net whose U1 pad is missing from the rulepack yields UNKNOWN with reason `rulepack-missing-pad`.
7. `#define PIN_X (2 + 3)` yields UNKNOWN (`unsupported-expression`) — never a parsed value, never PASS.
8. A missing netlist path or malformed `pinproof.yaml` exits `2` with a usage message and no verdicts.
9. Two conflicting supported declarations of the same symbol yield UNKNOWN with reason `ambiguous-declaration`, citing both `file:line` locations.
10. `pytest` is green, and `./scripts/demo.sh` runs all three fixtures printing the expected verdict (PASS / FAIL / UNKNOWN) for each.

## 6. Known limitations (stated in the README too)

- Firmware extraction is heuristic line/regex matching, not compilation: it ignores `#ifdef` branches, includes, and macros with arguments. UNKNOWN is the honest fallback, and we expect plenty of it.
- Exactly one module (ESP32-S3-WROOM-1-N8 at the configured ref) is supported; any other module is UNKNOWN territory.
- Fixture netlists are hand-authored in the documented KiCad XML netlist schema, so Week 1 does not prove robustness against messy real-world KiCad exports.
- The rulepack is hand-typed from the datasheet and may be incomplete or wrong; rulepack errors produce confident-looking verdicts — verify it once against the datasheet.

## 7. Scope-creep tripwire

During Week 1, every feature idea — yours, a friend's, a professor's — gets one line in `BACKLOG.md` and zero lines of code. The only allowed work is making the acceptance tests above pass. If a task doesn't move one of them, it waits.
