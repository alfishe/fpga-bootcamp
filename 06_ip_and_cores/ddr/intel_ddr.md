[← 06 IP & Cores Home](../README.md) · [← DDR Home](README.md) · [← Project Home](../../../README.md)

# Intel DDR Memory Controllers — UniPHY & EMIF

Intel provides two DDR controller generations: **UniPHY** (Cyclone V, Arria V, Arria 10) and **EMIF** (Stratix 10, Agilex, Arria 10 in hard-controller mode). Both abstract DDR PHY complexity behind an Avalon-MM interface, but their architecture and configuration differ significantly.

---

## UniPHY Architecture (Cyclone V / Arria V / Arria 10)

The UniPHY IP is a **soft memory controller** paired with a **hard PHY** (the physical I/O registers and DLLs in the FPGA fabric):

```
                    ┌─────────── UniPHY IP ───────────┐
Avalon-MM  ────────→│  Memory    ───→  PHY (ALTMEMPHY) │──→ DDR3/DDR3L/DDR2
  Master            │  Controller     Hard I/O + DLLs   │    up to 400 MHz
                    └──────────────────────────────────┘
```

### Cyclone V SoC — Hard Memory Controller (HMC)

Cyclone V and Arria V **SoC** variants include a hardened memory controller in the HPS (Hard Processor System). This is separate from the FPGA fabric DDR:

| Controller | Location | Interface | Best For |
|---|---|---|---|
| **HPS SDRAM Controller** | HPS hard block | HPS-to-SDRAM bus (internal) | Linux system memory, HPS DDR |
| **UniPHY (FPGA)** | FPGA fabric soft logic | Avalon-MM (FPGA side) | FPGA fabric DDR, video frame buffers, DMA buffers |

> The HPS hard controller is configured via the HPS Megawizard; the FPGA-side UniPHY is configured via the IP Catalog separately. They can target the same or different DDR chips.

### Configuration & Parameterization

Key parameters in the UniPHY IP configuration dialog (Platform Designer or IP Catalog):

| Parameter | Description | Typical Value |
|---|---|---|
| **Memory type** | DDR3 / DDR3L / DDR2 / LPDDR2 | DDR3L (Cyclone V) |
| **Data width** | Per controller: 8/16/32/64-bit | 16 or 32 |
| **Frequency** | Controller clock (half-rate for PHY) | 300–400 MHz (DDR3-800 to DDR3-1066) |
| **Row/Column/Bank** | Address mapping | Auto (from JEDEC SPD) |
| **Burst length** | On-the-fly burst chop (BC4/BL8) | BL8 (default) |
| **ODT** | On-die termination: Rtt_Nom, dynamic ODT | RZQ/4 (60Ω) for DDR3 |
| **Write leveling** | Required for DDR3 fly-by topology | Enabled |
| **DQS delay chain** | Per-DQS phase adjustment | Auto-calibrated |

### Calibration Sequence

The UniPHY controller runs a multi-stage calibration at power-up:

```
1. Memory Initialization (JEDEC sequence)
   ├── Precharge All
   ├── Load Mode Registers (MR0/MR1/MR2)
   └── ZQ Calibration (ZQCL)
2. Write Leveling
   ├── Align CK-to-DQS at each DRAM
   └── Compensate for fly-by topology skew
3. Read DQS Centering
   ├── Sweep DQS delay per byte lane
   └── Center DQS in the data eye
4. Read/Write Training
   ├── Sweep read data valid window (per-bit deskew)
   └── Verify write data timing at DRAM
```

The calibration result is stored in registers accessible via the controller's Avalon-MM status interface.

---

## EMIF — External Memory Interface (Stratix 10 / Agilex / Arria 10 Hard)

EMIF is Intel's next-generation DDR controller for 20nm and below:

| Feature | UniPHY (28nm) | EMIF (20nm/14nm/10nm) |
|---|---|---|
| **Controller type** | Soft logic | Hard controller (Arria 10/S10/Agilex) |
| **Max DDR4 speed** | N/A | DDR4-3200 (Agilex) |
| **DDR3 support** | Yes | Yes (backward compatible) |
| **LPDDR4** | No | Yes (Agilex) |
| **QDR II/II+** | No | Yes (RLDRAM 3) |
| **ECC** | Optional | Hard ECC (S10/Agilex) |
| **Interface** | Avalon-MM | Avalon-MM (with AXI4 bridge option) |
| **Calibration** | Soft + hard PHY | Nios II-based calibration processor |
| **Tool** | IP Catalog / Qsys | Platform Designer / IP Catalog |

### EMIF Efficiency Factors

| Factor | Impact | Mitigation |
|---|---|---|
| **Row miss** (tRC penalty) | 30–50% throughput drop | Bank interleaving, open-page policy |
| **Read-to-write turnaround** | 2–4 dead cycles | Group reads/writes |
| **Refresh (tRFC)** | 3–9% overhead (DDR4) | Refresh scheduling during idle |
| **Command bus contention** | 1–2 cycles queue delay | Use multiple chip-selects |

Typical efficiency: 75–85% for random access, 90–95% for sequential streaming.

---

## Avalon-MM to DDR Mapping

The UniPHY/EMIF controller presents a flat byte-addressable memory space:

```verilog
// Writing to DDR via Avalon-MM
// addr = byte address in DDR space
// burstcount = number of beats (each beat = data_width/8 bytes)
// For 32-bit data width, each beat is 4 bytes, addr increments by 4 per beat

always @(posedge clk) begin
    if (!waitrequest && write) begin
        // This beat is accepted
        // addr should be aligned to data width
    end
end
```

**Address map** (32-bit data width example):
- Beat 0: addr 0x0000_0000 → DDR bytes [3:0]
- Beat 1: addr 0x0000_0004 → DDR bytes [7:4]
- Burst of 8: addr 0x0000_0000, burstcount=8 → 32 bytes transferred

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **PHY reset stuck** | Calibration never completes | Check PLL lock, pll_ref_clk frequency |
| **Write leveling failure** | Calibration error "WL_FAIL" | Verify CK-to-DQS board delay within spec; adjust board skew |
| **Address/command timing** | Intermittent data corruption | Ensure address/command signals meet setup/hold at DRAM; check fly-by resistor pack |
| **Mismatched ODT settings** | Signal integrity issues, eye closure | Set Rtt_Nom = RZQ/4 (60Ω) for DDR3; verify VTT termination |
| **Avalon address alignment** | Unexpected data at wrong offsets | Each beat is `data_width/8` bytes; addr must be aligned |
| **HPS + FPGA DDR sharing** | Both controllers try to access same chip | They MUST target different DDR chips or use separate chip-selects |

---

## Further Reading

| Article | Topic |
|---|---|
| [xilinx_ddr.md](xilinx_ddr.md) | Xilinx MIG — DDR3/DDR4/LPDDR4 across 7-series and UltraScale+ |
| [lattice_others_ddr.md](lattice_others_ddr.md) | Lattice, Microchip, Gowin DDR controllers |
| [ddr_pin_planning.md](ddr_pin_planning.md) | PCB trace routing, fly-by topology, pin constraints |
| Intel EMI Handbook | https://www.intel.com/emif |
