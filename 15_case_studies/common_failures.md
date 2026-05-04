[← 15 Case Studies Home](README.md) · [← Project Home](../../README.md)

# Common FPGA Failures — Root Causes & Fixes

A catalog of frequently encountered FPGA failures organized by category: metastability, timing violations, power sequencing, configuration failures, clocking issues, BRAM errors, signal integrity, and resource exhaustion. Each entry includes the symptom, root cause, and resolution.

---

## Metastability

| Symptom | Root Cause | Fix |
|---|---|---|
| Intermittent data corruption across clock domains | CDC crossing without synchronizer | 2-FF synchronizer on single-bit signals; async FIFO or handshake for multi-bit |
| Random CPU hangs in SoC | Unsynchronized external input to bus register | Add 2-FF sync + edge detection before CSR |
| MTBF violations (calculated failure rate) | Synchronizer chain too short | 3-FF chain for high-MTBF requirements (aero/med) |
| FIFO output glitches | Gray-code pointer not used on async FIFO read side | Use gray-code encoding for cross-domain pointer bits |
| Multi-bit CDC corrupted | Multiple bits sampled on different clock edges | Use handshake (req/ack) or async FIFO, never multi-bit direct sync |

**Golden rule:** Any signal crossing clock domains must pass through at least 2 flip-flops in the destination domain before use. For multi-bit buses, use async FIFO or handshake — never sync individual bits independently.

### CDC Debugging Checklist

```verilog
// BAD: multi-bit CDC without gray code
always @(posedge dst_clk)
    data_out <= data_in;  // Bits may arrive at different times!

// GOOD: gray-code pointer crossing
always @(posedge dst_clk) begin
    gray_ptr_sync1 <= wr_ptr_gray;
    gray_ptr_sync2 <= gray_ptr_sync1;
end
// Only the gray-coded pointer crosses; data follows through FIFO
```

---

## Timing Violations

| Symptom | Root Cause | Fix |
|---|---|---|
| Setup time violation (negative slack) | Logic path too long between registers | Pipeline the path: insert register stage |
| Hold time violation | Clock skew > data path delay | Add delay to data path; check clock tree |
| `No routes possible` error | Congestion or over-constrained design | Reduce utilization, relax pblocks, add routing layers |
| Timing met in synth, failed in P&R | Synthesis estimate optimistic vs physical placement | Use physical-aware synthesis; check high-fanout nets |
| Negative slack on I/O paths | Missing `set_input_delay` / `set_output_delay` | Add I/O timing constraints referencing external device |
| Path from X to Y not timed | Missing `create_clock` or false path | Define clocks on all inputs; add `set_clock_groups` for async domains |
| Timing degradation at temperature | Hot junction slows transistors | Verify timing at worst-case corner (85°C junction) |

### Timing Closure Debug Flow

```
1. Run STA (Vivado: report_timing; Quartus: TimeQuest)
2. Sort paths by slack (most negative first)
3. Identify the path type:
   a. Logic-heavy path → pipeline or restructure
   b. Routing-heavy path → floorplan or add REG_SLICE
   c. I/O path → add set_input/output_delay constraints
   d. Cross-clock path → add set_clock_groups -asynchronous
4. Fix the worst 5 paths, re-run STA
5. Iterate until all slack > 0
```

---

## Power Sequencing

| Symptom | Root Cause | Fix |
|---|---|---|
| FPGA doesn't configure after power-up | VCCINT ramp too slow — POR timer expires | Check PMIC soft-start; reduce VCCINT ramp time to <50ms |
| FPGA draws excessive current, no config | Incorrect power sequencing (e.g., VCCO before VCCINT) | Verify sequence: VCCINT → VCCAUX → VCCO |
| Transceivers fail to lock | MGTAVCC/MGTAVTT noisy or late | Dedicated LDO for transceiver rails; check PSRR |
| Random configuration failures at cold temp | PLL lock lost due to voltage droop | Add bulk capacitance (100µF+) near FPGA core supply |
| FPGA powers up, immediately overheats | VCCINT shorted to GND (solder bridge) | Measure VCCINT resistance to GND; rework BGA |

### Power Sequencing by Vendor

| Vendor | Required Sequence | Tolerance |
|---|---|---|
| **Xilinx 7-series** | VCCINT → VCCAUX → VCCO | VCCINT must be within 10% before VCCAUX rises |
| **Xilinx UltraScale+** | VCCINT → VCCAUX → VCCO → MGTAVCC → MGTAVTT | Transceiver rails must be last |
| **Intel Cyclone V** | VCCD_FPLL → VCCINT → VCCA → VCCIO | PLL rail must be first |
| **Lattice ECP5** | VCC → VCCAUX → VCCIO | Simpler; fewer rails |
| **Gowin GW1N** | VCC → VCCIO | Flash-based; simplest sequencing |

---

## Configuration Failures

| Symptom | Root Cause | Fix |
|---|---|---|
| `INIT_B` stuck low | CRC check failed on bitstream | Rebuild bitstream; check flash integrity |
| `DONE` never goes high | Missing external pull-up on DONE pin | 330Ω to VCCO on DONE |
| `PROGRAM_B` keeps resetting | Floating PROGRAM_B pin | External 4.7kΩ pull-up to VCCO |
| JTAG IDCODE = `0xFFFFFFFF` | JTAG chain broken (TDI/TDO open) | Check JTAG header soldering; verify TCK continuity |
| Flash programming succeeds but FPGA doesn't boot | MSEL/M[2:0] wrong for flash mode | Verify strapping resistors match flash config mode |
| FPGA configures but bitstream wrong | Old .mcs / .pof in flash | Erase flash before reprogramming; old data can persist |
| Configuration takes too long | Flash interface too slow (SPI vs BPI) | Use BPI (parallel) or QSPI for faster config |
| FPGA configures, then immediately reconfigures | Watchdog timeout — design doesn't assert DONE | Ensure design doesn't drive DONE low; check startup clock |

---

## Clocking Issues

| Symptom | Root Cause | Fix |
|---|---|---|
| PLL doesn't lock | Input clock outside PLL frequency range | Check PLL min/max input frequency in datasheet |
| High jitter on fabric clock | Clock on non-CC pin; PLL cascade | Route clock to MRCC/GC pin; avoid PLL→PLL cascading |
| `No clock defined` warning | Missing `create_clock` on input port | Add create_clock constraint on all primary inputs |
| Generated clock timing wrong | Missing `create_generated_clock` on PLL output | Define generated clocks at PLL outputs |
| PLL lock but system unstable | Reference clock jitter too high | Use dedicated oscillator, not FPGA-derived refclk |
| Clock buffer overflow | Too many clocks on BUFGCTRL (max 32 on 7-series) | Use BUFR for regional clocks; merge clock domains |
| MMCM phase shift wrong | Dynamic phase shift not waited for lock | Wait for LOCKED after phase shift before using output |

---

## BRAM and Memory Errors

| Symptom | Root Cause | Fix |
|---|---|---|
| BRAM collision warning | Simultaneous read/write to same port at same address | Add read-first or write-first behavior; use RAM inference template |
| BRAM contents corrupted | No initialization — random on power-up | Initialize BRAM with `$readmemh` or `INIT_00` parameters |
| FIFO data corruption | Read during write on same clock (SRL-based FIFO) | Use block RAM (not SRL) for >16-deep FIFOs |
| Synthesis infers SRL not BRAM | Read-after-write pattern in always block | Use `(* ram_style = "block" *)` attribute |
| Multi-port RAM impossible | True dual-port BRAM only supports 2 write ports | For 3+ write ports, use banked BRAM or register-based RAM |
| DPRAM width mismatch | Port A = 32-bit, Port B = 8-bit on same BRAM | Use asymmetric BRAM (VHDL: `推断不对称双端口RAM`) |

### BRAM Collision Code Example

```verilog
// BAD: Simultaneous read/write collision
always @(posedge clk) begin
    if (wr_en) mem[addr] <= wr_data;  // Write
    rd_data <= mem[addr];              // Read same address!
end

// GOOD: Read-first behavior (Xilinx)
always @(posedge clk) begin
    if (wr_en) mem[addr] <= wr_data;
    rd_data <= mem[addr];  // Read returns OLD data before write
end

// GOOD: Write-first behavior
always @(posedge clk) begin
    if (wr_en) begin
        mem[addr] <= wr_data;
        rd_data <= wr_data;  // Bypass: return new data immediately
    end else begin
        rd_data <= mem[addr];
    end
end
```

---

## Signal Integrity

| Symptom | Root Cause | Fix |
|---|---|---|
| DDR calibration fails | Reflections on DQ/DQS lines | Add series termination (22–33Ω) near DDR chip |
| PCIe link won't train | AC coupling caps missing or wrong value | Add 75–200 nF caps on TX pairs per PCIe spec |
| Ethernet link drops at high traffic | Crosstalk between TX and RX differential pairs | Increase spacing; route TX/RX on different layers |
| Random bit errors on high-speed link | Via stub resonance (on thru-hole vias) | Use back-drilled vias or blind vias for >5 Gbps |
| USB enumeration fails | Impedance mismatch on USB traces | 90Ω differential (45Ω single-ended); controlled dielectric |
| SPI flash read errors | Long PCB traces with stubs | Route SPI as point-to-point; add series termination |

---

## Resource Exhaustion

| Symptom | Root Cause | Fix |
|---|---|---|
| `Out of LUTs` error | Design too large for target device | Optimize RTL; use DSP instead of LUT math; consider larger device |
| `Out of BRAM` error | Too many FIFOs/RAMs | Reduce FIFO depth; use SRL for shallow FIFOs; share BRAM |
| `Out of DSP` error | Too many multipliers | Time-multiplex DSP slices; use LUT-based multipliers for small factors |
| P&R fails with routing congestion | Localized high utilization (>80% in one region) | Floorplan design; spread logic with pblocks; reduce utilization |
| Build time excessive (>8 hours) | Very large design with tight constraints | Reduce constraint complexity; use OOC (out-of-context) synthesis |

### Resource Reduction Techniques

| Technique | Saves | Trade-Off |
|---|---|---|
| Replace LUT multipliers with DSP | 100+ LUTs per multiply | Fixed DSP placement; may need pipeline |
| Use SRL16E instead of BRAM for shallow FIFOs | 1 LUT vs 1 BRAM | Max 16-deep FIFO per SRL |
| Share BRAM between small RAMs | Up to 50% BRAM reduction | Requires arbitration logic |
| Time-multiplex DSP slices | 2–8× fewer DSP | Requires state machine + slower throughput |
| Reduce state machine encoding | 2–10× fewer registers for FSM | One-hot uses more FFs but often fewer LUTs |

---

## Synthesis and Build Issues

| Symptom | Root Cause | Fix |
|---|---|---|
| `Multi-driven net` error | Two always blocks drive same signal | Move all assignments to single always block |
| `Combinational loop` error | Signal feeds back without register | Break loop with register or add `(* allow_retiming *)` |
| X-propagation in simulation | Uninitialized registers or missing default | Initialize all regs; add `default:` in case statements |
| Synthesis produces wrong logic | `if/else` priority vs `case` parallel | Use `(* parallel_case *)` or `unique case` |
| Black box not found | Missing IP core or wrong library path | Add IP source files; check include paths |
| Incremental build fails | RTL change invalidates reference | Clean build; run full synthesis again |

---

## Quick Decision Tree

```
FPGA doesn't work?
    │
    ├─ No LEDs, no JTAG? → Power sequencing / rail short
    ├─ JTAG works, won't configure? → Configuration / MSEL / DONE pull-up
    ├─ Configures, behaves randomly? → Metastability / CDC / timing violation
    ├─ Configures, crashes under load? → Power integrity / IR drop
    ├─ Works for seconds, then fails? → Thermal shutdown
    ├─ Works at room temp, fails at cold/hot? → Timing corner violation
    └─ Works in simulation, fails on board? → Signal integrity / I/O standard
```

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [CDC Coding](../04_hdl_and_synthesis/cdc_coding.md) | This KB | Clock domain crossing patterns |
| [Timing Closure](../05_timing_and_constraints/timing_closure.md) | This KB | Methodology for fixing timing violations |
| [Power Integrity](../09_board_design/power_integrity.md) | This KB | PDN design, decoupling, sequencing |
| [High-Speed Signals](../09_board_design/high_speed_signals.md) | This KB | Signal integrity, crosstalk, eye diagrams |
| [Configuration Interfaces](../09_board_design/configuration_interfaces.md) | This KB | Flash selection, config modes, fallback |
| [Bring-Up Checklist](bring_up_checklist.md) | This KB | Systematic bring-up sequence |