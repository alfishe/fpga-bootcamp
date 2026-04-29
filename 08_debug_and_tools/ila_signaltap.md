[← 08 Debug And Tools Home](README.md) · [← Project Home](../../README.md)

# ILA vs SignalTap — On-Chip Logic Analyzers

When your FPGA design doesn't behave and simulation can't reproduce the bug, on-chip logic analyzers let you see internal signals in real-time. Xilinx ILA (Integrated Logic Analyzer) and Intel SignalTap II do the same job but with different architectures, resource costs, and workflows.

---

## Architecture Comparison

| Feature | Xilinx ILA (Vivado) | Intel SignalTap II (Quartus) |
|---|---|---|
| **IP name** | ILA (Integrated Logic Analyzer) | SignalTap II Logic Analyzer |
| **Trigger engine** | Configurable: basic (=, !=, <, >), advanced (edges, ranges, counters) | Configurable: basic, advanced (edges, ranges), state-based (12 levels) |
| **Max signals** | 1,024 per ILA core | 2,048 per instance |
| **Max sample depth** | 131,072 per ILA core | 128K per instance |
| **Clock** | Any FPGA net (no dedicated clock pin needed) | Any FPGA net |
| **Storage** | Block RAM (BRAM/URAM) | Block RAM (M10K/M20K) |
| **JTAG bandwidth** | Up to 30 MB/s (HS2/HS3 cable) | Up to 6 MB/s (USB Blaster II) |
| **Compression** | No | Yes (run-length encoding, ~2–10× effective depth) |
| **Trigger-in/out** | Yes — can route between ILAs | Yes — trigger in/out between instances |
| **Tcl control** | `run_hw_ila` / `wait_on_hw_ila` | `quartus_stp --script` |

---

## When to Use Each

| Scenario | Recommendation |
|---|---|
| Quick debug during development (GUI) | SignalTap — simpler setup, faster configure-upload cycle |
| Automated regression testing (Tcl) | ILA — better Tcl API for `wait_on_hw_ila` in CI |
| Very wide bus debugging (512+ bits) | ILA — handles 1,024 signals per core |
| Very deep trace capture (100K+ samples) | SignalTap — compression gives 2–10× effective depth |
| Multi-FPGA debugging | ILA — Xilinx HS3 can daisy-chain |
| Low-BRAM designs | Either — both consume the same BRAM per sample |

---

## Resource Cost

| Parameter | Formula |
|---|---|
| **BRAM blocks** | ceil(signal_width × sample_depth / BRAM_data_width) |
| **Logic (trigger)** | ~50–200 LUTs per trigger condition |
| **Logic (glue)** | ~100–300 LUTs for JTAG-to-ILA bridge |

**Example:** Capture 128 signals × 8,192 samples = 1,048,576 bits = 33 M10K blocks (32K each) or ~98 BRAM36 blocks (36K each). On a 110K LE Cyclone V (557 M10K), this is ~6% of BRAM.

**Practical limit:** On most designs, you can fit 1–2 ILAs at 128 signals × 8K depth before BRAM becomes scarce (aim for <10% BRAM usage for debug).

---

## SignalTap Quick Start

```
1. In Quartus: Tools → SignalTap II Logic Analyzer
2. Add nodes: drag signals from Node Finder or post-fit netlist
3. Set clock: any free-running clock in your design
4. Set trigger: basic (=, rising edge, etc.) or advanced (state machine)
5. Set sample depth: 1K–128K (compression ON by default)
6. Recompile (incremental if SignalTap-friendly constraints were used)
7. Program device → Run Analysis → trigger fires → waveform captured
```

### SignalTap-Friendly Design

For incremental recompilation (adding/removing signals without full P&R):
1. Enable "Incremental Compilation" in Quartus project settings
2. Reserve BRAM for SignalTap (Design Partitions → Reserve resources)
3. Use `(* preserve *)` or `(* keep *)` attributes on signals you'll debug
4. Don't optimize away signals during synthesis (`(* noprune *)` for wires)

---

## ILA Quick Start (Vivado)

```tcl
# Instantiate ILA in HDL or block design
ila_0: ila
  port map (
    clk    => debug_clk,
    probe0 => debug_signal_0,  -- up to 1024 bits total
    probe1 => debug_signal_1
  );

# In Vivado Tcl after programming:
run_hw_ila [get_hw_ilas -of_objects [get_hw_devices xc7z020_1]]
wait_on_hw_ila [get_hw_ilas]
display_hw_ila_data [upload_hw_ila_data [get_hw_ilas]]
```

### ILA Advanced Triggers

```tcl
# Set trigger: debug_signal_0 == 0xDEAD && debug_signal_1 rising edge
set ila [get_hw_ilas]
set trig [create_hw_probe_trigger -ila $ila]
add_hw_probe_trigger_condition $trig probe0 == 32'hDEAD
add_hw_probe_trigger_condition $trig probe1 -edge rising
set_hw_probe_trigger $ila $trig
```

---

## Best Practices

1. **Synth-preserve your debug nets** — synthesis can optimize away signals you added to ILA. Use `(* DONT_TOUCH = "TRUE" *)` or `(* KEEP = "TRUE" *)`.
2. **Use a dedicated debug clock** — sampling ILA on the same clock as the logic you're debugging. Never use a divided or gated clock.
3. **Lock BRAM placement for reproducibility** — if you remove ILA and timing changes, it's a different build. Use pblocks to lock ILA BRAM location.
4. **Tcl scripts for CI** — capture ILA/SignalTap traces in CI regression: script the trigger, upload, and save to VCD for post-processing.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Signal optimized away** | ILA shows constant 'X' or '0' | Add `(* KEEP *)` or `(* MARK_DEBUG *)` attribute |
| **ILA clock too fast** | ILA reports clock period violations | ILA max clock is fabric-limited (typically 200–300 MHz); check datasheet |
| **JTAG bandwidth bottleneck** | Upload takes minutes for 128K samples | Reduce sample count; use trigger to capture only region of interest |
| **Post-P&R signal naming changed** | Can't find signal in ILA setup | Use `(* MARK_DEBUG = "TRUE" *)` in HDL to preserve original name |
| **BRAM contention** | Design no longer fits with ILA | Reduce signal count or depth; use external logic analyzer for wide signals |

---

## References

| Source | Path |
|---|---|
| Vivado ILA IP (PG172) | Xilinx / AMD |
| Quartus SignalTap II User Guide | Intel FPGA Documentation |
| Vivado Tcl Command Reference (`run_hw_ila`) | Xilinx UG835 |
| Quartus Tcl Scripting (`quartus_stp`) | Intel FPGA Documentation |
