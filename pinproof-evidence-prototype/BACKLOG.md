# Backlog — ideas parked by the SCOPE.md tripwire

Every feature idea lands here as one line. Nothing here may be built during
Week 1. Re-triage only after the Week 1 acceptance tests pass and at least
five discovery interviews are logged.

- STM32 support via CubeMX `.ioc` (structured, no heuristics needed) — natural family #2
- Zephyr devicetree as a firmware source (most machine-readable option)
- Read `.kicad_sch` directly / detect stale netlist exports (timestamp check)
- GitHub Action wrapper published to the marketplace
- ESP32-S3 strapping-pin rules (rulepack already carries `strapping_gpios: [0, 3, 45, 46]`)
- I2C pull-up presence check (netlist already shows R1/R2 — needs a rule, not new parsing)
- `pinproof init` to scaffold a pinproof.yaml by suggesting nets/symbols it can see
- Kconfig/sdkconfig ingestion (ADC2-vs-WiFi class of checks)
- defusedxml + input hardening if the tool ever runs server-side
- Machine-readable SARIF output for code-scanning UIs
- Rulepack self-verification against a second data source (e.g., generated from ESP-IDF soc headers)
- Multi-pad net adjudication (currently conservative UNKNOWN)
