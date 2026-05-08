[← Design Flow Home](README.md) · [← Project Home](../README.md)

# Vendor Migration & Portability — Cross-Vendor FPGA Design

Designs outlive their target FPGA. A product built on Cyclone V may need to migrate to ECP5 for cost, or to Artix-7 for availability. This article covers the practical aspects of making RTL portable: abstraction layers, vendor-neutral coding, IP replacement strategies, constraint translation, and build-system automation with FuseSoC and Edalize.

For design patterns that support portability, see [Design Patterns](../04_hdl_and_synthesis/design_patterns.md). For vendor-specific pragmas, see [Vendor Pragmas](../04_hdl_and_synthesis/vendor_pragmas.md). For FPGA prototyping (ASIC→FPGA), see [FPGA Prototyping](fpga_prototyping.md).

---

## Why Vendor Migration Matters

| Scenario | Frequency | Impact |
|----------|-----------|--------|
| **End-of-life (EOL)** | Common — 7–10 year product lifecycle vs 3–5 year FPGA lifecycle | Forced migration |
| **Cost reduction** | Very common — move from high-end to mid-range | NRE cost vs volume savings |
| **Supply chain disruption** | Unpredictable — pandemic, trade restrictions | Emergency migration |
| **Second source** | Common in automotive/defense | Qualify two vendors |
| **Technology upgrade** | Periodic — new features, lower power | Voluntary migration |

---

## Portability Layers

```
┌─────────────────────────────────────────────────────────┐
│                  Application Logic                       │
│          (vendor-neutral, parameterized RTL)             │
├─────────────────────────────────────────────────────────┤
│              Abstraction Layer (wrappers)                │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│   │  Clock   │ │  Memory  │ │   I/O    │ │   DSP    │ │
│   │ abstract │ │ abstract │ │ abstract │ │ abstract │ │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
├────────┼────────────┼────────────┼────────────┼────────┤
│        ▼            ▼            ▼            ▼         │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │
│   │Xilinx  │  │ Intel  │  │Lattice │  │ Gowin  │      │
│   │prims   │  │ prims  │  │ prims  │  │ prims  │      │
│   └────────┘  └────────┘  └────────┘  └────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## Vendor-Neutral RTL Rules

### 1. Avoid Vendor Primitives in Application Logic

```verilog
// BAD: vendor-locked
BUFGCE u_clk (.I(clk), .CE(en), .O(gated_clk));
// This only compiles on Xilinx

// GOOD: abstract wrapper
clock_gate u_clk (.clk(clk), .enable(en), .clk_out(gated_clk));
// clock_gate is implemented per-vendor in a separate file
```

### 2. Use Parameters, Not Hard-Coded Values

```verilog
// BAD: assumes 36Kb BRAM
reg [31:0] mem [0:1023];

// GOOD: parameterized
module ram_wrapper #(
    parameter DATA_W = 32,
    parameter DEPTH  = 1024
) (
    input  wire                  clk,
    input  wire                  we,
    input  wire [AW-1:0]        addr,
    input  wire [DATA_W-1:0]    din,
    output wire [DATA_W-1:0]    dout
);
    localparam AW = $clog2(DEPTH);
    reg [DATA_W-1:0] mem [0:DEPTH-1];
    always @(posedge clk) begin
        if (we) mem[addr] <= din;
    end
    assign dout = mem[addr];
endmodule
```

### 3. Separate Behavioral from Structural

```verilog
// file: rtl/spi_master.v         — behavioral, vendor-neutral
// file: rtl/xilinx/spi_top.sv    — structural, instantiates Xilinx IO primitives
// file: rtl/intel/spi_top.sv     — structural, instantiates Intel IO primitives
// file: rtl/lattice/spi_top.sv   — structural, instantiates Lattice IO primitives
```

### 4. Use `ifdef` Sparingly — Prefer Build System Selection

```verilog
// AVOID: ifdefs everywhere (fragile, hard to read)
`ifdef XILINX
    BUFGCE u_bufgce (.I(clk), .CE(en), .O(gated_clk));
`elsif INTEL
    altera_clock_gating u_cg (.clk(clk), .ena(en), .clk_out(gated_clk));
`elsif LATTICE
    // Lattice has no native clock gate primitive
    assign gated_clk = clk & en;  // NOT glitch-free — needs wrapper
`endif

// PREFER: separate files per vendor, selected by build system
// spi_top_xilinx.sv   → uses BUFGCE
// spi_top_intel.sv    → uses altera_clock_gating
// spi_top_lattice.sv  → uses custom gate-and-register
```

---

## IP Replacement Strategy

### Vendor IP Mapping Table

| Function | Xilinx | Intel | Lattice | Microchip | Open-Source |
|----------|--------|-------|---------|-----------|-------------|
| DDR3 controller | MIG 7-series | EMIF | DDR3 IP Core | DDR3 IF | LiteDRAM |
| DDR4 controller | MIG UltraScale+ | EMIF | DDR4 IP Core | DDR4 IF | LiteDRAM |
| PCIe Gen3 | XDMA / PCIe IP | PCIe Gen3 IP | PCIe IP | — | litepcie |
| AXI Interconnect | AXI Interconnect | Qsys Interconnect | — | — | [verilog-axi](https://github.com/alexforencich/verilog-axi) |
| Clock manager | MMCM/PLL | IOPLL | PLL | PLL | — |
| FIFO | FIFO Generator | DCFIFO | FIFO IP | FIFO | [fifo_generator](https://github.com/FPGA-Systems/fifo_generator) |
| SPI Flash | AXI Quad SPI | EPCS/EPCQ | SPI Flash IP | SPI Flash | [spiflash](https://github.com/alexforencich/verilog-spiflash) |
| Ethernet MAC | TEMAC | Triple-Speed ETH | — | — | verilog-ethernet |
| USB | — | — | — | — | ValentyUSB |
| UART | AXI UARTlite | UART IP | — | — | [uart](https://github.com/jamieiles/uart) |

### Migration Decision Tree

```
Does open-source IP exist for this function?
├── YES → Use open-source IP (portable, testable)
│         ├── Does it meet timing? → YES → Done
│         └── No → Add pipeline stages or vendor-specific optimization
└── NO → Use vendor IP
          ├── Is it wrapped in an abstraction layer? → YES → Swap wrapper
          └── No → Create wrapper now (for future portability)
```

---

## Constraint Translation

### Clock Constraints — Cross-Vendor Reference

| Constraint | Xilinx (XDC) | Intel (SDC/QSF) | Lattice (LPF/SDC) | Gowin (CST/SDC) |
|-----------|--------------|-----------------|-------------------|----------------|
| Primary clock | `create_clock -period 10 [get_ports clk]` | `create_clock -period 10 [get_ports clk]` | `create_clock -period 10 [get_ports clk]` | `create_clock -period 10 [get_ports clk]` |
| Generated clock | `create_generated_clock -master_clock ...` | `create_generated_clock -master_clock ...` | `create_generated_clock -master_clock ...` | `create_generated_clock -master_clock ...` |
| False path | `set_false_path -from [get_clocks a] -to [get_clocks b]` | Same | Same | Same |
| Clock groups | `set_clock_groups -asynchronous -group [get_clocks a] -group [get_clocks b]` | Same | Same | Same |
| Input delay | `set_input_delay -clock clk 3 [get_ports data_in]` | Same | Same | Same |
| Output delay | `set_output_delay -clock clk 2 [get_ports data_out]` | Same | Same | Same |
| Multicycle | `set_multicycle_path 2 -setup ...` | Same | Same | Same |

> **SDC is the common denominator.** Xilinx XDC is a superset of SDC. Intel, Lattice, and Gowin all use SDC directly. Write constraints in SDC first, then add Xilinx-specific extensions in XDC.

### Pin Constraints — Vendor-Specific

| Attribute | Xilinx (XDC) | Intel (QSF) | Lattice (LPF) | Gowin (CST) |
|-----------|-------------|------------|---------------|-------------|
| Pin location | `set_property PACKAGE_PIN A1 [get_ports clk]` | `set_location_assignment PIN_A1 -to clk` | `LOCATE COMP "clk" SITE "A1";` | `IO_LOC "clk" 1;` |
| IO standard | `set_property IOSTANDARD LVCMOS33 [get_ports clk]` | `set_instance_assignment -name IO_STANDARD "3.3-V LVCMOS" -to clk` | `IOBUF PORT "clk" IO_TYPE=LVCMOS33;` | `IO_PORT "clk" IO_TYPE=LVCMOS33;` |
| Pull-up | `set_property PULLUP TRUE [get_ports btn]` | `set_instance_assignment -name WEAK_PULL_UP_RESISTOR ON -to btn` | `IOBUF PORT "btn" PULLMODE=UP;` | `IO_PORT "btn" PULL_MODE=UP;` |
| Drive strength | `set_property DRIVE 12 [get_ports led]` | `set_instance_assignment -name CURRENT_STRENGTH_NEW "12MA" -to led` | `IOBUF PORT "led" DRIVE=12;` | `IO_PORT "led" DRIVE=12;` |
| Slew rate | `set_property SLEW SLOW [get_ports led]` | `set_instance_assignment -name SLOW_SLEW_RATE ON -to led` | `IOBUF PORT "led" SLEWRATE=SLOW;` | — |

---

## FuseSoC — Portable Build System

[FuseSoC](https://github.com/olofk/fusesoc) is a package manager and build system for HDL that decouples your RTL from vendor tools.

### Core File

```yaml
# my_soc.core
CAPI=2:
name: mycompany:my_soc
filesets:
  rtl:
    files:
      - rtl/spi_master.v
      - rtl/uart_tx.v
      - rtl/uart_rx.v
      - rtl/top_soc.v
    file_type: verilogSource

  xilinx:
    files:
      - rtl/xilinx/clock_gate_xilinx.v
      - rtl/xilinx/top_xilinx.v
    file_type: verilogSource
    depend:
      - ::xilinx_clock_gate:1.0

  intel:
    files:
      - rtl/intel/clock_gate_intel.v
      - rtl/intel/top_intel.v
    file_type: verilogSource
    depend:
      - ::intel_clock_gate:1.0

  lattice:
    files:
      - rtl/lattice/clock_gate_lattice.v
      - rtl/lattice/top_lattice.v
    file_type: verilogSource

  testbench:
    files:
      - tb/top_soc_tb.v
    file_type: verilogSource

targets:
  arty_a7:
    filesets: [rtl, xilinx, testbench]
    tools:
      vivado:
        part: xc7a35tcsg324-1
        top: top_xilinx
    toplevel: top_xilinx

  de10_nano:
    filesets: [rtl, intel, testbench]
    tools:
      quartus:
        quartus_options: ["--c5gx"]
        top: top_intel
    toplevel: top_intel

  ulx3s:
    filesets: [rtl, lattice, testbench]
    tools:
      trellis:
        top: top_lattice
    toplevel: top_lattice

  sim:
    filesets: [rtl, testbench]
    tools:
      verilator:
        mode: cc
        top: top_soc
    toplevel: top_soc
```

### Build Commands

```bash
# Build for Xilinx Arty A7
fusesoc run --target=arty_a7 mycompany:my_soc

# Build for Intel DE10-Nano
fusesoc run --target=de10_nano mycompany:my_soc

# Build for Lattice ULX3S (open-source flow)
fusesoc run --target=ulx3s mycompany:my_soc

# Run Verilator simulation
fusesoc run --target=sim mycompany:my_soc
```

### Edalize — Tool Abstraction Layer

FuseSoC uses [Edalize](https://github.com/olofk/edalize) under the hood to translate the core file into vendor tool commands:

```
Core File → FuseSoC → Edalize → Vivado / Quartus / Diamond / Yosys / Verilator / ...
```

| Edalize Backend | Vendor / Tool | Notes |
|----------------|-------------|-------|
| `vivado` | Xilinx Vivado | Full project + non-project mode |
| `quartus` | Intel Quartus | Full flow |
| `diamond` | Lattice Diamond | Full flow |
| `trellis` | Yosys + nextpnr-ECP5 | Open-source ECP5 flow |
| `icestorm` | Yosys + nextpnr-iCE40 | Open-source iCE40 flow |
| `vivado` (HLS) | Vivado HLS | C/C++ synthesis |
| `verilator` | Verilator | Simulation only |
| `ghdl` | GHDL | VHDL simulation |
| `icarus` | Icarus Verilog | Simulation only |

---

## Migration Checklist

### Pre-Migration Assessment

| # | Item | Notes |
|---|------|-------|
| 1 | Resource utilization vs. target device | LUTs, FFs, BRAM, DSP, IO — need 20% margin |
| 2 | Clock architecture compatibility | Number of PLLs/MMCMs, frequency ranges |
| 3 | IO standard support | Target device supports all required standards |
| 4 | Transceiver line rates | Target device transceivers support required speeds |
| 5 | Hard IP availability | PCIe, Ethernet MAC, memory controllers |
| 6 | Package/pin compatibility | If reusing PCB, check pinout compatibility |
| 7 | Power supply compatibility | Core voltage, rail requirements |
| 8 | Tool license availability | Vivado vs Quartus vs Diamond vs Gowin EDA |

### RTL Migration Steps

| Step | Action | Effort |
|------|--------|--------|
| 1 | Remove vendor primitives from application logic | High — identify every vendor instantiation |
| 2 | Create abstraction wrappers for clocking, memory, IO | Medium |
| 3 | Replace vendor IP with portable alternatives (or new vendor IP) | High |
| 4 | Translate constraints (XDC → SDC → LPF → CST) | Medium — mostly mechanical |
| 5 | Update build system (or create FuseSoC core file) | Medium |
| 6 | Re-target parameters (BRAM depth, DSP width) | Low |
| 7 | Re-verify functional correctness | Medium — re-run testbench |
| 8 | Close timing on new target | High — different architecture, different critical paths |
| 9 | Re-qualify power and thermal | Medium |
| 10 | Update documentation and BOM | Low |

### Typical Migration Timeline

| Design Size | RTL-Only Migration | RTL + IP Migration | PCB Redesign |
|------------|-------------------|-------------------|-------------|
| Small (< 10K LUTs) | 1–2 weeks | 2–4 weeks | N/A |
| Medium (10K–100K LUTs) | 2–4 weeks | 4–8 weeks | 4–8 weeks |
| Large (100K–1M LUTs) | 4–8 weeks | 8–16 weeks | 8–16 weeks |
| Very Large (> 1M LUTs) | 8–16 weeks | 16–32 weeks | 16–24 weeks |

---

## Common Pitfalls

| Pitfall | Description | Prevention |
|---------|-------------|-----------|
| **BRAM aspect ratio mismatch** | Xilinx BRAM36 = 36Kb; Intel M20K = 20Kb — different width/depth combos | Parameterize all memories; test both mappings |
| **DSP cascade difference** | Xilinx DSP48E2 has cascade chain; Intel DSP varies by family | Avoid relying on cascade behavior; write explicit pipeline |
| **Clock buffer limits** | Xilinx: 24–32 BUFG; Intel: GCLK varies by family; Lattice: limited PLLs | Count clock domains early; merge where possible |
| **Reset behavior** | Xilinx FF: async or sync reset; Intel: ALM has different packing rules with reset | Use sync reset everywhere; test both vendors |
| **IO register packing** | Xilinx IOB=TRUE; Intel FAST_INPUT_REGISTER; different timing | Don't rely on IO register packing; register in fabric with margin |
| **SRL vs distributed RAM** | Xilinx SRL32; Intel MLAB; Lattice EBR — different timing | Use BRAM for large memories; register outputs |
| **Uninitialized memory** | Xilinx BRAM initializes to 0; Intel M20K is undefined | Always use `initial` blocks or `$readmemh` |

---

## Cross-References

| Topic | Article |
|-------|---------|
| Design patterns for portability | [Design Patterns](../04_hdl_and_synthesis/design_patterns.md) |
| Vendor-specific synthesis attributes | [Vendor Pragmas](../04_hdl_and_synthesis/vendor_pragmas.md) |
| IP packaging & reuse (FuseSoC) | [IP Reuse](../06_ip_and_cores/ip_reuse/README.md) |
| FPGA prototyping (ASIC→FPGA) | [FPGA Prototyping](fpga_prototyping.md) |
| Constraint quick reference | [Constraint Quickref](../14_references/constraint_quickref.md) |
| Open-source flow | [Open-Source Flow](../13_toolchains/open_source_flow.md) |
