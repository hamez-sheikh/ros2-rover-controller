# Outreach Messages

## A. Forum / Reddit post (r/embedded or forum.kicad.info)

**Title:** War stories wanted: firmware pin config that didn't match the schematic

Doing some research on cross-domain bugs — the ones where the schematic was fine
and the firmware was fine, but they disagreed (SDA/SCL swap, wrong GPIO in the
pinmap, strapping pin driven at boot, TX/RX not crossed).

If you've been bitten: **when did you catch it** (desk review, first flash,
bring-up, field?), **what did it cost** (respin? days of debugging?), and **how
do you guard against it now** (checklists, codegen, grep scripts, nothing)?

Not selling anything. I'll aggregate whatever comes in and post the summary of
failure patterns + catch stages back in this thread.

### What NOT to say
- Do not mention PinProof, a product, a waitlist, or "I'm building a tool for this."
- Do not ask "would you pay for X?" — hypothetical-demand answers are worthless.
- Do not argue with anyone who says "this is a process problem, not a tool problem" — that's data, thank them.

## B. Direct DM / email (~90 words)

Subject: 20 min on board bring-up failures?

Hi <name> — I saw your <post/talk/repo> about <specific thing>. I'm researching
how teams catch mismatches between firmware pin config and the schematic —
the bugs that survive both reviews because each side only checks its own half.

Could I get 20 minutes to hear how your last bring-up went and where the gaps
were? For context only: I've open-sourced a week-old prototype that diffs a
KiCad netlist against ESP32-S3 firmware, but I'm here to learn about your
process, not pitch. Any time next week work?

### What NOT to say
- Do not lead with the prototype or send the repo link unprompted — it's context if they ask, not the hook.
- Do not promise features, pricing, or a roadmap; you're in discovery, not pre-sales.
- Do not ask leading questions ("wouldn't it be great if CI caught this?"); ask what actually happened last time.
