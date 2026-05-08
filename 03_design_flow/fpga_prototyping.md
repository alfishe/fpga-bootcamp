[← Design Flow Home](README.md) · [← Project Home](../README.md)

# FPGA Prototyping & ASIC Emulation

Before committing to a $10M+ ASIC tapeout, you need to verify your RTL on real silicon. FPGA prototyping maps an ASIC design onto one or more FPGAs, running at a fraction of the target clock speed but with full functional accuracy. This article covers partitioning strategies, multi-FPGA interconnect, co-simulation bridges, clock migration, and the commercial prototyping platforms used in the industry.

For the standard FPGA design flow, see [Design Flow Overview](overview.md). For synthesis optimization, see [Synthesis](synthesis.md). For vendor migration considerations, see [Vendor Migration](vendor_migration.md).

---

## Why FPGA Prototyping?

| Goal | How FPGA Prototyping Helps |
|------|---------------------------|
| **Functional verification** | Run real software stacks (Linux, Android, firmware) against the RTL for billions of cycles |
| **Software development** | Give software teams a platform months before silicon arrives |
| **Corner case coverage** | Simulation covers millions of cycles; prototyping covers billions |
| **In-system validation** | Connect real peripherals (PCIe, USB, Ethernet) that simulation can't model |
| **Power/performance hints** | Toggle rates from real workloads feed power estimation |

### Prototyping vs. Simulation vs. Emulation

| Aspect | RTL Simulation | FPGA Prototyping | Hardware Emulation (Palladium/Veloce) |
|--------|---------------|-----------------|--------------------------------------|
| Speed | 10–1000 Hz | 10–100 MHz | 1–10 MHz |
| Cycle accuracy | Exact | Exact (if mapped correctly) | Exact |
| Cost | $0–$50K (licenses) | $5K–$500K | $1M–$10M |
| Debug visibility | Full (all signals) | Limited (ILA/probes) | Good (waveform capture) |
| Setup time | Hours | Weeks–Months | Days–Weeks |
| Software workloads | Short tests only | Full OS boot, benchmarks | Medium workloads |
| Capacity | Unlimited (memory) | 100M–1B gates (multi-FPGA) | 10B+ gates |

---

## Partitioning — When One FPGA Isn't Enough

### Capacity Planning

| ASIC Gate Count | FPGA Resources Needed | Prototyping Approach |
|----------------|----------------------|---------------------|
| < 500K gates | 1 × mid-range FPGA (Artix-7, Cyclone V) | Single-FPGA |
| 500K–5M gates | 1 × large FPGA (Virtex UltraScale+, Stratix 10) | Single-FPGA |
| 5M–50M gates | 2–4 large FPGAs | Multi-FPGA board |
| 50M–500M gates | 4–16+ FPGAs | Commercial prototyping platform |
| 500M+ gates | 16–64 FPGAs | Emulation cluster |

**Rule of thumb:** An ASIC gate ≈ 2–5 FPGA LUTs (depends on logic type). A design that uses 1M ASIC gates typically needs 2–5M FPGA LUTs.

### Partitioning Strategies

#### Time-Multiplexed (Single-FPGA)

Run different ASIC blocks on the same FPGA at different times. Works for designs with distinct test phases.

```
┌────────────────────────────┐
│       Single FPGA          │
│  ┌──────────┐ ┌─────────┐  │
│  │ Phase 1  │ │ Phase 2 │  │
│  │ CPU+Cache│ │ GPU+MEM │  │
│  └──────────┘ └─────────┘  │
│  (never active at once)    │
└────────────────────────────┘
```

**Pros:** Lowest cost. **Cons:** Cannot test full-system interaction.

#### Cut-Based Partitioning (Multi-FPGA)

Split the ASIC netlist at module boundaries. Each FPGA hosts one or more blocks. Inter-FPGA connections carry the cut signals.

```
┌──────────┐    SerDes    ┌──────────┐
│  FPGA 0  │──────────────│  FPGA 1  │
│ CPU +    │   high-speed │ GPU +    │
│ L2 Cache │   serial     │ Memory   │
│          │   link       │ Ctrl     │
└──────────┘              └──────────┘
      │                       │
      │    ┌──────────┐       │
      └────│  FPGA 2  │───────┘
           │ IO + DMA │
           └──────────┘
```

**Key challenge:** Inter-FPGA bandwidth. Each cut signal must cross a physical link:

| Interconnect | Bandwidth (per lane) | Latency | Pin Cost |
|-------------|---------------------|---------|----------|
| Direct LVDS pair | 0.5–1.5 Gbps | 1–2 cycles | 2 pins |
| GTH/GTY transceiver | 10–58 Gbps | 10–40 cycles | 4–8 pins |
| Parallel bus (16-bit) | 200 Mbps @ 12.5 MHz | 1 cycle | 36 pins (16+16+ctrl) |
| Aurora 64B/66B | 5–58 Gbps | ~20 cycles | 4–8 pins |

#### Automatic Partitioning Tools

| Tool | Vendor | Approach | Max FPGAs |
|------|--------|----------|-----------|
| **Certify** | Synopsys | Automatic cut-based partitioning | 64+ |
| **ProtoCompiler** | Synopsys | Multi-FPGA synthesis + partitioning | 32+ |
| **FPGA Prototyping Compiler** | Cadence | Partition + synthesis + debug | 16+ |
| **BlueBox** | AMD/Xilinx | Xilinx-specific multi-FPGA flow | 16 |
| **Manual** | — | Hand-coded hierarchy assignment | Any |

---

## Clock Migration — ASIC Clocks → FPGA Clocks

ASIC designs use different clocking conventions than FPGAs. Migration requires careful handling:

| ASIC Feature | FPGA Challenge | Migration Strategy |
|-------------|---------------|-------------------|
| **Generated clocks** (PLL output dividers) | FPGA PLLs have limited M/D ratios | Pre-compute achievable ratios; add clock domain logic |
| **Clock gating cells** (ICG) | FPGA has no latch-based ICG | Replace with BUFGCE or inferred clock gating |
| **Multiple clock domains** | FPGA has limited PLL/MMCM resources | Merge similar-frequency domains; share PLLs |
| **Clock mesh** | FPGA clock tree has fixed structure | Accept higher skew; add margin in STA |
| **Custom CDR** | FPGA transceiver CDR is fixed | Use FPGA CDR with same line rate; custom CDR in fabric |
| **Half-cycle paths** | FPGA tools struggle with these | Add false_path or retiming |
| **Latch-based designs** | FPGAs have limited latch support | Convert to edge-triggered if possible |

### PLL Configuration Migration

```tcl
# ASIC: clk_400m generated from clk_50m with M=8, D=1
# FPGA: Same ratio achievable with MMCM

# Vivado MMCM configuration
create_clock -period 20.000 [get_ports clk_50m_in]

create_generated_clock -name clk_400m \
    -multiply_by 8 -divide_by 1 \
    -source [get_pins mmcm_inst/CLKIN1] \
    [get_pins mmcm_inst/CLKOUT0]
```

---

## Memory Migration

### ASIC SRAM → FPGA BRAM

| ASIC SRAM Type | FPGA Mapping | Notes |
|---------------|-------------|-------|
| Single-port SRAM | Single-port BRAM | Direct mapping |
| Dual-port SRAM | True dual-port BRAM | Direct mapping |
| 1R1W pseudo-dual | Simple dual-port BRAM | Direct mapping |
| Multi-port (2R2W+) | Replicate BRAM or bank | Multi-port not native to BRAM |
| Register file (1WnR) | n × BRAM (write broadcast) | All BRAMs receive same write data |
| Custom SRAM compiler output | Behavioral replacement | Black-box ASIC SRAM → BRAM inference |

### Memory Replacement Strategy

```verilog
// ASIC: black-box SRAM (compiler-generated)
// Your design instantiates: sram_32x256 u0 (.clk, .cs, .we, .addr, .din, .dout);

// FPGA: replace with behavioral BRAM
// Option 1: Use `ifdef FPGA_PROT to swap instantiation
`ifdef FPGA_PROT
    bram_32x256 u0 (.clk, .cs, .we, .addr, .din, .dout);
`else
    sram_32x256 u0 (.clk, .cs, .we, .addr, .din, .dout);
`endif

// Option 2: FuseSoC core with variant
//   core_name:   my_sram
//   default:     asic_sram
//   variant fpga: fpga_bram
```

### Memory Width/Depth Adjustment

ASIC SRAMs come in arbitrary aspect ratios. FPGA BRAMs are 36Kb (or 18Kb), configurable as:

| Configuration | Depth | Width | BRAMs Used |
|---------------|-------|-------|-----------|
| 36Kb × 1 | 32768 | 1 | 1 |
| 36Kb × 4 | 8192 | 4 | 1 |
| 36Kb × 9 | 4096 | 9 (8+parity) | 1 |
| 36Kb × 18 | 2048 | 18 (16+parity) | 1 |
| 36Kb × 36 | 1024 | 36 (32+parity) | 1 |
| 72Kb × 36 (cascade) | 2048 | 36 | 2 |

When ASIC SRAM doesn't match a BRAM aspect ratio, you must either:
- **Pad the width** (add don't-care bits to fill BRAM)
- **Cascade BRAMs** (concatenate for deeper memories)
- **Use distributed RAM** (for small memories < 64 entries)

---

## Co-Simulation Bridges

### SpeedBridge / Transactor Models

Connect FPGA prototype to a software simulator for hybrid verification:

```
┌─────────────────┐         ┌─────────────────┐
│  Software Sim   │  TCP/   │  FPGA Prototype │
│  (VCS/Xcelium)  │◄───────►│  (Virtex/Ultra) │
│                 │  PCIe   │                 │
│  - Testbench    │         │  - DUT RTL      │
│  - Checkers     │         │  - SpeedBridge  │
│  - Scoreboard   │         │    transactor   │
└─────────────────┘         └─────────────────┘
```

| Bridge Type | Vendor | Protocol | Latency |
|------------|--------|----------|---------|
| **SpeedBridge** | Synopsys | AXI/AHB/APB | ~1 μs |
| **Cadence Palladium** | Cadence | Multiple | ~100 ns |
| **Veloce** | Siemens | Multiple | ~500 ns |
| **Custom DPI-C** | Any | TCP/PCIe | Variable |

### Custom Co-Emulation with DPI-C

```c
// DPI-C bridge: FPGA side sends AXI transactions to software checker
#include "svdpi.h"
#include <sys/socket.h>

int bridge_fd;

void bridge_init() {
    bridge_fd = socket(AF_INET, SOCK_STREAM, 0);
    // connect to software checker...
}

void bridge_axi_write(int addr, int data) {
    uint32_t pkt[2] = {addr, data};
    send(bridge_fd, pkt, 8, 0);
}

int bridge_axi_read(int addr) {
    uint32_t pkt[1] = {addr};
    send(bridge_fd, pkt, 4, 0);
    uint32_t data;
    recv(bridge_fd, &data, 4, 0);
    return data;
}
```

```verilog
// SystemVerilog DPI import
import "DPI-C" function void bridge_init();
import "DPI-C" function void bridge_axi_write(input int addr, input int data);
import "DPI-C" function int  bridge_axi_read(input int addr);
```

---

## Debug Visibility on FPGA Prototypes

### ILA Depth Challenges

ASIC prototypes run at 10–100 MHz for hours. ILA depth of 65K samples captures < 1 ms. Solutions:

| Technique | Capture Depth | Trade-off |
|-----------|--------------|-----------|
| Deep ILA (max BRAM) | 1M+ samples | Consumes BRAM that could hold design logic |
| Stream to host via PCIe | Unlimited | Requires PCIe core; limited by host bandwidth |
| Triggered capture | Variable | Only captures around events of interest |
| Trace FIFO to DRAM | Very deep | Requires DDR controller + DRAM interface |
| On-chip trace (ARM CoreSight) | Compressed | Only for CPU cores with trace output |

### Multi-FPGA Debug Synchronization

When logic spans multiple FPGAs, correlating ILA captures across devices requires:

1. **Common trigger:** Distribute a trigger signal across all FPGAs
2. **Timestamp alignment:** Each FPGA marks captures with a common counter
3. **Post-processing:** Merge ILA data from all FPGAs, sorted by timestamp

```
┌────────┐  trigger  ┌────────┐
│ FPGA 0 │──────────►│ FPGA 1 │
│ ILA    │           │ ILA    │
│ t=0..N │           │ t=0..N │
└───┬────┘           └───┬────┘
    │                    │
    └──────┬─────────────┘
           ▼
    ┌──────────────┐
    │ Merge Tool   │
    │ (correlated  │
    │  waveforms)  │
    └──────────────┘
```

---

## Commercial Prototyping Platforms

| Platform | Vendor | FPGAs | Capacity | Speed | Price Range |
|----------|--------|-------|----------|-------|-------------|
| **HAPS-70** | Synopsys | 1–2 × Virtex UltraScale+ | 200M+ gates | 100 MHz | $100K–$300K |
| **HAPS-100** | Synopsys | 2–4 × Virtex UltraScale+ HBM | 500M+ gates | 200 MHz | $200K–$500K |
| **Protium X1** | Cadence | 1–4 × Virtex UltraScale+ | 300M+ gates | 100 MHz | $150K–$400K |
| **Veloce Strato** | Siemens | Custom FPGA array | 15B+ gates | 1–5 MHz | $1M+ |
| **Palladium Z2** | Cadence | Custom processors | 20B+ gates | 1–4 MHz | $2M+ |
| **Alveo SN1022** | AMD | 2 × VU45P (HBM) | 100M+ gates | 200 MHz | $30K–$60K |
| **Varium C1500** | Xilinx | VU9P | 50M+ gates | 200 MHz | $10K–$15K |

### Open / DIY Multi-FPGA Prototyping

| Board | FPGAs | Interconnect | Target Use |
|-------|-------|-------------|-----------|
| **AWS F1** | 1 × VU9P | PCIe Gen3 ×16 | Cloud prototyping |
| **Alveo AU280** | 1 × VU9P + HBM | PCIe Gen4 | Memory-intensive |
| **Custom 4-FPGA board** | 4 × Artix-7 | Aurora links | Educational / budget |
| **FireSim** | Cloud FPGA instances | Ethernet | RISC-V chip prototyping |

---

## RTL Modifications for Prototyping

### Common `ifdef` Pattern

```verilog
module my_soc (
`ifdef FPGA_PROT
    // FPGA prototype ports
    input  wire        clk_50mhz,      // board oscillator
    input  wire        uart_rx,        // debug UART
    output wire        uart_tx,
    output wire [7:0]  led,            // status LEDs
`else
    // ASIC ports
    inout  wire [31:0] pad_gpio,
    output wire        clk_pll_out,    // ASIC PLL output
`endif
    // Common ports
    input  wire        rst_n
);

// ASIC SRAM → FPGA BRAM replacement
`ifdef FPGA_PROT
    bram_wrapper #(.DW(32), .DEPTH(256)) u_ram0 (...);
`else
    asic_sram_32x256 u_ram0 (...);
`endif

// ASIC clock gating → FPGA BUFGCE
`ifdef FPGA_PROT
    BUFGCE u_clk_gate (.I(clk), .CE(clk_en), .O(gated_clk));
`else
    CLK_GATE_CELL u_clk_gate (.CK(clk), .EN(clk_en), .CKG(gated_clk));
`endif

endmodule
```

### Compile-Time Switches

| Define | Purpose | Typical Effect |
|--------|---------|---------------|
| `FPGA_PROT` | Enable FPGA prototype mode | Swap SRAMs, clocks, IO |
| `PROT_SPEED` | Reduce operating frequency | Relax timing constraints |
| `PROT_DEBUG` | Enable ILA + debug UART | Add debug infrastructure |
| `PROT_NO_ANALOG` | Stub analog blocks | Replace ADC/DAC/PLL with stubs |
| `PROT_NO_SRAM_BIST` | Remove BIST controllers | Save area for design logic |

---

## Bring-Up Methodology

### Phase 1: Sanity

1. Program bitstream — verify LEDs blink
2. Check clock frequencies via XADC/SysMon
3. Verify JTAG chain — all FPGAs detected
4. Test UART console — basic printf works

### Phase 2: Block-Level

1. Enable one block at a time
2. Run block-level tests from simulation
3. Verify register access (read/write checks)
4. Check interrupt delivery

### Phase 3: Integration

1. Enable inter-block communication
2. Run full-chip test suite
3. Boot OS / firmware
4. Run stress tests (hours/days)

### Phase 4: Performance

1. Measure achievable fMAX
2. Profile power consumption
3. Run software benchmarks
4. Feed toggle rates back to power estimation

---

## Common Pitfalls

| Pitfall | What Happens | Fix |
|---------|-------------|-----|
| **Wrong SRAM mapping** | ASIC SRAM has different latency than BRAM | Insert pipeline registers to match ASIC timing; document all latency differences |
| **Missing clock domain crossing** | ASIC uses clock gates that don't exist in FPGA | Add explicit synchronizers at every crossing |
| **Floating pads** | ASIC has internal pull-ups; FPGA IO defaults to weak pull-up | Add explicit pull-up/pull-down constraints |
| **Timing mismatch** | ASIC runs at 1 GHz; prototype at 50 MHz | Scale all timing-sensitive code (timeouts, baud rates) |
| **Transceiver initialization** | ASIC SerDes is custom; FPGA transceivers need their own init | Add transceiver initialization state machine before protocol logic |
| **Reset sequencing** | ASIC has single POR; FPGA needs per-domain reset | Add reset synchronization module per domain |

---

## Cross-References

| Topic | Article |
|-------|---------|
| Standard design flow | [Design Flow Overview](overview.md) |
| Synthesis optimization | [Synthesis](synthesis.md) |
| Vendor migration | [Vendor Migration](vendor_migration.md) |
| Clock domain crossing | [CDC Coding](../04_hdl_and_synthesis/cdc_coding.md) |
| Debug with ILA | [ILA / SignalTap](../08_debug_and_tools/ila_signaltap.md) |
| DFX (for partial prototyping) | [DFX & Partial Reconfiguration](../16_advanced_topics/dfx_partial_reconfiguration.md) |
| Memory types in FPGA | [BRAM & URAM](../02_architecture/fabric/bram_and_uram.md) |
