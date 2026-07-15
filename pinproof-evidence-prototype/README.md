# PinProof — evidence prototype (Week 1)

**One question, honestly answered:**

> Can one small, local checker independently extract hardware and firmware pin
> information and catch one deliberately introduced mismatch with exact evidence?

PinProof reads three things — a **KiCad XML netlist**, a **PlatformIO firmware
project**, and a small **role contract** (`pinproof.yaml`) that names *nets* and
*firmware symbols* but never GPIO numbers — and answers, per role:

- **PASS** — both sides independently derive the same GPIO.
- **FAIL** — both sides are supported evidence and they *provably disagree*.
  This is the only thing that exits nonzero (CI gate).
- **UNKNOWN** — the evidence is missing, unsupported, or ambiguous. UNKNOWN is
  printed loudly with a machine-readable reason and **never silently becomes a
  PASS** — and never blocks CI.

This is *not* a product. It is a falsification experiment for the "Interface
Contract CI" hypothesis. Read [`SCOPE.md`](SCOPE.md) before writing any code —
it defines what Week 1 is allowed to contain.

## Quick start (GitHub Codespaces or any Linux + Python ≥3.10)

In a Codespace, the dev container installs everything automatically
(`.devcontainer/`). Locally:

```bash
pip install -e ".[dev]"
```

Then run the three demonstration cases:

```bash
# Case 1 — known-good project: schematic and firmware agree  →  PASS, exit 0
pinproof scan --config fixtures/good/pinproof.yaml

# Case 2 — deliberate SDA mismatch: firmware says GPIO18, the schematic routes
# net SDA to module pad 23 (IO21 → GPIO21)                   →  FAIL, exit 1
pinproof scan --config fixtures/mismatch_sda/pinproof.yaml

# Case 3 — firmware picks the pin from a runtime array       →  UNKNOWN, exit 0
pinproof scan --config fixtures/unsupported_expression/pinproof.yaml
```

Or all at once, with expected-vs-actual verification: `./scripts/demo.sh`

Inspect each side independently (useful when adopting a new project):

```bash
pinproof inspect-hardware --netlist fixtures/good/hardware/controller.xml --mcu-ref U1
pinproof inspect-firmware --project fixtures/good/firmware
pinproof inspect-firmware --project fixtures/good/firmware --symbol PIN_SENSOR_SDA
```

Run the test suite: `pytest`

## How a verdict is derived (the whole trick)

```
pinproof.yaml role:            { role: sensor_sda, net: SDA, firmware_symbol: PIN_SENSOR_SDA }

hardware side                                firmware side
─────────────                                ─────────────
controller.xml: net "SDA" has                include/pins.h:9  #define SDA_GPIO 18
  <node ref="U1" pin="11"/>                  include/pins.h:10 #define PIN_SENSOR_SDA SDA_GPIO
rulepack: pad "11" = IO18 = GPIO18           resolved: PIN_SENSOR_SDA → SDA_GPIO → 18

                    GPIO18  ==  GPIO18   →   PASS
```

The two derivations share nothing except the rulepack (module pad → GPIO
table, transcribed from the Espressif datasheet with provenance recorded in
[`rulepacks/esp32-s3-wroom-1-n8.yaml`](rulepacks/esp32-s3-wroom-1-n8.yaml)).
That independence is the point: the contract can't leak the answer to either side.

## What's deliberately supported (and nothing else)

- **Hardware:** one KiCad XML netlist (KiCad 8/9/10 `<export version="E">`
  format; export yours with
  `kicad-cli sch export netlist --format kicadxml -o out.xml your.kicad_sch` —
  verified against KiCad 10.0 docs/source, July 2026).
- **Module:** ESP32-S3-WROOM-1-N8 only.
- **Firmware:** PlatformIO project layout; pin declarations of exactly these
  shapes (plus deterministic alias chains between them, depth ≤ 8, cycles detected):
  ```c
  #define PIN_SENSOR_SDA 18
  #define PIN_SENSOR_SDA GPIO_NUM_18
  const int PIN_SENSOR_SDA = 18;
  constexpr int PIN_SENSOR_SDA = GPIO_NUM_18;
  ```
- Everything else — arithmetic, function calls, arrays, `#ifdef` variants,
  Kconfig — is **UNKNOWN by design**. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## Repository map

| Path | What it is |
|---|---|
| `SCOPE.md` | The Week 1 contract: verdict semantics, acceptance tests, scope tripwire |
| `src/pinproof/` | The checker: `hardware.py`, `firmware.py`, `compare.py`, `reporting.py`, `cli.py`, `models.py`, `config.py` |
| `rulepacks/` | Module pad→GPIO mapping with datasheet provenance (safety-critical data!) |
| `fixtures/` | The three demonstration projects (good / mismatch_sda / unsupported_expression) |
| `tests/` | pytest suite incl. seeded-mutation tests |
| `docs/EXPECTED_RESULTS.md` | Exactly what each fixture must print and exit |
| `docs/LIMITATIONS.md` | Honest boundaries + security notes |
| `docs/INTERVIEW_TRACKER.csv`, `docs/OUTREACH_MESSAGES.md`, `docs/COMPETITOR_TRIAL_PLAN.md` | Week 1 discovery kit |
| `.devcontainer/` | Codespaces setup (KiCad/PlatformIO optional, see `install-optional-tools.sh`) |
| `scripts/demo.sh` | Runs all three cases and checks exit codes |

## Privacy

PinProof is local-only: it reads the files you point it at and makes **no
network calls of any kind**. Nothing is uploaded, logged, or phoned home.

## Status

Week 1 prototype. Expect rough edges everywhere except the verdict semantics —
those are tested. New feature ideas go to `BACKLOG.md`, per the SCOPE.md tripwire.

License: MIT (see `LICENSE`).
