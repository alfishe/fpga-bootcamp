[← 06 Ip And Cores Home](../README.md) · [← Vendor Ip Home](README.md) · [← Project Home](../../../README.md)

# Xilinx IP Ecosystem — Vivado IP Integrator

Vivado IP Integrator (IPI) is Xilinx's block-design tool for connecting IP cores via AXI buses. It's the most mature IP ecosystem in the FPGA industry, with 200+ free IPs, IP-XACT packaging, and deep integration with the Vivado toolchain.

---

## IP Integrator Architecture

```
Vivado IP Catalog (200+ cores)
    │
    ▼
Block Design (.bd)
    │
    ├─ Add IP from catalog (drag-and-drop or Tcl)
    ├─ Connect via AXI4 / AXI4-Lite / AXI4-Stream
    ├─ Configure via IP customization GUI
    ├─ Auto-assign address maps
    ├─ Run Connection Automation (one-click wiring)
    └─ Generate → HDL wrapper + constraints + simulation
    │
    ▼
Synthesis → Implementation → Bitstream
```

---

## AXI Bus Types in Xilinx IP

| Bus | Width | Use Case | Example IPs |
|---|---|---|---|
| **AXI4** | 32–1024 bit | High-bandwidth memory-mapped (bursts) | DDR MIG, DMA/Bridge, Video Frame Buffer |
| **AXI4-Lite** | 32 bit | Low-bandwidth register access (no bursts) | GPIO, UART, I2C, SPI, Timer, Interrupt Controller |
| **AXI4-Stream** | 8–1024 bit | Unidirectional streaming (no address) | Video processing, FFT, DDS, Ethernet MAC, JESD204B |

**Xilinx differentiator**: AXI4-Stream is the backbone of Xilinx DSP pipelines. The entire RF Data Converter, AI Engine, and Video IP suites use AXI4-Stream exclusively.

---

## Key IP Categories

| Category | Key IPs | Notes |
|---|---|---|
| **Embedded CPUs** | MicroBlaze (soft), MicroBlaze V (RISC-V soft), Zynq PS (hard Cortex-A/R) | MicroBlaze is deeply integrated with AXI |
| **Memory Controllers** | MIG (DDR3/4/L), HBM Controller, RLDRAM 3, QDR II+ | MIG is the most configurable DDR controller in the industry |
| **Ethernet** | 1G/10G/25G/40G/100G MAC, MRMAC (multi-rate), TSN | Hard MACs on Zynq MPSoC and Versal |
| **PCI Express** | PCIe Gen1–Gen5, AXI Memory Mapped Bridge, AXI Stream Bridge, DMA/Bridge for PCIe (XDMA), QDMA | Integrated DMA engines |
| **Serial** | JESD204B/C (for RF data converters), Aurora (lightweight serial), Interlaken | Telecom/datacom/RF |
| **Video** | Video Mixer, Video Timing Controller, HDMI, DisplayPort, MIPI CSI/DSI | Strongest video IP ecosystem among vendors |
| **DSP** | FFT (pipelined/radix-2/burst), DDS Compiler, FIR Compiler, CIC Compiler, Cordic | Tuned for DSP48 slices |
| **AI Engine** | AIE Graph, AIE Kernel (Versal only) | Vector processors for ML/DSP |
| **RF** | RF Data Converter, RFSoC DDC/DUC (Versal/Zynq RFSoC only) | Direct-RF sampling integration |
| **Security** | AES-GCM, HMAC, TRNG, RSA, ECC, Secure Boot Monitor (Versal) | Integrated with bitstream encryption |

---

## Connection Automation — The Killer Feature

IPI's *Connection Automation* is what sets it apart from Intel's Platform Designer:

1. Drop a Zynq Processing System and a DDR MIG into a block design
2. Run Connection Automation
3. IPI auto-connects: clock, reset, AXI master→slave, interrupt, M_AXI_HPM0→DDR
4. Result: a working hardware platform in 30 seconds

```tcl
# Equivalent Tcl (what Connection Automation generates)
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config { \
    Clk_master {/zynq_ps/pl_clk0 (100 MHz)} \
    Clk_slave {/mig_7series/ui_clk (200 MHz)} \
    Clk_xbar {/axi_interconnect_0/ACLK (100 MHz)} \
    Master {/zynq_ps/M_AXI_HPM0} \
    Slave {/mig_7series/S_AXI} \
    intc_ip {/zynq_ps/IRQ_F2P} \
    master_apc {Auto} }
```

---

## IP-XACT Packaging

Vivado IP cores are packaged in IEEE 1685 IP-XACT format. This means:

- **Metadata-rich**: each IP includes ports, parameters, interfaces, memory maps, and constraints
- **Version-controlled**: IP can be revision-tracked
- **Cross-tool compatible** (theoretically): IP-XACT is an IEEE standard
- **Custom IP packaging**: Package your own RTL as IP-XACT for reuse in IPI

```tcl
# Package a custom RTL module as IP-XACT
ipx::package_project -root_dir ./my_ip -vendor mycompany -library ip -taxonomy /UserIP
ipx::add_bus_interface S_AXI -bus_type AXI4Lite -mode slave
ipx::save_core
```

---

## Zynq Processing System IP

The Zynq PS IP is the most important single IP in Vivado's catalog:

| PS Feature | Configuration |
|---|---|
| CPU | Cortex-A53/A9/R5 (select clocks, enable/disable cores) |
| DDR | DDR3/4/L, DDR I/O voltage, ECC enable |
| Peripherals | UART, SPI, I2C, CAN, GPIO, SD, USB, GigE, QSPI, NAND |
| AXI Master Ports | HPM0/1 (high-performance), HPC0/1 (coherent on MPSoC) |
| AXI Slave Ports | HPS-to-FPGA bridge for CPU→FPGA access |
| Interrupts | PL→PS interrupts (IRQ_F2P), 16 lines |
| Clocks | PL Fabric Clocks (configurable from PS PLLs) |
| FPGA Config | PCAP (processor configuration access port) for partial reconfig |

---

## Block Design Tcl Scripting

For reproducible builds and CI:

```tcl
# Create block design
create_bd_design "my_design"

# Add Zynq PS
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 zynq_ps
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e -config {apply_board_preset "1"}

# Add AXI GPIO
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_led
set_property -dict [list CONFIG.C_GPIO_WIDTH {4} CONFIG.C_ALL_OUTPUTS {1}] [get_bd_cells axi_gpio_led]

# Connect via AXI SmartConnect
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 smartconnect_0
connect_bd_intf_net [get_bd_intf_pins zynq_ps/M_AXI_HPM0_LPD] [get_bd_intf_pins smartconnect_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins smartconnect_0/M00_AXI] [get_bd_intf_pins axi_gpio_led/S_AXI]

# Connect clocks
connect_bd_net [get_bd_pins zynq_ps/pl_clk0] [get_bd_pins smartconnect_0/aclk]

# Auto-assign addresses
assign_bd_address

# Generate wrapper and output products
make_wrapper -files [get_files *.bd] -top
```

---

## Best Practices

1. **Always Tcl-script your block design** — GUI-built .bd files are fragile across Vivado versions. Tcl is version-agnostic and CI-friendly.
2. **Use AXI4-Stream for DSP pipelines, AXI4-Lite for control** — separating data path (stream) from control path (Lite) keeps designs clean.
3. **Run Connection Automation first, then customize** — let the tool wire 90%, then tweak the remaining 10%.
4. **Version-lock IP in your project** — use `set_property IP_REPO_PATHS` instead of relying on Vivado's default IP catalog path.
5. **Use AXI SmartConnect, not AXI Interconnect** — SmartConnect is the modern replacement with better QoD (quality of design) and lower latency.
6. **Export hardware platform (.xsa) for Vitis** — the .xsa file contains the full hardware description for software development.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Clock not connected** | IP greyed out in block design | Check all clk pins; IPI won't let you generate with unconnected clocks |
| **Address collision** | `assign_bd_address` fails | Two slaves at same address — manually adjust in Address Editor |
| **AXI protocol mismatch** | Validation error | AXI4 master can't connect to AXI4-Lite slave directly — use AXI Protocol Converter |
| **IP version mismatch** | "IP is locked" error | Upgrade IP to current Vivado version: `upgrade_ip [get_ips *]` or Tcl: `upgrade_bd_cells` |
| **Reset polarity wrong** | Nothing works after config | Xilinx uses active-low reset (`peripheral_aresetn`); check your custom IP polarity |

---

## References

- [Vivado Design Suite User Guide: Designing IP Subsystems Using IP Integrator (UG994)](https://docs.amd.com/r/en-US/ug994-vivado-ip-subsystems)
- [Vivado Design Suite User Guide: Creating and Packaging Custom IP (UG1118)](https://docs.amd.com/r/en-US/ug1118-vivado-creating-packaging-custom-ip)
- [AXI Reference Guide (UG1037)](https://docs.amd.com/r/en-US/ug1037-vivado-axi-reference-guide)
- [IP-XACT IEEE 1685 Standard](https://ieeexplore.ieee.org/document/6998910)
- [Zynq-7000 SoC Technical Reference Manual (UG585)](https://docs.amd.com/r/en-US/ug585-zynq-7000-trm)
