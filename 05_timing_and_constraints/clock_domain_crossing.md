[← Section Home](README.md) · [← Project Home](../README.md)

# Clock Domain Crossing — The Timing Constraints View

> **This is the constraint-level companion to [cdc_coding.md](../04_hdl_and_synthesis/cdc_coding.md).** The HDL article covers what synchronizers to write in RTL. This article covers what the timing engine needs to know about those synchronizers — how to tell the tool "this path is intentionally unconstrained by setup/hold because a 2-FF synchronizer handles it."

A clock domain crossing (CDC) is any path where the source register is clocked by one clock and the destination register is clocked by another. From the STA (Static Timing Analysis) engine's perspective, CDCs are a problem: the phase relationship between two unrelated clocks is unknowable. Any attempt to compute setup/hold across domains produces meaningless results.

Your job with constraints is to:

1. **Identify** which clock-to-clock paths are CDC paths
2. **Exclude** those paths from standard setup/hold analysis
3. **Apply** targeted delay constraints (max_delay) where appropriate
4. **Verify** that no CDC path is accidentally left unconstrained

---

## The STA Problem With Cross-Domain Paths

STA computes whether data launched by one clock edge is captured correctly by another. This requires the two clocks to have a **known, fixed phase relationship**. Two unrelated oscillators have no such relationship:

```
clk_a (100 MHz, oscillator A):  ┌─┐  ┌─┐  ┌─┐  ┌─┐  ┌─┐
                                ┘ └──┘ └──┘ └──┘ └──┘ └──

clk_b (125 MHz, oscillator B):  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──
                                ┘  └──┘  └──┘  └──┘  └──┘

Phase relationship:                ?? (drifting, unknowable)
```

If the tool analyzes this as a standard setup path, it will choose an arbitrary phase alignment and report either false violations or false passes — both dangerous because they give you no actionable information about whether the synchronizer will actually work.

---

## Solution Overview — The CDC Constraint Strategy

| Synchronizer Type | Constraint Strategy | Why |
|---|---|---|
| **2-FF synchronizer** (single-bit) | `set_false_path` from source to first sync FF; optionally from source to second sync FF | First FF metastability is expected — there is no valid setup/hold to check |
| **Pulse synchronizer** (toggle) | `set_false_path` from toggle FF to sync[0]; optionally `set_max_delay` on the path | Same as 2-FF but with optional bounded delay for MTBF |
| **Gray code + 2-FF** (multi-bit counter) | `set_false_path` from counter bits to sync[0]; `set_max_delay -datapath_only` on the Gray-encoded path | False path on synchronizer; max_delay on Gray logic ensures bits arrive within one clock |
| **Async FIFO** (dual-clock BRAM) | `set_clock_groups -asynchronous` on write/read clocks; `set_false_path` on gray-to-binary conversion; `set_max_delay` on gray pointer paths | FIFO handles all CDC internally; only constrain the pointer logic |
| **Handshake / request-ack** | `set_false_path` on request and acknowledge; `set_max_delay` on the data bus relative to request | Data must be stable before request crosses; false path on handshake signals |
| **MCP with false paths** (multi-cycle path) | `set_multicycle_path` + `set_false_path` on the control signal's crossing path | Complex — see separate pattern documentation |

---

## set_clock_groups — The First Line of Defense

Tell the tool which clocks are asynchronous. This prevents the STA engine from analyzing any path between those clock groups:

```tcl
# SDC / XDC
set_clock_groups -asynchronous \
    -group [get_clocks {sys_clk clk_200m clk_50m}] \
    -group [get_clocks {eth_rx_clk eth_tx_clk}] \
    -group [get_clocks {video_pclk}] \
    -group [get_clocks {spi_sclk}]
```

**Rule:** All clocks derived from the same oscillator (via PLL/MMCM) go in the SAME group. Clocks from different oscillators go in DIFFERENT groups. Internally generated clocks from the same source clock (via `create_generated_clock`) share a group implicitly.

### XDC Extensions

Xilinx adds two more group types beyond `-asynchronous`:

```tcl
# Physically exclusive: only one clock can be active at a time (e.g., BUFGMUX)
set_clock_groups -physically_exclusive \
    -group [get_clocks clk_100m] \
    -group [get_clocks clk_125m]

# Logically exclusive: both clocks exist but are never used simultaneously
# in the same functional mode (e.g., test clock vs operational clock)
set_clock_groups -logically_exclusive \
    -group [get_clocks func_clk] \
    -group [get_clocks test_clk]
```

> **Critical:** `set_clock_groups -asynchronous` does NOT make the crossing safe. It only stops the STA engine from reporting timing violations. You STILL need the synchronizer in hardware. The constraint and the circuit must match.

---

## set_false_path — Per-Path Exclusion

When you have a specific CDC path (one synchronizer chain), use `set_false_path` instead of a blanket clock group exclusion. This gives finer granularity:

```tcl
# 2-FF synchronizer: path from source domain to first sync register
# is intentionally unconstrained because metastability is allowed here
set_false_path -from [get_ports async_signal_in] \
               -to [get_cells sync_ff_reg[0]]

# Optionally also false-path to sync_ff[1] for conservative analysis
set_false_path -from [get_ports async_signal_in] \
               -to [get_cells sync_ff_reg[1]]
```

### When to Use false_path vs clock_groups

| Scenario | Use | Why |
|---|---|---|
| **All paths between clk_a and clk_b are CDC** | `set_clock_groups -asynchronous` | Simple, broad — one line covers everything |
| **Some clk_a→clk_b paths are CDC, others have known phase** | `set_false_path` on specific paths | Keep clock groups open for real timing paths |
| **Single synchronizer chain on a specific signal** | `set_false_path -from ... -to ...` | Precise; documents which signal is async |
| **Bus with handshake where data path needs max_delay** | `set_false_path` on handshake + `set_max_delay` on data | Mixed strategy (see below) |

---

## set_max_delay — Bounding Paths You Excluded

After excluding a path from standard setup/hold, you can apply a `set_max_delay -datapath_only` to bound the combinatorial delay:

```tcl
# The Gray-encoded counter bits must all arrive at the destination
# within one destination clock cycle (for reliable sampling)
set_max_delay -from [get_cells rd_ptr_gray_reg[*]] \
              -to [get_cells rd_ptr_sync_reg[0]] \
              -datapath_only 4.0
# 4.0 ns = one destination clock period at 250 MHz
```

**`-datapath_only` is critical:** It excludes clock skew from the calculation. Since the clocks are asynchronous, skew is meaningless — you only care about the raw wire+LUT delay.

### Max Delay Values by Synchronizer Type

| Synchronizer | Typical max_delay | Rationale |
|---|---|---|
| 2-FF (single bit) | None needed | 2-FF handles any delay; no max_delay necessary |
| Gray code counter | 1 destination clock period | All bits must settle within one dst_clk cycle |
| Handshake data bus | 2 source clock periods | Data must be stable before request reaches destination |
| Async FIFO pointers | 1 destination clock period | Gray pointers must settle before sampling edge |
| MCP data path | setup multiplier × period | Already handled by `set_multicycle_path` |

---

## CDC Reporting — Verifying Your Constraints

### Vivado

```tcl
# Generate CDC report — lists all cross-clock paths
report_cdc -file cdc_report.txt

# Clock interaction matrix — see which clocks have paths between them
report_clock_interaction -file clock_interaction.txt

# Check for unsafe CDC (no synchronizer constraints)
report_cdc -details -severity critical
```

### Quartus

```tcl
# Clock domain crossing report
report_cdc -file cdc_report.txt

# List all unconstrained CDC paths
report_cdc -unconstrained -file unconstrained_cdc.txt

# CDC viewer (GUI)
# Tools → CDC Viewer
```

### Third-Party CDC Verification

| Tool | Vendor | Strength |
|---|---|---|
| **Questa CDC** | Siemens | Structural + protocol CDC analysis |
| **SpyGlass CDC** | Synopsys | Deep protocol checking (handshake, FIFO, MCP) |
| **Vivado report_cdc** | Xilinx | Free, integrated, good for structural checks |
| **Quartus CDC Advisor** | Intel | Free, integrated |

These tools do what the STA engine cannot: verify that your synchronizer topology is correct and complete. For example, SpyGlass will flag if you have a multi-bit bus crossing without Gray encoding or handshake.

---

## Per-Vendor CDC Constraint Comparison

| Operation | SDC (Intel/Lattice/Microchip) | XDC (Xilinx) |
|---|---|---|
| Async clock groups | `set_clock_groups -asynchronous` | Same + `-physically_exclusive` / `-logically_exclusive` |
| False path on first sync FF | `set_false_path -from ... -to sync_reg[0]` | Same, use `get_cells` or `get_pins` |
| Max delay (datapath only) | `set_max_delay -from ... -to ... -datapath_only` | Same |
| Gray code counter paths | `set_max_delay -datapath_only 4.0` on Gray bits | Same |
| Async FIFO | `set_clock_groups` on rd_clk/wr_clk | Same; optionally use XDC FIFO generator |
| CDC report | `report_cdc` | `report_cdc` + `report_clock_interaction` |

---

## The CDC Sign-Off Checklist

Before signing off on timing, verify every CDC:

| # | Check | How |
|---|---|---|
| 1 | Every clock input has a `create_clock` | `report_clocks` |
| 2 | Clocks from different oscillators are in different async groups | `report_clock_groups` |
| 3 | Every CDC path has EITHER a synchronizer in RTL OR is excluded via constraints | `report_cdc` |
| 4 | Every 2-FF synchronizer has `set_false_path` on the first stage | Manual review + `report_cdc` |
| 5 | Every Gray code path has `set_max_delay -datapath_only` | `report_cdc` |
| 6 | No multi-bit bus crosses without Gray, handshake, or async FIFO | CDC tools (SpyGlass/Questa) or manual review |
| 7 | Every async FIFO has rd_clk and wr_clk in different clock groups | `report_clock_interaction` |
| 8 | Pulse synchronizer toggle FF has `set_false_path` to sync[0] | Manual review |
| 9 | No `set_false_path` is overly broad (masking real timing paths) | Review `-from`/`-to` scopes |
| 10 | Static analysis tool (SpyGlass/Questa) passes without critical CDC violations | Run CDC tool |

---

## Common CDC Constraint Mistakes

| Mistake | What Happens | Fix |
|---|---|---|
| **No async clock groups** | Thousands of meaningless violations clutter the report; real violations are buried | Add `set_clock_groups -asynchronous` |
| **Forgetting max_delay on Gray code** | Gray bits have unbounded skew → counter value sampled mid-transition → FIFO overflow/underflow | `set_max_delay -datapath_only` on Gray logic |
| **set_false_path on the WHOLE synchronizer chain** | The path from sync[1] to logic is also excluded from timing → timing violation in the destination domain goes undetected | False-path only from source to sync[0] (or sync[1]) |
| **Grouping related clocks as async** | Clocks from same PLL placed in different groups → valid timing paths excluded → real violations hidden | Only group truly async clocks; all PLL outputs of same source go in same group |
| **No CDC report review before sign-off** | Undocumented CDC paths exist in the design → silicon failures | Always run `report_cdc` and verify every path |
| **Relying on clock groups alone without synchronizers** | Timing report is clean but hardware fails intermittently | Clock groups suppress analysis; synchronizers handle the physical reality |

---

## Further Reading

| Article | What It Covers |
|---|---|
| [cdc_coding.md](../04_hdl_and_synthesis/cdc_coding.md) | RTL patterns: 2-FF, pulse sync, Gray code, async FIFO, handshake, MCP, correlated signals |
| [sdc_basics.md](sdc_basics.md) | Constraint syntax reference: create_clock, clock groups, false_path, max_delay |
| [false_paths.md](false_paths.md) | Deep dive on `set_false_path` usage and safety |
| [timing_closure.md](timing_closure.md) | End-to-end timing closure methodology |
| [io_timing.md](io_timing.md) | Source-synchronous IO timing |
| Xilinx UG903 | Vivado Using Constraints — CDC section |
| Intel AN 793 | Clock Domain Crossing Design and Verification |
