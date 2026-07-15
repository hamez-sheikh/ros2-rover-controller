# Expected results — the three demonstration cases

If any of these does not match what you see, something regressed. `./scripts/demo.sh`
checks the exit codes automatically; this file explains what to look for by eye.

## Case 1 — `fixtures/good` (known-good project)

```bash
pinproof scan --config fixtures/good/pinproof.yaml
```

- **Verdicts:** `sensor_sda` PASS, `sensor_scl` PASS, `status_led` PASS
- **Exit code:** `0`
- **Evidence to spot-check:** `sensor_sda` resolves through an alias chain —
  `PIN_SENSOR_SDA -> SDA_GPIO (include/pins.h:9) -> 18 (include/pins.h:8)` —
  and the hardware side shows `net 'SDA' → U1 pad 11 (IO18) → GPIO18`.

## Case 2 — `fixtures/mismatch_sda` (deliberate SDA mismatch)

```bash
pinproof scan --config fixtures/mismatch_sda/pinproof.yaml
```

- **Verdicts:** `sensor_sda` **FAIL**, `sensor_scl` PASS, `status_led` PASS
- **Exit code:** `1` (the only nonzero-exit condition: a supported, proven mismatch)
- **Evidence required on screen (both sides, exact):**
  - firmware: `PIN_SENSOR_SDA = GPIO18`, with the chain citing `include/pins.h`
    line numbers and the extraction method (`define`);
  - hardware: `net 'SDA' → U1 pad 23 (IO21) → GPIO21`;
  - header names the rulepack id + version and the tool version.
- **The story it models:** a late schematic change moved SDA from IO18 to IO21;
  nobody updated the firmware. On real hardware this "works on the bench never"
  bug costs a debugging session or a respin; here it costs one CI run.

## Case 3 — `fixtures/unsupported_expression` (runtime pin selection)

```bash
pinproof scan --config fixtures/unsupported_expression/pinproof.yaml
```

- **Verdicts:** `sensor_sda` **UNKNOWN** (reason `unsupported-expression`),
  `sensor_scl` PASS, `status_led` PASS
- **Exit code:** `0` — UNKNOWN is loud but never CI-blocking, and never a PASS.
- **Evidence:** the report prints the offending expression
  (`SDA_PIN_OPTIONS[selectBoardRevision()]`) with its file and line, so a human
  can decide. The tool refuses to guess.

## Why case 3 matters as much as case 2

A checker that guessed here would eventually emit a confident wrong verdict —
and one confidently wrong verdict destroys the trust that makes case 2
valuable. The honesty rule (missing evidence → UNKNOWN, never PASS) is the
product's core design decision, not a limitation.
