# The Student Founder Execution Plan

## From Incoming Freshman to (Maybe) Founding the Embedded Verification Company

*Companion to "The All-in-One Embedded Engineering Platform: A $50M Diligence Report." Written as your startup strategist, technical mentor, market researcher, and execution lead. Research updated July 2026, including a targeted evidence hunt for direct competitors to the proposed wedge. Direct and critical by request.*

**Stated assumptions (labeled per your instruction):**
- **A1:** You start university ~September 2026 and graduate ~May 2030 (4-year program). Adjust dates if different.
- **A2:** You can sustain **8–12 focused hours/week** on this alongside a full engineering course load during term, and 30–40 hrs/week during summers. If reality is 4 hrs/week, cut every "optional" item and stretch timelines ~1.5x; the plan still works.
- **A3:** You're at a university with some robotics/design-team infrastructure (most engineering schools qualify). Country unknown; funding/program specifics in §12 skew North American — analogues exist elsewhere.
- **A4:** You have no obligation to monetize during university; your downside is capped at time. This changes strategy fundamentally: **you can afford the open-source long game that funded startups can't.**
- **A5:** Your listed skills (Python, C++, ROS 2, ESP32, git) are honest beginner-to-intermediate level.

---

## 1. Executive verdict

**The platform company from the diligence report is not buildable by you today, and that is irrelevant — because the correct first move doesn't require it.** The report's own logic says the winning entry point is a thin verification layer over existing tools. A thin verification layer over existing tools is, almost uniquely in this industry, **a project one motivated student can genuinely build**: it's parsers + rules + a CLI, not a CAD editor, not a solver, not a trained model.

The verdict in five points:

1. **Build one specific thing starting now:** an open-source **hardware pre-flight checker** — working name **`boardcheck`** — that cross-checks an ESP32 firmware project against its KiCad schematic and a curated rule set, and runs in CI. Section 5 is its full spec; Section 6 is the 12-week build plan; Section 7 starts Monday.
2. **The competitive research (Section 3) confirms the specific gap is real — and closing.** No tool found in current searches ships deterministic firmware↔schematic cross-verification as a product. But three funded neighbors are circling it: Embedder (YC) generates firmware *from* schematics, AllSpice's DRCY reviews schematics with AI (no firmware input yet), and Traceformer ships LLM schematic checks including strapping-pin rules. The seam between domains is open today and will not stay open for four years — which is fine, because your plan (Section 8) treats the tool as an evidence-and-credibility engine with quarterly kill gates, not a race you must win.
3. **Treat the next four years as a funnel with kill gates, not a countdown to a predetermined company.** You listed five acceptable graduation outcomes; all five are covered by the same plan. The tool + interviews + internships generate the evidence that picks the branch. Explicit kill criteria are in Section 13 — hold yourself to them.
4. **The most probable outcome, stated honestly:** the tool becomes a respected niche open-source project with hundreds-to-thousands of users, you graduate as a top-1% embedded-tools engineer with a network into Quilter/AllSpice/Antmicro-class companies, and *that* — not a freshman incorporation — is the launching pad. Venture-scale is the tail scenario and requires the Section 13 gates to pass. Do not incorporate anything for at least 18 months.
5. **Your single biggest personal risk is not competition; it's scope creep.** Every instinct that produced "all-in-one platform, 60/30/10" will keep whispering "add a GUI, add simulation, support Altium." The plan below is deliberately narrow. Narrow is the strategy.

---

## 2. The exact startup you should pursue

### 2.1 The decision

**Primary direction: `boardcheck` — a firmware-to-schematic consistency checker and platform-specific design linter, starting with ESP32 + KiCad, delivered as an open-source CLI and GitHub Action.**

One sentence for your README: *"Catches the board-killing mistakes ERC can't see — because it reads your firmware and your schematic together."*

### 2.2 Why this wedge beats the alternatives you listed

| Candidate first build | Verdict | Why |
|---|---|---|
| **ESP32 firmware↔schematic consistency checker** | ✅ **Chosen** | Matches your exact current skills (ESP32, Python, git); deterministic (no AI-trust problem, no API costs); genuinely unoccupied per Section 3 research; distribution channel exists (GitHub Action + KiCad/ESP32 communities); demos in 60 seconds; accretes directly into the diligence report's platform vision. |
| General KiCad project reviewer (AI) | ❌ Not first | Head-on with AllSpice AI, Flux Copilot, and every "GPT + checklist" weekend project. Your differentiation would be zero and your API bill nonzero. Becomes a *layer on top of* boardcheck later. |
| Datasheet-grounded component assistant | ❌ Not first | Thin wrapper over frontier models; SnapMagic-class companies and free chatbots already squat here; no data moat a student can build fast; hallucination liability without a verification engine underneath. |
| BOM-risk analyzer | ❌ Not first | Real pain, but Octopart/Cofactr/distributor APIs already serve it and the value is the data feed, which you don't own. Ship it later as one *rule category* inside boardcheck (part-lifecycle check) — a feature, not a company. |
| Virtual-board simulator | ❌ Not first, ✅ year-3 expansion | The most valuable long-term asset and completely out of solo-freshman range (Wokwi is years of full-time work by a world-class engineer; peripheral modeling is a grind). Renode integration is your year-3 project once boardcheck has users to feed it. |
| Robotics electrical-system checker | ❌ Not first, ✅ future vertical | The pain is real (you've lived it in this very repo) but the inputs are spreadsheets and tribal knowledge — **no machine-readable file formats to parse means no software wedge**. Revisit when boardcheck can ingest harness/system descriptions (year 3+). |

### 2.3 What v0.1 must contain — and must not

**Contains (the whole product is three moves):**

1. **Parse the hardware:** KiCad schematic/netlist (KiCad 7/8/9) → which component pins connect to which nets, which MCU pins are used for what, presence of pull-ups/decoupling on relevant nets, part numbers and footprints.
2. **Parse the firmware:** an ESP-IDF or PlatformIO/Arduino project → which GPIOs the code claims, for what function (heuristics over `#define`/`const` pin declarations + `sdkconfig` + optional explicit `pins.yaml` manifest for anything the heuristics miss).
3. **Judge:** run ~25 deterministic rules across both sides + the ESP32 pin-capability database, and emit a readable report (terminal + Markdown/HTML) with severity, explanation, and a datasheet/TRM citation for every finding. Exit nonzero on errors → it's a CI gate for free.

**The launch rule set (this specific list is your v0.1 spec):**

- *Cross-domain (the unique ones):* firmware uses a GPIO not connected on the schematic; schematic wires a function (e.g., LED, sensor) to a pin the firmware configures differently; two firmware peripherals claim one pin; firmware I²C bus on nets missing pull-up resistors; firmware UART TX/RX crossed vs. schematic labels.
- *ESP32 platform gotchas (the crowd-pleasers — each one is a famous respin story):* strapping pins (GPIO0/2/5/12/15 on classic ESP32; MTDI/GPIO12 flash-voltage trap) loaded incorrectly; input-only pins (GPIO34–39) driven as outputs or given internal-pull-up expectations; ADC2 used while Wi-Fi enabled in `sdkconfig`; flash pins (6–11) reused; EN pin missing RC delay; GPIO used that doesn't exist on the specific module variant (WROOM vs WROVER vs S3 vs C3 — parse the module part number from the schematic).
- *Electrical basics visible from the netlist:* 5V net driving a 3.3V-only input (needs a small voltage-class table for common parts); missing decoupling caps adjacent to MCU/regulator power pins; floating enable/boot pins; missing series resistor on common cases.
- *Sourcing/library sanity:* footprint name inconsistent with package field (string heuristics, e.g. part is `-QFN32` but footprint says `SOIC`); part number flagged EOL/not-stocked via one distributor API (optional, keyed).

**Must NOT contain (write this list on your wall):** no GUI, no web app, no Altium import, no autofix, no simulation, no LLM in the checking path (an optional LLM "explain this finding in context" layer is permitted — it can only rephrase deterministic findings, never create them), no STM32 until ESP32 is loved, no accounts, no cloud. **Local-only by default is a feature:** professional engineers will not upload proprietary designs to a student's server, and "your design never leaves your machine" is your trust wedge against the cloud-AI competitors.

### 2.4 Data it needs — all obtainable by one student, legally

- **ESP32 pin-capability database:** machine-generated from ESP-IDF's own headers and `soc` definitions (Apache-2.0 — reusable with attribution) + hand-curated strapping/errata facts from Espressif's public TRM and datasheets (facts aren't copyrightable; cite pages).
- **Rule corpus:** Espressif hardware-design guidelines, community folklore (forum/Reddit post-mortems), your own interviews (§9). Every interview yields rules — this is how discovery and engineering feed each other.
- **Test corpus:** 20–50 public ESP32+KiCad projects from GitHub (respect licenses; you're reading, not redistributing) + 10 deliberately-broken fixtures you author.
- **Availability data:** one distributor API key (Digi-Key/Mouser/Nexar free tiers) — optional rule category, degrade gracefully without it.

### 2.5 What can one student really implement, and what gets mocked

**Realistically implementable solo:** everything in 2.3. The netlist parse is genuinely easy (KiCad's formats are documented S-expressions with existing MIT-licensed Python parsers). The rules are `if` statements over a graph. The hard-and-mockable part is **firmware parsing**: full C semantic analysis is a compiler project — don't. Ship regex/tree-sitter heuristics for the 80% case (`#define LED_PIN 12`, `gpio_config_t` literals, common Arduino calls) plus the `pins.yaml` escape hatch, and **be loudly honest in the README about the heuristic boundary.** Precision beats recall: a false accusation kills trust; a missed bug is just v0.2's changelog.

**Success for v0.1 (measurable):** ≥25 rules with tests; runs on ≥30 real public projects without crashing; **finds ≥10 genuine, confirmed-by-maintainer issues in public projects** (you'll file them as GitHub issues — this is both validation and the best marketing you can buy for $0); ≥300 GitHub stars within 60 days of launch; ≥10 discovery interviews completed citing a real cross-domain bug. Timeline: **12 weeks part-time** (§6).

### 2.6 How it becomes a company

The evolution ladder, each rung gated by evidence (§13): boardcheck (OSS, ESP32+KiCad) → multi-family (STM32 via CubeMX `.ioc` — which is *structured*, easier than ESP32; Zephyr via devicetree — the most machine-readable of all; RP2040) → paid team layer (private-repo CI, dashboards, custom org rules, compliance report artifacts) → AI review layer grounded in the deterministic engine (now you have the trust substrate the pure-AI competitors lack) → virtual-board CI via Renode (firmware boots against a board model derived from the schematic — the diligence report's §7 orchestration, seeded by boardcheck's design graph) → the verification platform of the original report. Rung 1 is you alone. Rung 3 is where a cofounder joins. Rung 5 is where venture money makes sense and where the report's company begins.

---

## 3. What already exists (researched July 2026)

Three research agents ran ~50 web searches across product sites, funding news, GitHub, forums, and academic sources. Facts below are cited; inferences are labeled. Full source list in the appendix.

### 3.1 The direct question: does your wedge already exist?

**Verdict: no purpose-built tool — commercial or open-source — was found that deterministically cross-checks firmware pin configuration (ESP-IDF, STM32Cube `.ioc`, Zephyr devicetree, Arduino/PlatformIO) against a board netlist/schematic.** But three funded products are approaching the same seam from different sides, and each could extend into it:

| Near-neighbor | What it does today | What it does NOT do | Threat read |
|---|---|---|---|
| **Embedder** (YC-backed, embedder.com) | AI *firmware agent*: "reads your schematics alongside your datasheets so generated code already knows how the board is wired"; register-level knowledge graph, claims 500+ MCUs, hardware-in-the-loop validation | Deterministic lint/CI verification of *existing hand-written* firmware vs. netlist; it generates rather than verifies | ⚠️ **Closest conceptual neighbor.** A "verify mode" would be a natural extension for them (inference). Watch quarterly. |
| **AllSpice DRCY** (AllSpice.io, ~$24.8M raised) | AI design-review agent on their git-for-hardware hub: analyzes native Altium/OrCAD/KiCad schematics vs. datasheets — mismatched pins/footprints, swapped TX/RX, pull-up values, I²C/USB configs. Cites an aerospace customer reporting ~30% respin reduction from schematic linting | Does not ingest firmware source, `.ioc`, or devicetree (their blog mentions firmware-register mapping aspirationally — inference: not shipped) | ⚠️ Owns the *schematic-side* review workflow for enterprise. Your firmware side + open-source + local-first is the differentiation. |
| **Traceformer.io** (new; Show HN Jan 2026) | LLM schematic checker for KiCad/Altium with datasheet-cited findings — including boot/strapping pins, voltage levels, pull-ups | Firmware input; deterministic guarantees (it's LLM-based); CI-gate positioning | ⚠️ Proves the *schematic-only half* of your rule set is buildable-by-one-person and is being built. Your moat is the cross-domain half + determinism. |

Also directly relevant, from the adjacent-tooling map:

- **KiCad ERC + KiBot/kicad-cli CI**: intra-schematic electrical-type rules in CI (unconnected pins, driver conflicts) — zero datasheet semantics, zero firmware awareness. This is the baseline you extend, not competition.
- **Vendor pin tools (STM32CubeMX, TI SysConfig, NXP Pins)**: excellent *intra-firmware* pin-conflict solvers that know nothing about the actual PCB — a conflict against the real board is invisible to them. They validate half the equation each; nobody joins the halves.
- **Zephyr devicetree validation**: checks DTS against driver *bindings*, not against physical wiring — a perfectly valid devicetree can describe the wrong board.
- **DLR (German Aerospace Center) `kicad_firmware_generation`** (MIT, Jan 2026, small): generates firmware pin headers *from* KiCad schematics — correct-by-construction generation, one-directional, no rule checking. Institutional evidence the pain is real; a complement (and a collaboration target), not a competitor.
- **Wokwi / Renode CI**: simulate real firmware dynamically, but wiring comes from hand-authored `diagram.json` / `.repl` files — neither imports a netlist. The "schematic → simulation model" link remains unbuilt (your year-3 rung).
- **Flux Copilot**: can query the live netlist and pick pins within Flux-native designs — but doesn't parse external firmware repos or act as a CI gate, and requires designing *in Flux*.

### 3.2 The broader landscape (funding-verified July 2026)

Movements since the original diligence report, most consequential first:

- **Flux.ai raised $37M (Feb 2026: $27M Series B led by 8VC + a previously unannounced $10M Series A) and now claims 1.1M users / 6.4M projects** — heavily prosumer-skewed (inference). The AI-EDA bottom-up land grab is accelerating, not cooling.
- **CELUS is now white-labeled inside Siemens PADS Pro Essentials** — the first incumbent distribution deal for an AI schematic-generation startup. Incumbents will buy/embed rather than build (inference) — which is your eventual exit pattern too.
- **Memfault sold to Nordic for $120M** (closed July 2025, ~$7.2M ARR — i.e., ~17x revenue for embedded dev-infra with a data loop; a useful comp for what verification data assets are worth).
- **"Renesas 365 powered by Altium" went GA early 2026** — chip-vendor-owned "hardware-software digital thread" marketing is now real; the neutrality gap identified in the diligence report widened.
- **Cadence Allegro X AI, Siemens Xpedition AI routing, Zuken AIPR, DeepPCB (InstaDeep)** all ship incremental AI place/route; **Autodesk Fusion** ships an assistant that answers questions about schematics. None touch firmware.
- **New AI-schematic entrants keep spawning:** siliXon ($1.5M seed, May 2026, text-to-PCB), CircuitPilot, ProtoFlow (free AI schematic capture with KiCad export) — the "generate a schematic with AI" quadrant is now genuinely crowded at every price point, reinforcing that generation is the wrong wedge for you.
- **JITX** now ships a Python interface and an SI-optimized autorouter, with Honeywell/Lockheed-class users — code-first EDA is finding its (aerospace/defense) niche. **Diode** ($11.4M a16z Series A) serves Fortune-100s plus robotics/defense startups with AI design services. **Quilter** ($40M) remains layout-only. **atopile** remains small (~7 people, ~$1M revenue reported; sources conflict).
- **Wokwi** remains bootstrapped-small (no funding found) with a VS Code + GitHub Actions CI story. **Antmicro/Renode** keeps expanding (KVM-accelerated sim, Google collaborations) as a services-led open-source powerhouse — your most natural year-3 partner.
- **KiCad's 2026 community funding campaign reported <2% of its goal after a month** — the ecosystem you're building on is healthy in adoption but thin in money (inference: services/donations model has a ceiling; commercial tooling *around* KiCad has room).

### 3.3 Demand evidence for the specific wedge (cited, concrete)

- KiCad forum users explicitly requesting schematic→firmware pin-header generation ("pindefs.h from schematic," 2019 thread) — the one-directional version of your product, asked for by name.
- DLR built (and wrote a thesis around) their generator because manual pin-definition maintenance causes errors — institutional-grade validation.
- ESP32.com threads: custom boards failing to flash from GPIO2/GPIO12 strapping misuse; an ESP32-S2 board dead on arrival from a GPIO0/GPIO2 swap; ESP-IDF issue #1736: SPI MISO assigned to input-only GPIO34–39. Every one of these is a rule in your §2.3 launch set, documented as a real-world failure.
- Memfault's Interrupt blog and Embedded Artistry publish *manual* "schematic review checklists for firmware engineers" — the industry currently solves your problem with prose checklists and discipline. A checklist that popular is a product spec wearing a disguise.
- AllSpice's own marketing: ~30% respin reduction from (schematic-only) automated linting at an aerospace supplier — third-party economic evidence for the category.

### 3.4 So: unnecessary, validated, or partnership?

- **Does anything make the startup unnecessary?** Not today. The deterministic cross-domain checker does not exist (§3.1). But note honestly: the *combination* of AllSpice DRCY (schematic AI review), Embedder (schematic-aware firmware generation), and vendor pin tools brackets your territory on three sides. The gap is real and *closing* — this strengthens the case for starting now and for the open-source speed strategy, and weakens any plan that waits two years to launch.
- **What validates you:** Traceformer (one person shipping schematic checks and getting HN traction), DLR's tool, the Memfault/Embedded Artistry checklists, AllSpice's respin-reduction claim, and the forum failure archaeology.
- **Partnership opportunities:** Antmicro/Renode (year-3 simulation rung), DLR's generator (complementary — generation + verification), KiCad ecosystem (KiBot integration; their funding gap makes them partner-hungry), Wokwi (netlist→diagram.json bridge would serve both), distributor APIs (self-serve), and eventually Espressif devrel (your rules reduce their support load).

---

## 4. The remaining market opening

- **The poorly-solved problem, stated exactly:** *no automated gate verifies that the firmware and the physical board agree with each other and with the silicon's documented constraints, before the board is manufactured.* Schematic tools check schematics (ERC, now DRCY/Traceformer); firmware tools check firmware against *itself* (CubeMX, SysConfig, devicetree bindings); nothing checks the marriage — and the marriage is where the §3.3 failure stories live.
- **Who feels it most:** small embedded teams (2–15 engineers) where the same people span both domains with no dedicated review function — funded hardware startups, consultancies, and advanced student/OSHW teams. Enterprise feels it too but buries it under process.
- **Who pays:** consultancies and SMB hardware startups (per the diligence report's beachhead analysis) — via team CI subscriptions, once the free tier has proven itself on their public/side projects.
- **Why hasn't it been solved?** Structural, not technical: EDA companies have no firmware-parsing DNA and firmware-tool vendors have no netlist DNA (the org-chart gap); the deterministic version requires unglamorous curation (pin databases, rule folklore) that doesn't demo as well as generative AI, so 2021–26 capital flowed to generation instead (inference, but strongly supported by §3.2's funding map); and the buyers are fragmented SMBs the incumbents don't chase.
- **Gap type:** primarily a **data + integration** gap (pin DBs, rule corpus, parsers) with a **distribution** component (must live in git/CI where firmware engineers already are). Not deep-tech, not legal.
- **Could a big company copy it quickly?** The rules, yes; the position, less easily. Altium/Cadence copying it helps only their captive ecosystems; AllSpice copying it is the real risk (K3 in §13) — your defenses are speed, open-source community gravity (they're enterprise SaaS), local-first trust, and going deeper on firmware parsing than a schematic-first company will prioritize.
- **The moat that can grow:** the curated pin/errata/rule database with citations; the opt-in telemetry of which rules fire in the wild (a failure-mode dataset nobody else can assemble); CI workflow lock-in; and eventually the netlist→virtual-board bridge (§3.1 shows both Wokwi and Renode lack it — whoever builds it owns the connection between the design world and the simulation world).
- **Venture-scale or small business?** As a linter: a good small business (§12's Scenario 2, realistically $0.4–3M ARR territory at maturity). Venture-scale only via the evolution ladder (§2.6) into verification-platform territory — which is exactly the diligence report's thesis, entered through a defensible side door. Both outcomes are acceptable per your own five-outcome frame; the gates in §12–13 decide.
- **Is robotics a good initial vertical?** As a *community and corpus*, yes (you're in it; teams are reachable; failure tolerance for new tools is high). As a *product vertical*, not yet — robotics electrical-system design lacks machine-readable inputs (§2.2). Recommendation: robotics teams as early adopters of the generic tool, robotics-specific features only after the harness/system-description problem has a parseable format (or you define one — a year-3+ option).
- **Start with which audience?** Sequence: open-source/ESP32 community (distribution + corpus) → student teams (network + CI habit) → consultancies/SMB professionals (revenue). Not enterprises (sales cycle you can't run from a dorm), not pure students (no money), not professionals-first (no trust yet).

**Primary recommendation:** the §2 wedge, unchanged by the research — the research narrowed its window but confirmed its existence. **Backup wedges** (pre-committed in §13): STM32/Zephyr professional-first variant; Renode-based virtual-board CI with netlist import.

---

## 5. Your first prototype: full technical specification

### 5.1 User workflow

```
$ pip install boardcheck        # or: uses in GitHub Actions via boardcheck-action
$ cd my-esp32-project/
$ boardcheck run --schematic hw/board.kicad_sch --firmware fw/
  ✔ Parsed 214 nets, 87 components (ESP32-WROOM-32E detected: U1)
  ✔ Parsed firmware: 14 GPIO claims (11 from source, 3 from pins.yaml)
  ✖ ERROR   GPIO12 (strapping, flash-voltage) tied high via R7 10k — device may
            fail to boot. [ESP32 datasheet §2.4; TRM strapping table]
  ✖ ERROR   Firmware configures GPIO34 as OUTPUT (motor_en, main.c:41) but
            GPIO34 is input-only.
  ⚠ WARN    I2C bus on GPIO21/22 (imu driver) — no pull-ups found on nets
            SDA/SCL.
  ⚠ WARN    U3 (MPU-6050) footprint field says QFN-24 but symbol package
            field says LGA-24.
  ℹ INFO    2 of 6 BOM parts not checked (no distributor API key).
  Result: 2 errors, 2 warnings → exit code 1
```

That terminal transcript **is** the product. Everything else is packaging.

### 5.2 Architecture (student-buildable, deliberately boring)

```
 KiCad files ─→ [hw parser] ─┐
                             ├─→ Design Graph (in-memory + JSON dump) ─→ [rule engine] ─→ findings ─→ [reporters]
 firmware  ──→ [fw parser] ──┘         ↑                                      ↑
 pins.yaml ──→ [manifest] ────────────┘                    [pin DB: ESP32 SoC data] [part DB: SQLite cache]
```

- **Language:** Python 3.12+. (Yes, the diligence report said Rust for the *platform*. You are not building the platform; you are building a parser+rules CLI where iteration speed and library availability dominate, and where every potential contributor in the KiCad world already writes Python. Rewrite the hot core later if it ever matters.)
- **Hardware parser:** `kiutils` (MIT) or `kicad-cli` netlist export + `sexpdata` for raw S-expressions. Model: `Component(ref, value, footprint, fields)`, `Net(name, [Pin])`, plus derived views (`mcu_pins`, `pullups_on(net)`, `voltage_class(net)` heuristics from net names/regulator outputs).
- **Firmware parser:** three tiers, in order of trust — (1) `pins.yaml` explicit manifest (always wins), (2) structured configs: PlatformIO `platformio.ini`, ESP-IDF `sdkconfig` (Kconfig format — trivially parseable; gives you Wi-Fi/ADC2 flags, flash mode, console pins), (3) heuristic source scan via `tree-sitter-c`/`tree-sitter-cpp` (or regex to start): `#define`/`constexpr` pin names matching `(.*_)?(PIN|GPIO|IO)`, `gpio_config_t` initializers, common Arduino/ESP-IDF calls (`pinMode`, `gpio_set_direction`, `ledcAttachPin`, `Wire.begin(sda, scl)`, `i2c_param_config`). Report the *provenance and confidence* of every claim.
- **Pin database:** generated script scrapes ESP-IDF `components/soc/<chip>/` (Apache-2.0) into `soc/esp32*.json`: per-GPIO capabilities (input-only, ADC1/2 channel, touch, strapping role, default pull state, flash-reserved), per-module variant availability. Hand-curated overlay file for datasheet facts with citation strings.
- **Rule engine:** each rule = a Python class with `id`, `severity`, `applies_to`, `check(graph) -> [Finding]`, plus a YAML front-matter doc (description, rationale, citation, false-positive notes). Rules discoverable via entry points → community rule plugins later. `# boardcheck: ignore RULE-ID` inline suppressions from day one (nothing kills a linter faster than unsuppressible false positives).
- **Storage:** none required locally beyond a SQLite cache for distributor lookups. No accounts, no telemetry beyond opt-in anonymous rule-hit counts (ask at first run; this data is your future goldmine — which rules fire in the wild = which pains are real).
- **AI/RAG components in v0.1:** **none in the decision path.** Optional `boardcheck explain <finding-id>` calls any LLM API with the finding + graph context to produce a longer teaching explanation — clearly labeled, never gating CI. RAG over datasheets is a v1.0+ feature after the deterministic core has users.
- **Reporters:** rich terminal, Markdown (for PR comments), JSON (for tooling), single-file HTML. GitHub Action wrapper posts the Markdown as a PR comment.
- **Test strategy:** golden-file tests — `tests/fixtures/<case>/` each containing a minimal KiCad project + firmware + `expected_findings.json`; plus a `corpus/` runner executing against 30+ real cloned repos in CI, asserting no crashes and tracking finding drift. Every real-world bug you find becomes a fixture. Target: every rule has ≥1 positive and ≥2 negative (false-positive-trap) fixtures.
- **Deployment:** PyPI package + prebuilt GitHub Action + Dockerfile. Versioned rule IDs so CI configs stay stable.
- **Privacy:** local-only execution; explicit statement in README; distributor API calls send part numbers only (document this — even part numbers are sensitive to some teams; provide `--offline`).
- **License:** MIT or Apache-2.0 for the tool (maximum adoption; your moat is momentum and data, not code secrecy). Keep the curated rule *content* in-repo under the same license — closed rules would kill contribution, and contributed rules are the flywheel.
- **Honest limitations to document:** heuristic firmware parsing (mitigated by pins.yaml); netlist-level only (no layout/DRC — KiCad already does that); ESP32-family only; voltage-class checks depend on a small curated part table and will have gaps; footprint check is string heuristics, not geometry.

### 5.3 Explicit integration decisions you asked about

| Integrate? | Verdict for v0.1 |
|---|---|
| KiCad formats / Python tooling | ✅ Core dependency (kiutils / kicad-cli). Don't write your own S-expr grammar beyond what's needed. |
| ESP-IDF configs (`sdkconfig`, Kconfig) | ✅ Yes — cheap, structured, unlocks the ADC2/Wi-Fi and flash-pin rules. |
| PlatformIO | ✅ Parse `platformio.ini` (board id → module variant, framework). Deep plugin later. |
| STM32CubeMX `.ioc` | ⏳ v0.3 — it's an INI-style gift (explicit pin→function map, no heuristics needed). First expansion family. |
| Zephyr devicetree | ⏳ v0.4+ — most machine-readable firmware pin source in existence; save it for when you want the professional audience. |
| Renode / QEMU | ❌ Not in the linter. Year-3 expansion (virtual-board CI). |
| ngspice | ❌ No simulation in v0.x. |
| Distributor APIs (Digi-Key/Mouser/Nexar) | ✅ One, optional, cached, degrade gracefully. |
| Manufacturer datasheets | ✅ As curated facts with citations in the pin DB — not as bundled PDFs (see §11). |
| RAG / LLM | ⚠️ Explain-only layer, off the decision path, v0.2+. |
| Static analysis / deterministic rules | ✅ This IS the product. |

---

## 6. The 8–12 week build plan

Assumes ~15–25 hrs/week (summer before university — your best uninterrupted block for the next four years; spend it here, not on a fifth ESP32 hobby project).

| Week | Build | Exit criterion |
|---|---|---|
| 1 | Corpus + formats: clone 20 public ESP32+KiCad repos; export netlists with `kicad-cli`; read them raw; write a 1-page data-model sketch. Also: skim kiutils, sexpdata, tree-sitter-c docs. | You can explain, on paper, how a pull-up on SDA appears in a netlist. |
| 2 | Hardware parser → Design Graph: components, nets, pins, MCU detection (match `ESP32-*` in part fields), pull-up/decoupling detection helpers. | `boardcheck graph board.kicad_sch` dumps correct JSON for 5 corpus boards. |
| 3 | ESP32 pin DB generator from ESP-IDF `soc/` + curated strapping/errata overlay with citations. | JSON DBs for ESP32, S3, C3 pass spot-checks against datasheet. |
| 4 | Rule engine skeleton + first 5 hardware-only rules (strapping ×3, input-only, flash pins) + terminal reporter. | Finds a real issue in ≥1 corpus board. Screenshot it. That screenshot is your founding artifact. |
| 5 | Firmware parser tier 1+2 (`pins.yaml`, `sdkconfig`, `platformio.ini`) + first cross-domain rule (firmware pin not connected / conflict). | End-to-end run on your own past ESP32 project catches a seeded bug. |
| 6 | Firmware tier 3 (heuristic source scan) + 8 more rules (I²C pull-ups, ADC2/Wi-Fi, output-on-input-only, UART cross, voltage-class v1) + suppression comments. | 15+ rules; false-positive fixtures pass. |
| 7 | **The proof campaign:** run against 30+ public repos; manually verify every finding; file polite, detailed GitHub issues on genuine ones ("boardcheck flagged X; datasheet §Y says Z"). | ≥5 maintainer-confirmed real bugs. Save every reply — this is your validation evidence AND your launch content. |
| 8 | GitHub Action + Markdown/JSON/HTML reporters + PyPI packaging + docs site (mkdocs). | A stranger can go zero→CI-gate in 10 minutes. Test on a friend. |
| 9 | Polish: README with 60-second GIF, rule catalog page (each rule = its own linkable doc — SEO), `pins.yaml` spec, contribution guide. Pick the real name (check trademark/domain — see §11). | Launch-ready repo. |
| 10 | **Launch:** Show HN, r/esp32, r/PrintedCircuitBoard, r/embedded, KiCad forum, ESP32.com, relevant Discords. Post the proof campaign write-up: *"I scanned 100 open-source ESP32 boards; here's what's silently broken."* | ≥200 stars or ≥3 substantive "I need this for X" threads (either validates). |
| 11 | Triage feedback; fix the top false-positive sources; **start interviews (§9) from inbound** — everyone who stars/comments is a warm lead. | 10 interviews booked. |
| 12 | v0.2: top 3 community requests + telemetry opt-in + STM32 `.ioc` spike (proves multi-family architecture). Write retro against §13 gates. | Honest go/adjust/kill memo to yourself. |

---

## 7. What to do this week (7 days × ≤2–3 hrs)

**Day 1 — See the data.** Install KiCad 9. Open two example projects (KiCad's own demos + one downloaded ESP32 board, e.g. any popular open ESP32 dev board repo). Run `kicad-cli sch export netlist`. Read the output file top to bottom in a text editor. Skim the kiutils README. *Output: notes file mapping "thing on schematic" → "thing in netlist text."*

**Day 2 — First parse.** Write ~40 lines of Python (sexpdata or kiutils) printing every component ref + every net + attached pins from that netlist. *Output: `parse_netlist.py` committed to a new private repo.*

**Day 3 — Build the corpus.** Find 10 GitHub repos containing BOTH a KiCad ESP32 board and firmware (search: `esp32 kicad`, filter by recent activity). Clone into `corpus/`, record licenses in a spreadsheet. Skim how each declares pins in firmware — tally the patterns you see (`#define`? `constexpr`? Kconfig?). *Output: corpus + pattern tally (this tally decides your parser tiers' priority).*

**Day 4 — Become the strapping-pin expert.** Read the ESP32 datasheet §strapping-pins and Espressif's hardware design guidelines GPIO sections. Hand-write the rule table: pin, condition, failure mode, citation. Manually audit 3 corpus boards against it. *Output: `rules/strapping.md`. If you find a real violation today — you probably will — you've validated the idea in week zero.*

**Day 5 — Rule #1 runs.** Code the GPIO12/MTDI strapping rule end-to-end: parse netlist → detect ESP32 → check pull-up on GPIO12 → print finding with citation. Run on all 10 corpus boards. *Output: first automated finding (screenshot it).*

**Day 6 — First contact.** Post ONE question (not a pitch) in r/embedded or the KiCad forum: "What's the most expensive board respin you've had, and what caused it?" Separately DM/email 3 people (an ESP32 open-source maintainer, a local hardware engineer, a senior from a university design team) asking for a 20-minute chat about how they review boards before fab. Use the outreach template in §9. *Output: 3 messages sent, 1 thread live.*

**Day 7 — Ship something visible.** Make the repo public (even at one rule), write an honest README ("early, one rule, here's the roadmap"), record a 60-second terminal demo GIF. Send it to the 3 people from Day 6. *Output: a public artifact with a real check. You are now, verifiably, building.*

---

## 8. The four-year university roadmap

Format per stage: **Essential** (do these or the plan breaks) vs *Optional* (do if bandwidth allows). Course names are generic — map to your university's catalog.

### Summer before first year (now → ~Sep 2026)
- **Essential:** the §6 twelve-week build, launched. Interviews started. That's the whole summer; it's enough.
- *Optional:* skim *The Mom Test* (Fitzpatrick) before interviewing; learn basic soldering/scope skills if weak.
- **Milestone:** public tool, ≥200 stars or equivalent signal, 10 interviews, go/adjust memo.

### First year (2026–27)
- **Skills (essential):** C fundamentals properly (not Arduino-C++ — pointers, memory, linkers); git beyond basics; how to read a datasheet cover-to-cover.
- **Courses that matter:** intro programming (trivial for you — use the spare cycles), digital logic, calculus/linear algebra (matters for controls/simulation later). Circuits usually comes year 2.
- **Do (essential):** join ONE hardware-heavy student team (FSAE electric, rocketry avionics, RoboMaster, solar car, URC rover) as *electrical/firmware* member, not software — you need schematic scar tissue and it's your cofounder hunting ground. Maintain boardcheck ~4 hrs/wk (issues, one minor release/term). Complete 25 total interviews by spring.
- *Optional:* KiCad-org Google Summer of Code application in spring (huge credibility; KiCad regularly participates — verify current-year orgs); university entrepreneurship club (for the network, not the pitch competitions yet).
- **Milestone:** 500+ users-ish (stars/downloads), your team's board passes through boardcheck, 25 interviews synthesized, you've personally designed ≥1 PCB that got fabbed.

### First summer (2027)
- **Essential (choose one, in order of preference):** (1) GSoC with KiCad/Zephyr/an embedded org — paid, prestigious, puts you inside the ecosystem whose users you want; (2) internship at a hardware startup or design consultancy (any size — you want respin stories firsthand); (3) if neither: full-time on boardcheck v1.0 = STM32 `.ioc` support + the paid-tier experiment (see §12).
- **Milestone:** multi-family support shipped OR ecosystem insider status begun; 40 cumulative interviews.

### Second year (2027–28)
- **Skills:** embedded systems course (RTOS, interrupts, buses — take the hardest version available), circuits I/II, signals & systems. Learn Rust on the side *only if* the tool's performance/architecture demands it (probably not yet).
- **Do (essential):** electrical lead (or firmware lead) on your student team; boardcheck becomes the team's CI (then evangelize to 5 other universities' teams — student teams talk to each other; this is your beachhead network from §12 of the diligence report). Approach one professor whose lab touches embedded/CPS/verification — offer boardcheck as infrastructure for their projects; a lab affiliation gets you equipment, credibility, and possibly funded hours.
- *Optional:* university startup competition IF you have paying-user evidence to present (otherwise skip — pitch competitions without customers are theater); publish 2–3 technical blog posts (the "N boards scanned" genre compounds).
- **Milestone:** 2,000+ users, 3+ external student teams in CI, first "would you pay?" conversations with consultancies from your interview network.

### Second summer (2028)
- **Essential:** the strategic internship — target, in order: **Quilter, AllSpice, Antmicro, Wokwi (if hiring), Espressif/Nordic/ST developer-tooling teams, or an EDA group at Cadence/Siemens/Altium.** You are doing paid reconnaissance: how these companies build, sell, and where they're blind. (Apply in fall 2027; these are small companies — a student who *ships a known tool in their space* gets interviews that GPAs don't.)
- *Optional:* if the tool has real traction (see §13 gates), consider ZFellows/Neo-style micro-programs instead of interning.
- **Milestone:** industry insider knowledge + a mentor/advisor relationship + a sharpened thesis on the gap.

### Third year (2028–29) — the decision year
- **Skills:** controls, computer architecture, and (if offered) compilers — compilers is the single most differentiating course for this company's future (parsers, IRs, semantic analysis = boardcheck's core).
- **Do (essential):** decide the branch per §13 evidence. Branch A (traction): incorporate, apply Neo Scholars/ZFellows/university accelerator, recruit the cofounder you've been working beside for two years, ship the paid tier for real. Branch B (no traction, thesis alive): keep tool in maintenance, optimize for the post-grad job at the acquirer-shaped company. Branch C (thesis dead per kill criteria): archive gracefully, write the public post-mortem (post-mortems build more reputation than zombie projects), pick the next thing with your now-excellent judgment.
- **Milestone:** an explicit written branch decision with evidence attached.

### Third-year summer / co-op (2029)
- Branch A: full-time on the company; raise the angel/pre-seed round ($100–500k from the operators you've met) if and only if paying teams exist. Branch B: second strategic internship or co-op at the top target company, negotiate return offer.

### Fourth year (2029–30)
- **Essential:** capstone/thesis aligned with the mission regardless of branch (e.g., "firmware-to-hardware interface verification" or "board-level digital-twin generation from netlists" — with the professor from year 2). This converts degree-hours into company-hours legitimately (mind IP policy — §11).
- Branch A: YC/accelerator application with real metrics; graduate into the company. Branch B: convert the return offer; set a personal 2-year learning contract ("I leave with: EDA internals knowledge, 3 potential cofounders, a customer map").
- **Milestone:** graduation with one of your five acceptable outcomes *explicitly achieved and documented* — not by accident, by audit.

### First six months post-graduation
- Branch A: full-time, first hire, seed conversations at >$25k MRR or strong design-partner pull. Branch B: execute the learning contract at the employer; keep boardcheck alive nights-and-weekends as the option premium; found in 2031–32 with scar tissue, savings, and a network — exactly the "join Quilter/Diode, found in 2028 with scar tissue" logic from the diligence report, shifted to your timeline. **Both branches are wins. Say that out loud whenever the comparison-to-dropout-founders demon visits.**

---

## 9. Customer-discovery plan

**Prime directive: you are investigating engineering failures, not promoting a product.** Read *The Mom Test*. Never demo in the first meeting unless begged.

### The first 30 conversations (roles, not names)

| # | Who | Why | Where to find |
|---|---|---|---|
| 1–6 | EEs at hardware/design consultancies (2–50 ppl) | The diligence report's beachhead; respins hit their invoices directly | LinkedIn search "hardware design consultancy" + your metro; KiCad Services partner lists; local PCB meetups |
| 7–12 | Firmware engineers at funded hardware startups (IoT, robotics, devices) | The cross-domain bug lands on them; they adopt CI tools personally | LinkedIn/AngelList; YC startup directories (hardware filter); warm intros from professors/alumni |
| 13–17 | Maintainers of popular open-source boards/firmware (ESP32 projects, badge makers, OSHW) | Reachable, talkative, your launch audience | GitHub (you already have the corpus), Hackaday.io, Discords |
| 18–21 | Electrical leads of university design teams (other schools) | Peer access, high bug rates, future funnel | Team websites/Instagram; competition Discords/paddocks |
| 22–24 | Freelance embedded engineers | See many clients' workflows = pattern detectors | Upwork/Toptal profiles, r/embedded flair, embedded.fm community |
| 25–27 | Application/support engineers at fabs & assemblers (JLC/PCBWay/Aisler/local CM) | They see EVERYONE's mistakes at scale — the single densest source of failure data | LinkedIn; sales-inquiry channels (they answer!) |
| 28–30 | Senior EEs at mid-size product companies | Calibrate how the pain changes with process maturity | Alumni network, IEEE student-branch events, local chapter talks |

### Outreach message (short version — adapt, don't lengthen)

> Subject: 20 min on board bring-up failures?
> Hi ___, I'm an engineering student researching how teams catch board mistakes before fab — specifically bugs that live between the schematic and the firmware. I'm interviewing engineers about real failure stories (not selling anything; I'm building an open-source checker and want to know if I'm solving a fake problem). Could I get 20 minutes this week? Happy to share what I learn across all interviews.

(The "I'll share the aggregated findings" offer converts surprisingly well — engineers want the data.)

### Ten questions

1. Walk me through the last board revision that was caused by a mistake rather than a spec change. What exactly was wrong?
2. What did that revision cost — fab, assembly, and calendar time?
3. How was the mistake eventually found? Who found it, and at what stage?
4. What's your review process before sending a board out? Who reviews, with what checklist, for how long?
5. Has firmware ever "blamed" hardware or vice versa on your team? Tell me about the worst one.
6. What do you currently run automatically — ERC, DRC, anything in CI? What do those checks miss?
7. Have you ever written a script or checklist of your own to catch a specific class of mistake? (⭐ If yes: gold. People who half-built your product are your best evidence and best future users.)
8. When you bring up a new MCU family, what bites you first?
9. What design data would you never upload to a cloud tool, and why?
10. Who else should I talk to who's been burned worse than you?

### What NOT to say
Don't pitch features; don't ask "would you use a tool that…" (hypothetical yes = worthless); don't ask "would you pay" in interview #1 (ask what they *currently spend* on reviews/respins instead); don't defend the idea when someone dismisses it — dig into *why*; don't mention AI (it derails into opinions); don't let them design your product ("what features would you want" is a trap — collect problems, not feature requests).

### Evidence thresholds
- **Validates:** ≥8 of 30 tell an unprompted cross-domain failure story with a cost attached; ≥3 have hand-rolled partial checkers; fab AEs confirm recurring mistake classes matching your rules; interviewees ask to be notified when the tool supports their stack.
- **Invalidates:** stories are overwhelmingly layout/EMC/mechanical (outside your wedge); teams say ERC + human review catches pin-level issues reliably and the data supports them; nobody recalls a firmware↔schematic bug reaching fab; universal refusal to add any CI step for hardware.
- **Storage & analysis:** one spreadsheet/Notion DB — row per interview: role, org type, failure story (verbatim quotes!), cost, detection stage, current process, tools, quotable lines, rule-idea, referrals. Tag failure stories by category; monthly rollup: which rule categories map to the most real-world cost. This artifact later becomes your seed-deck evidence page and your rule-prioritization backlog simultaneously.

---

## 10. Founding team and recruiting plan

### 10.1 The honest read on your role
You are not yet the CTO of a verification platform, and pretending otherwise repels the people you need. Your realistic trajectory: **founding engineer of the wedge → product-founder (CEO-track) of the company**, on the strength of (a) having personally built the thing users adopted, (b) owning the customer-failure dataset from 100+ interviews, and (c) four years of visible, compounding public work. The founder who *wrote the tool and talked to every user* is fundable; "idea person seeking technical cofounder" is not. Every element of this plan is engineered to make you the former.

### 10.2 The eventual team (when the §13 gates pass)

- **Ideal technical cofounder:** a systems/compilers/graphics-grade engineer who can own the platform architecture as the product outgrows Python. You will meet this person in your student team, in an OS community, or at the year-2/3 internship — **the correct recruiting strategy is working beside them for a year before either of you says the word 'cofounder.'** Do not recruit from pitch events.
- **EDA/EE veteran:** *advisor first, cofounder almost never.* A 20-year Altium/Cadence veteran has a mortgage and equity-risk aversion; 0.25–1% advisory equity for monthly calls and design-review credibility is the right structure until you can pay senior salaries (post-seed). Source: the internship network, KiCon, interview standouts.
- **Simulation specialist:** needed only when the virtual-board rung begins (year 3+ of the *company*, not of university). Recruit from Antmicro's orbit, academia (your year-2 professor relationship), or Wokwi-adjacent contributors. Until then, Renode integration is engineering, not research — you can do it.
- **Advisors vs. cofounders rule:** cofounders for work that is full-time for years and existential (platform engineering, sales once revenue exists); advisors for credibility, domain review, and doors (EDA veteran, fab executive, regulated-industry EE, one famous educator/YouTuber).
- **When to start recruiting:** cofounder conversations begin when the tool has ~1,000+ real users or a first paying pilot (a person of quality won't jump for less, and you shouldn't dilute for less). Senior/experienced hires: only post-funding. **What you must have before asking anyone experienced to bet on you:** live users, retention data, 3+ documented "this caught a real bug" stories, and a written thesis they can attack.

### 10.3 Should you work at a company first?
Per the diligence report and unchanged by anything found since: **the default answer is yes — unless the traction gates in §13 fire early.** The plan already encodes this: strategic internships (Antmicro/Quilter/AllSpice/Nordic/Cadence-class) in summers 2 and 3 give you 70% of the "work there first" benefit without surrendering the four-year compounding of the tool. The full-time-job-first branch (Branch B) is not the failure mode; for most people in your position it is the *modal correct path*, and it converts to founding in 2031–32 with dramatically better odds. Hold both branches without ego; let the §13 evidence choose.

---

## 11. Legal and partnership overview

*(General information, not legal advice — this section summarizes and extends the diligence report's §5 for your specific situation; engage a real startup/IP lawyer before incorporation, fundraising, or any paid product.)*

- **Supporting ESP32/Arduino/RPi/STM32/Nordic/TI/NXP/Microchip:** no permission required. Interoperability — reading public datasheets, parsing project files, generating code for a platform — is lawful and vendor-desired. Chip vendors *want* tools that catch design-in mistakes.
- **Trademarks — compatibility vs. logos:** saying "supports ESP32 and KiCad projects" in plain text = nominative fair use (allowed; add a trademark-ownership disclaimer; never imply endorsement). Using the Espressif/Arduino/KiCad *logos*, or a name containing their marks = requires permission. Name your tool something original; check the name against USPTO/EUIPO databases and domain availability before launch week (§6 week 9).
- **Vendor SDK licenses:** parsing ESP-IDF headers to *generate your own pin database* is use of Apache-2.0 code — permitted with attribution (keep the NOTICE file). STM32Cube `.ioc` files are *your users'* project files — parsing them is fine. You are not redistributing vendor SDKs at all in this design, which sidesteps nearly everything.
- **Datasheets:** facts (pin tables, electrical limits) are not copyrightable in the US; your curated pin/rule DB with citations is fine. Don't bundle or re-host the PDFs; deep-link. (EU database rights are a wrinkle — matters only if you commercialize extracted datasets in the EU; lawyer then.)
- **Component models:** manufacturer SPICE/3D models generally carry no-redistribution EULAs — irrelevant to boardcheck v0.x since you don't ship models; remember it at the simulation rung.
- **KiCad and GPL:** you're parsing KiCad's *file format* (open, documented) with MIT-licensed third-party libraries — no GPL exposure at all. If you later call `kicad-cli` as a **separate process**, that also creates no derivative-work obligation. Only *linking against or forking KiCad's source* would put your code under GPLv3. Your architecture never needs to.
- **University IP policy — the student-specific trap the diligence report didn't cover:** many universities claim rights to IP developed with "significant use of university resources," through funded research, or in some cases through coursework. **Before year 1: read your university's IP policy.** Keep boardcheck on personal hardware, personal time, personal GitHub; be deliberate before making it a funded lab project or credit-bearing work (the year-4 capstone alignment in §8 is worth doing *only after* you've confirmed your university's policy treats course projects as student-owned — most do, some don't). If you take a professor's lab funding for it, negotiate IP in writing first.
- **Open-source hygiene as a solo maintainer:** MIT/Apache-2.0 license file from day one; DCO or lightweight CLA once external contributions arrive (protects the future company's right to relicense/dual-license); don't accept large anonymous code dumps.
- **Partnerships — when they become real:** distributor API partnerships (Digi-Key/Mouser/Nexar) are self-serve from day one. Espressif/vendor devrel relationships become plausible once the tool demonstrably reduces their support burden (~year 2; a tweet from a vendor devrel is worth 1,000 stars). Fab partnerships (rule decks, co-marketing) at the paid-tier stage. **When you actually need a lawyer:** incorporation (Branch A, year 3), first CLA, first paid customer contract, first equity split conversation, any investor paperwork, or the first cease-and-desist-shaped email (unlikely, but forward it to counsel, don't answer it yourself).

---

## 12. Business model and funding path

### 12.1 Difficulty, capital, and time — realistic numbers

| Question | Honest estimate |
|---|---|
| Development difficulty of v0.1 | 4/10 for a competent student — the difficulty is discipline (scope), not algorithms |
| Time to *useful* product | 12 weeks to first-value; ~12 months to "professional would rely on it" |
| Capital required, years 0–2 | ~$0–500 (domain, API keys, a couple of test boards). Your costs are time. |
| Capital, bootstrapped niche (Branch A-lite) | $10–50k/yr (part-time contractor help, infra) — coverable by grants (§12.3) + early revenue |
| Capital, venture platform | $2–4M seed post-graduation to hire 6–8 and build the AI/sim layers (per diligence report §9) |
| Time to first revenue | Earliest sensible: month 12–18 (paid CI tier). Rushing it earlier costs more community trust than it earns cash. |
| Likely initial pricing | Free forever: OSS core, public repos. **Team tier $20–50/user/mo**: private-repo CI, org rule packs, dashboards, priority families. Consultancy/enterprise **$200–500/mo/team**: custom rules, report artifacts for design reviews, support. (Anchor: teams pay $10–20/user for lint/CI tools; you're claiming respin-prevention, so the consultancy tier can hold a premium.) |
| Realistic early customer count | 18–24 months post-launch: 10–40 paying teams ≈ $15–100k ARR if discovery validated. That's a *strong* outcome for a student-run tool — calibrate expectations to that, not to a16z-portfolio charts. |

### 12.2 The three scenarios and their gates

**Scenario 1 — student side project (default, starts now).** Cost: time. Outcome even if it never monetizes: elite skills, network, reputation, and the evidence to kill or continue honestly. *You are in this scenario until proven otherwise.*

→ **Gate to Scenario 2:** ≥1,500 genuinely active users (not stars — CI runs/downloads with retention), ≥10 unsolicited "can we pay for private-repo support?" signals, discovery threshold from §9 met. Expect to evaluate this gate around month 12–18.

**Scenario 2 — bootstrapped niche company.** Incorporate; ship the team tier; target 50–200 paying teams over 2–3 years ($50–400k ARR); fund via revenue + grants (§12.3) + possibly a small angel check from an operator in your network. A calm, profitable verification-tools business serving consultancies and SMB hardware teams is a *real and good* outcome — the "useful smaller business" you asked about exists here, and it can pay you better than a graduate job while you decide about the platform.

→ **Gate to Scenario 3:** evidence of *platform pull*, not just linter satisfaction — customers asking for multi-family coverage, AI review, simulation, org-wide dashboards; NDR >120% on the paid tier; a credible technical cofounder committed; and the market check: the AI-EDA consolidation (§3) has left the verification seam still open. If those hold: raise the $2–4M seed and execute the diligence report's roadmap from its v1 onward — you'll be entering with the two assets that report said matter most (a trusted deterministic engine + a failure-mode dataset).

**Scenario 3 — venture-backed platform company.** Only enter through the gates. Entering Scenario 3 without Scenario 2's evidence converts you from "founder with proprietary insight" into "another AI-EDA pitch," and §3 shows how crowded that pitch is.

### 12.3 Money available to you specifically (verified July 2026; details/deadlines drift — recheck each cycle)

- **Now/any time:** 1517 Fund's Medici Project ($1k no-strings prototype grants); Emergent Ventures (rolling, fast, loves concrete "zero-to-one" projects — boardcheck with traction is exactly their pattern); Z Fellows ($10k + network, no need to leave school, rolling).
- **After year 1–2 (US undergrads):** Neo Scholars ($25k equity-free + community; annual cycle, deadline was mid-June for 2026); Contrary (campus network → checks); Pear Competition (up to $100k uncapped SAFE) if your campus is in scope.
- **Open-source route:** GSoC — 2026's application window is closed; **target GSoC 2027** (orgs announced ~Feb, apply ~March; Zephyr participates under the Linux Foundation; KiCad is a recurring participant — verify the 2027 org list; FOSSi Foundation runs EDA-adjacent projects). Stipends run ~$1.5–6.6k and the credibility is worth more than the money.
- **At graduation decision point:** YC now runs 4 batches/year and offers **Early Decision for students** — you can apply in your final fall and defer to a post-graduation batch; this is purpose-built for your Branch A timing. Thiel Fellowship ($250k for the class of 2026 onward) exists but requires dropping out — given your Branch structure, only relevant if Scenario 3 gates fire *early and hard* (don't plan on it).
- **Hardware-specific:** HAX (SOSV, up to ~$550k + Newark facility) if the company ever needs physical-product depth; university accelerators (SKYDECK-class) once enrolled — check your own school's versions in week 1 on campus.

### 12.4 Why the company could fail (pre-answering §13)
Ranked: (1) **false-positive trust collapse** — the tool cries wolf, engineers uninstall, game over (this is why precision > recall is engineering law); (2) **the seam closes** — AllSpice/Altium/Cadence ship credible firmware-aware review before you have distribution (mitigation: OSS speed + the seam requires firmware-parsing DNA they lack — but watch it quarterly); (3) **adoption friction** — hardware teams won't add CI steps (discovery tests this directly; if true, kill early); (4) **the pain is episodic, not chronic** — respins hurt but happen quarterly; tools bought for episodic pain churn (mitigation: daily-value features — the pin DB, the review report in every PR); (5) **founder burnout/scope creep** — a solo student maintaining a growing OSS project through exam seasons is the quiet killer (mitigation: ruthless scope, recruit co-maintainers by year 2, and it's OK for releases to slow in term time — say so in the README).

---

## 13. Risks and kill criteria

**Standing quarterly review (put four recurring 2-hour blocks in your calendar per year — this discipline is the difference between evidence-driven and sunk-cost-driven):**

| # | Kill/pivot criterion | Check | If it fires |
|---|---|---|---|
| K1 | **Discovery fails:** after 30 interviews, <5 unprompted cross-domain failure stories with real cost | Month ~4 | Pivot wedge to backup #1 or #2 (below); the platform thesis survives, the entry point changes |
| K2 | **Nobody runs it twice:** launch spike but <20% of installers run it on a second project within 60 days | Month ~5–8 | Diagnose: false positives (fix precision) vs. no felt pain (K1 by other means → pivot) |
| K3 | **The seam closes:** a funded competitor or incumbent ships real firmware↔schematic verification with distribution (named watch list: Embedder, AllSpice/DRCY, Traceformer, Flux, plus vendor tools) | Quarterly scan | Don't compete head-on; either become the OSS standard they must interop with, or pivot vertical (robotics electrical) or become their best acquisition/hire |
| K4 | **Paid gate fails:** 1,500+ active users but 12 months of zero willingness-to-pay signals | Month ~24–30 | Freeze at Scenario 1 (great OSS project, career asset); do NOT bootstrap a company on hope |
| K5 | **Personal gate:** two consecutive terms where the project got <20 hours total | Each term | Be honest: park it publicly ("maintenance mode"), don't let it zombie — a cleanly parked project preserves reputation; a rotting one spends it |

**Backup wedges (pre-committed, so a pivot is a decision, not a crisis):**
1. **STM32-first professional version** — if discovery says the pain lives with professionals on STM32 rather than the ESP32 community: `.ioc`+Zephyr devicetree cross-check, marketed to consultancies directly. Same engine, different beachhead.
2. **Virtual-board CI (Renode-based)** — if discovery says "we catch pin bugs fine; what kills us is firmware regressions with no hardware in the loop": pivot up the stack to hardware-in-CI. Harder build, clearer budget line, adjacent to Antmicro rather than competitive with it.

---

## 14. Final recommendation

Do these, in this order, and let the gates do the deciding:

1. **This week:** the §7 seven-day plan. It ends with a public repo containing one real check. Everything else in this document is downstream of whether you actually do this step.
2. **This summer:** the §6 twelve-week build, culminating in a launch and ten interviews. Protect the summer — it's the best contiguous block you'll have until 2030.
3. **Through university:** the §8 roadmap — one hardware team, strategic internships (Antmicro-class), 100 cumulative interviews, quarterly §13 reviews. Keep the project personal-IP-clean (§11).
4. **Never during years 1–2:** incorporate, fundraise, build a GUI, add Altium support, chase AI features, or say "platform" out loud. The wedge earns the right to the platform; the platform pitch without the wedge is the crowded, funded field of §3.
5. **The mindset:** the diligence report's final line said an under-teamed correct thesis is still a zero — your version of that warning is *an under-focused student is also a zero*. But a student who ships a sharp tool, talks to a hundred wounded engineers, and audits themselves quarterly against written kill criteria will graduate holding one of your five acceptable outcomes **by construction, not by luck**. That is the whole plan. Start Monday.

---

## Appendix — Key sources (research current as of July 2026)

**The wedge and near-neighbors:** [Embedder](https://embedder.com/) · [Embedder on YC](https://www.ycombinator.com/companies/embedder) · [AllSpice DRCY](https://www.allspice.io/ai-agent) · [DRCY under the hood](https://www.allspice.io/post/under-the-hood-how-drcy-reviews-your-schematics) · [AllSpice on AI schematic review + respin-reduction claim](https://www.allspice.io/post/using-ai-in-schematic-design-reviews-what-we-learned-and-what-surprised-us) · [Traceformer](https://traceformer.io/) ([Show HN](https://news.ycombinator.com/item?id=46492601)) · [DLR kicad_firmware_generation](https://github.com/DLR-RY/kicad_firmware_generation) ([forum thread](https://forum.kicad.info/t/kicad-firmware-generation-extract-information-from-kicad-schematics-and-generate-firmware/66585)) · [kicube32](https://github.com/waynegramlich/kicube32) · [TI SysConfig](https://www.ti.com/tool/SYSCONFIG) · [Zephyr devicetree bindings](https://docs.zephyrproject.org/latest/build/dts/bindings.html) · [KiBot](https://github.com/skorokithakis/KiBot) · [Wokwi](https://wokwi.com/) · [Antmicro Visual System Designer](https://antmicro.com/blog/2023/09/build-embedded-systems-with-vsd)

**Demand evidence:** [KiCad forum: pindefs.h request](https://forum.kicad.info/t/automatically-generate-a-pindefs-h-header-file-for-include-in-firmware-project/17223) · [Hackaday.io: wrong pin assignment log](https://hackaday.io/project/19914/log/56888-wrong-pin-assignment) · [Hackaday: 312 weeks fixing a pin-rotated board](https://hackaday.com/2023/02/17/fail-of-the-week-epic-312-weeks-of-fixing-a-broken-project/) · [esp32.com: GPIO2/GPIO12 flash failures](https://www.esp32.com/viewtopic.php?t=27365) · [esp32.com: GPIO12 bootstrapping](https://esp32.com/viewtopic.php?t=3954) · [esp32.com: S2 GPIO0/GPIO2 swap](https://esp32.com/viewtopic.php?t=27954) · [ESP-IDF #1736: MISO on input-only pin](https://github.com/espressif/esp-idf/issues/1736) · [Memfault Interrupt: schematic review checklist](https://interrupt.memfault.com/blog/schematic-review-checklist) · [Embedded Artistry: schematic reviews for firmware engineers](https://embeddedartistry.com/blog/2016/07/07/schematic-reviews-for-firmware-engineers/)

**Landscape/funding:** [Flux $37M](https://www.flux.ai/p/blog/we-raised-37m-to-take-the-hard-out-of-hardware) ([SiliconANGLE](https://siliconangle.com/2026/02/27/flux-nabs-37m-automate-printed-circuit-board-development-ai/)) · [Quilter $25M Series B](https://www.businesswire.com/news/home/20251007165399/en/Quilter-Secures-$25M-Series-B-to-Eliminate-Manual-PCB-Design-with-Physics-Driven-AI) · [Diode Computers (YC)](https://www.ycombinator.com/companies/diode-computers-inc) · [AllSpice funding (Crunchbase)](https://www.crunchbase.com/organization/allspice) · [Nordic acquires Memfault ($120M)](https://www.nordicsemi.com/Nordic-news/2025/06/Nordic-Semiconductor-acquires-Memfault) · [CELUS](https://www.businesswire.com/news/home/20250513761600/en/) · [Siemens PADS Pro AI (CELUS-powered)](https://news.siemens.com/en-us/siemens-pads-pro-xpedition-ai/) · [Renesas 365 GA](https://www.renesas.com/en/about/newsroom/renesas-announces-general-availability-renesas-365) · [Cadence Allegro X AI](https://www.cadence.com/en_US/home/resources/white-papers/allegro-x-ai-for-generative-system-design-wp.html) · [Zuken AIPR](https://www.zuken.com/us/product/cr-8000/ai-pcb-design/) · [DeepPCB](https://deeppcb.ai/) · [Autodesk Fusion 2026 roadmap](https://www.autodesk.com/products/fusion-360/blog/fusion-roadmap-2026/) · [Luminovo ElectronicsGPT](https://luminovo.com/about/press/luminovo-introduces-electronicsgpt) · [Cofactr Series A](https://www.businesswire.com/news/home/20241212219735/en/) · [JITX 2025](https://blog.jitx.com/jitx-corporate-blog/whats-new-in-jitx-2025) · [atopile](https://atopile.io/) · [siliXon seed](https://www.atlaspcb.com/news/news-silixon-ai-text-to-pcb-funding-2026/) · [ProtoFlow](https://www.protoflow.ai/) · [CircuitPilot](https://circuitpilot.dev/) · [Renode/Antmicro news](https://antmicro.com/blog/2025/09/faster-renode-simulation-via-kvm) · [KiCad 2026 funding campaign](https://forum.kicad.info/t/2026-funding-campaign/66647) · [KiCad professional support](https://www.kicad.org/help/professional-support/)

**Student programs/funding:** [YC Apply](https://www.ycombinator.com/apply) · [YC Early Decision (students)](https://www.ycombinator.com/early-decision) · [Neo Scholars](https://neo.com/scholars) · [Z Fellows](https://www.zfellows.com/) · [1517 Medici Project](https://www.1517fund.com/medici) · [Emergent Ventures](https://www.mercatus.org/emergent-ventures) · [Pear Competition/Garage](https://pear.vc/programs/dorm/) · [Contrary](https://contrary.com) · [GSoC](https://summerofcode.withgoogle.com/) ([stipends](https://developers.google.com/open-source/gsoc/help/student-stipends)) · [Zephyr GSoC](https://www.zephyrproject.org/google-summer-of-code-zephyr-rtos/) · [FOSSi GSoC ideas](https://fossi-foundation.org/gsoc/gsoc26-ideas) · [Antmicro internships](https://careers.antmicro.com/internships/) · [Nordic internships](https://careers.nordicsemi.com/jobs) · [Cadence interns](https://www.cadence.com/en_US/home/company/careers/interns-and-new-grads.html) · [Siemens student programs](https://www.siemens.com/en-us/company/siemens-software-student-talent-programs/) · [University Rover Challenge](https://urc.marssociety.org/) · [FSAE](https://www.fsaeonline.com/) · [IREC 2026](https://www.esrarocket.org/2026irec) · [American Solar Challenge](https://www.americansolarchallenge.org/) · [HAX](https://hax.co)

*Licensing/legal content is general information, not legal advice. Program deadlines and funding figures drift — re-verify each application cycle.*




