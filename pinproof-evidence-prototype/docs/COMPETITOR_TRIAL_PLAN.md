# Competitor Trial Plan — can anyone already catch a firmware↔schematic pin mismatch?

*(Trial availability verified July 2026 where cited; unverified items marked.)*

## Common test fixture (build once, ~1 hr, reuse everywhere)
A minimal KiCad project: ESP32-S3-WROOM-1, one I2C sensor (e.g. BME280),
net labels `SDA -> GPIO8`, `SCL -> GPIO9`. A PlatformIO firmware repo where
`i2c_master` config deliberately says **SDA = GPIO10** (schematic says GPIO8).
Also include one control bug both domains *can* see alone (missing pull-up)
to separate "generic schematic review" from "cross-domain check."
Export: netlist (.net/XML), schematic PDF, and the firmware repo.

Per product, run the SAME three questions:
1. **Ingest:** can it accept BOTH the KiCad design and the firmware source at all?
2. **Detect:** does it flag SDA firmware=GPIO10 vs schematic=GPIO8, unprompted?
3. **Evidence:** does it show file/line + net/pin provenance, or just prose?

Comparison-table columns to record for each:
`product | plan used | ingests firmware? (Y/N) | ingests KiCad? (Y/N) | flagged SDA mismatch? (Y/N/prompted-only) | false positives count | evidence quality (provenance/prose/none) | CI-able? | time to first result | cost signal`

## 1. AllSpice DRCY — https://www.allspice.io/product/drcy  (cap: 3 hr)
- **Sign up:** AllSpice Hub account; free educational tier for students exists
  (verified via [allspice.io/pricing](https://allspice.io/pricing) — as a student, request edu access). Standard DRCY
  trial pricing/length: **unverified**, check their pricing page.
- **Experiment:** push the KiCad project to an AllSpice Hub repo, run a DRCY
  design review. Then try adding the firmware repo/pins file — expectation:
  DRCY reviews schematic-vs-datasheet, not schematic-vs-firmware. Prompt it
  explicitly with the pins file attached as a comment and see if it reasons about it.
- **Record:** table columns + whether firmware is even a supported input type.

## 2. Traceformer — https://traceformer.io  (cap: 2.5 hr)
- **Sign up:** free trial then usage-based (per-review) billing (verified: [traceformer.io](https://traceformer.io/)).
  There is a KiCad export plugin ([kicad-traceformer](https://github.com/lflanagan/kicad-traceformer)).
- **Experiment:** run a standard review — it claims to catch "pin mismatches"
  and "incorrect configurations." Key question: mismatches *within* the
  schematic/datasheet, or against firmware? Try pasting the firmware pin
  config into any free-text context field and re-run.
- **Record:** table columns + per-review cost shown + determinism (run twice, same findings?).

## 3. Embedder — https://embedder.com  (cap: 2.5 hr)
- **Sign up:** free tier, no credit card (verified: [embedder.com/pricing](https://embedder.com/pricing); PRO ~$20/mo).
- **Experiment:** the closest threat — it ingests datasheets *and* schematics
  to write firmware. Open the PlatformIO project + schematic PDF, ask it to
  "review the I2C setup against the schematic." Then the harder, fairer test:
  don't ask — request an unrelated task ("add a temperature read loop") and
  see if it notices GPIO10 is wrong on its own.
- **Record:** table columns + prompted vs unprompted detection + reproducibility across 3 runs.

## 4. Flux — https://www.flux.ai  (cap: 2 hr)
- **Sign up:** two-week free trial, paid from ~$20/mo (verified: [flux.ai/p/pricing](https://www.flux.ai/p/pricing)).
- **Experiment:** import the KiCad project (or rebuild the 3-component schematic
  in Flux), ask Flux Copilot "does firmware SDA=GPIO10 match this schematic?"
  Expectation: Flux is design-side only; firmware ingestion likely impossible.
  Confirm and document that boundary precisely. (Whether KiCad import preserves
  net labels: **unverified** — record it.)
- **Record:** table columns + whether KiCad import preserved net labels.

## 5. DLR-RY/kicad_firmware_generation — https://github.com/DLR-RY/kicad_firmware_generation  (cap: 2 hr)
- **Sign up:** none; open source, public, Python, active (verified on GitHub, updated June 2026).
- **Experiment:** clone, run against the test schematic. It *generates*
  firmware pin definitions from KiCad rather than checking existing code —
  the inverse approach. Test: does its generated header make the mismatch
  obvious on diff? Does it support ESP32-S3/PlatformIO targets or need adaptation?
- **Record:** table columns + generate-vs-verify note + license + effort to adapt.

## What would falsify PinProof's opening
The opening is dead if any trial shows this outcome: a product ingests the
untouched PlatformIO repo AND the KiCad netlist, flags "SDA: firmware GPIO10 ≠
schematic GPIO8" **unprompted**, with file/line and net/pin provenance, zero
false positives on a 3-component board, reproducibly across repeated runs, and
runnable headless in CI on a free or <$25/mo tier. Embedder and Traceformer are
the ones to watch; if either does this today, PinProof is a feature they
already shipped, and the pivot question becomes determinism and CI-native
guarantees versus their LLM pipelines — or a different wedge entirely.
