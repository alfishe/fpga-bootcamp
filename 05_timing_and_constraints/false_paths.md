[← Section Home](README.md) · [← Project Home](../README.md)

# False Paths — When Timing Analysis Should Stay Silent

A false path is a logic path that can never cause a functional failure, regardless of propagation delay. Declaring false paths correctly is one of the highest-leverage timing constraint operations: a single well-placed `set_false_path` can clear thousands of meaningless violations, letting you focus on the paths that actually matter.

But false paths are also the **most dangerous constraint** — overly broad declarations mask real timing failures that cause silicon bugs. This article covers when to use them, how to scope them precisely, and how to verify you haven't over-applied them.

---

## What Makes a Path "False"

A path is false if **no sequence of input stimuli can cause a transition to propagate from source to destination and be captured**. In practice, this means:

| Category | Example | Why It's False |
|---|---|---|
| **Static signals** | Reset, configuration registers | Signal never changes during normal operation |
| **CDC synchronizer first stage** | 2-FF sync[0] | Metastability is expected and handled; setup/hold is meaningless |
| **Structurally unreachable** | Mode-dependent mux where one branch is disabled | Control logic prevents propagation |
| **Asynchronous interfaces** | Handshake data before request arrives | Data is guaranteed stable before capture |
| **Test/DFT logic** | Scan chain paths | Only active in test mode, not functional |

---

## set_false_path — Syntax and Scoping

```tcl
# Basic form: from any source to any destination
set_false_path -from [get_ports async_in] -to [get_cells sync_ff_reg[0]]

# Scoping options:
set_false_path -from    [get_clocks clk_a]          # All paths launched by clk_a
set_false_path -to      [get_clocks clk_b]          # All paths captured by clk_b
set_false_path -through [get_pins my_mux/S]         # All paths passing through this pin
set_false_path -rise_from [get_ports clk]            # Only rising-edge launched
set_false_path -fall_to   [get_ports clk]            # Only falling-edge captured
```

### The Precision Rule

**Always use the most specific scope possible.** Start narrow and expand only when justified.

```tcl
# BAD — over-broad: masks all paths leaving clk_a, including real timing paths
set_false_path -from [get_clocks clk_a]

# GOOD — specific: only the synchronizer first stage
set_false_path -from [get_ports async_signal_in] \
               -to   [get_cells sync_ff_reg[0]]
```

---

## Common False Path Patterns

### 1. CDC Synchronizer — First Flip-Flop Only

```tcl
# 2-FF synchronizer: false-path only from source to sync[0]
# The path from sync[1] to destination logic IS timed in the destination domain
set_false_path -from [get_ports ext_async_signal] \
               -to   [get_cells {sync_ff_reg[0]}]

# Optionally extend to sync[1] for conservative sign-off
# (sync[1] can still go metastable at very low probability)
set_false_path -from [get_ports ext_async_signal] \
               -to   [get_cells {sync_ff_reg[0] sync_ff_reg[1]}]
```

> **Do NOT** false-path the whole synchronizer chain. The register after the last sync FF must meet timing in the destination domain.

### 2. Async Reset Tree

Reset assertion (entering reset) is timing-critical. Reset de-assertion (leaving reset) has relaxed timing because the design is coming out of a known state:

```tcl
# Assertion path: must meet recovery timing (handled by set_max_delay or tool default)
# De-assertion: can be declared false path if recovery is guaranteed by other means

# Common pattern: false-path reset to all registers (ONLY if reset synchronizer exists)
set_false_path -from [get_ports rst_n] \
               -to   [get_cells *] \
               -reset_path
# The -reset_path flag tells the tool this is a reset de-assertion path
```

### 3. Static Configuration Registers

Registers that are written once at boot and never change:

```tcl
# Config register written by CPU at init, stable during operation
set_false_path -from [get_cells config_reg_*] \
               -to   [get_cells datapath_*]
```

**Verify this is actually static.** If any software path can change it during operation, this false path will mask a real bug.

### 4. Mode-Exclusive Paths

Two functional modes that never operate simultaneously:

```tcl
# Test mode vs operational mode — use XDC physically_exclusive instead:
set_clock_groups -physically_exclusive \
    -group [get_clocks func_clk] \
    -group [get_clocks test_clk]
```

If you must use `set_false_path` for mode-exclusive paths, document the mode gating clearly:

```tcl
# FAILSAFE pattern: false path conditioned on mode signal
# Only valid if MODE_SEL is statically tied and never toggles
set_false_path -from [get_cells test_mode_path_*] \
               -to   [get_cells func_capture_*]
```

---

## When NOT to Use False Paths

| Don't Do This | Use This Instead | Why |
|---|---|---|
| `set_false_path` between two async clocks | `set_clock_groups -asynchronous` | Clock groups express intent broadly; false paths should be per-path |
| `set_false_path` on a slow-changing but timed signal | `set_multicycle_path` | The path DOES need to meet timing — just over more cycles |
| `set_false_path -from [get_clocks clk_a]` globally | Scope to specific source cells | Over-broad false paths hide real violations |
| `set_false_path` on a multi-bit bus without Gray/handshake | Add synchronizer; then false-path the synchronizer | False path alone doesn't make the crossing safe |

---

## Verifying False Paths

### Check What's Covered

```tcl
# Vivado
report_exceptions -exception_type false_path

# Quartus
report_exceptions -type false_path
```

### Check What's NOT Covered

```tcl
# Ensure no unintended CDC paths remain
report_cdc -unconstrained
report_clock_interaction
```

### The Most Common Verification Mistake

Applying false paths then never checking if they were accepted:

```tcl
# After applying false paths, verify they took effect:
get_false_paths                    # List all active false paths
report_timing -from [get_ports async_in]   # Should show NO path, or a false-path annotation
```

If the tool silently ignores your false path (wrong object name, wrong hierarchy), you'll have both the false path AND the violation — but you won't know until you verify.

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| **False path on entire clock domain** | Real timing violations hidden | Use `set_clock_groups` for domain-wide exclusion; false paths only for specific paths |
| **Forgetting to false-path CDC sync[0]** | Thousands of meaningless violations on every CDC path | Add specific false paths for each synchronizer chain |
| **False path on sync[2]+ in a 2-FF chain** | Destination-domain timing violation undetected | False-path only to sync[0] or sync[1] |
| **False path on async reset without reset synchronizer** | Recovery timing violation masked | Add reset synchronizer in RTL first, then consider false path |
| **Static signal that isn't static** | Intermittent functional failure on "static" signal change | Verify with formal or review; prefer `set_multicycle_path` for slow-changing signals |

---

## Quick Reference

| Signal Type | Constraint | Scope |
|---|---|---|
| CDC 2-FF sync[0] | `set_false_path` | Source → sync[0] (or sync[1]) |
| Async reset de-assertion | `set_false_path -reset_path` | Resets → all registers (with sync) |
| Static config registers | `set_false_path` | Config regs → datapath |
| JTAG/scan chains | `set_false_path` | Scan flops → functional flops |
| Clock domain pairs (all paths) | `set_clock_groups -asynchronous` | Clock group → clock group |
| Mode-exclusive clocks | `set_clock_groups -physically_exclusive` | Clock group → clock group |

---

## Further Reading

| Article | Topic |
|---|---|
| [sdc_basics.md](sdc_basics.md) | Constraint syntax reference |
| [clock_domain_crossing.md](clock_domain_crossing.md) | CDC constraint strategy |
| [multicycle_paths.md](multicycle_paths.md) | When to use multicycle instead of false path |
| [timing_closure.md](timing_closure.md) | Using false paths in the closure loop |
| [cdc_coding.md](../04_hdl_and_synthesis/cdc_coding.md) | Synchronizer RTL patterns |
