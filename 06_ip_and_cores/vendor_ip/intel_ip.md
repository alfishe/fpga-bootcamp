[← 06 Ip And Cores Home](../README.md) · [← Vendor Ip Home](README.md) · [← Project Home](../../../README.md)

# Intel FPGA IP Ecosystem — Platform Designer (Qsys)

Intel's IP integration flow centers on Platform Designer (formerly Qsys), a system-integration tool that connects IP components via Avalon buses and generates the interconnect fabric automatically. It's the Intel equivalent of Vivado IP Integrator.

---

## Platform Designer Architecture

```
IP Catalog (500+ components)
    │
    ▼
Platform Designer GUI
    │
    ├─ Add components from catalog
    ├─ Connect via Avalon-MM / Avalon-ST / Conduit
    ├─ Configure parameters (GUI forms)
    ├─ Set address maps (auto-assigned)
    └─ Generate → System HDL + interconnect fabric
    │
    ▼
Quartus Compilation
```

---

## Component Library Highlights

| Category | Key IPs | Notes |
|---|---|---|
| **Embedded CPUs** | Nios II (3 variants), Nios V (RISC-V) | Soft CPUs for fabric |
| **Memory Controllers** | DDR3/4/L, QDR II/IV, RLDRAM 3, HMC, HBM2 | Intel's memory controller IP is industry-leading |
| **Ethernet** | Triple-Speed (1G), 10G/25G/100G MAC, TSN | Time-Sensitive Networking for industrial |
| **PCI Express** | PCIe Gen1–Gen5, SR-IOV, CXL | Hard IP + soft wrapper for Avalon-MM/ST |
| **Serial** | JESD204B/C, CPRI, Interlaken | Telecom/datacom focus |
| **Video** | Video and Image Processing Suite, HDMI, DisplayPort | Good for machine vision |
| **DSP** | FFT, FIR, NCO, CIC, CORDIC | Standard DSP building blocks |
| **Security** | AES, SHA, ECC, TRNG | For secure boot / bitstream encryption |

---

## Avalon Interface Types

| Interface | Signal Group | Use Case |
|---|---|---|
| **Avalon-MM** | address, read, write, readdata, writedata, waitrequest | Register access, memory-mapped DMA |
| **Avalon-ST** | data, valid, ready, channel, error | Streaming data (packets, DSP) |
| **Avalon-TC** | (memory-mapped with burst) | Burst memory transfers |
| **Conduit** | Arbitrary signals | Export to FPGA top-level pins |
| **Clock/Reset** | clk, reset, reset_req | Clock and reset distribution |
| **Interrupt** | irq | Connect to HPS/Nios interrupt controller |

---

## Address Map Auto-Assignment

Platform Designer auto-assigns addresses to Avalon-MM slaves:

```
0x0000_0000  Nios II/f reset vector
0x0000_1000  On-Chip RAM
0x0000_2000  JTAG UART
0x0000_2010  System Timer
0x0000_2020  PIO (LEDs)
0x0000_2030  PIO (Buttons)
0x1000_0000  DDR3 SDRAM
```

Manual override possible but rarely needed.

---

## Tcl Scripting

For CI and repeatability, everything in Platform Designer is scriptable:

```tcl
# Create a new system
set qsys_name my_system
create_qsys_system $qsys_name

# Add Nios II processor
add_instance nios2 altera_nios2_gen2
set_instance_parameter nios2 {core_type} {Nios II/f}

# Add on-chip memory
add_instance onchip_ram altera_avalon_onchip_memory2
set_instance_parameter onchip_ram {memorySize} {65536.0}

# Connect clock and reset
add_connection nios2.clk onchip_ram.clk
add_connection nios2.reset onchip_ram.reset

# Connect data master to slave
add_connection nios2.data_master onchip_ram.s1

# Save and generate
save_qsys_system $qsys_name
run_qsys_generation $qsys_name
```

---

## IP Catalog by Category

### Clocking & PLLs

| IP | Description | Families | Key Parameters |
|---|---|---|---|
| **PLL** | Standard PLL with C0–C9 outputs | All | Multiply/divide 1–512, phase shift per output |
| **Fractional PLL** | Fractional-N synthesis (fine freq resolution) | Arria 10+, Cyclone V | Allows non-integer multiply/divide ratios |
| **IO-PLL** | Per-bank PLL for I/O serialization | Agilex 7 | Independent per I/O lane |
| **fPLL** | Fractional PLL for transceiver refclk gen | Stratix 10, Agilex | Drives QPLL/CPLL for multi-protocol support |

### Memory Controllers

| IP | Description | Interfaces | Max Rate |
|---|---|---|---|
| **EMIF (DDR3)** | Hard memory controller PHY | Avalon-MM | 800 MHz (DDR3-1600) |
| **EMIF (DDR4)** | Hard memory controller with ECC | Avalon-MM + Avalon-ST | 3200 Mbps (DDR4-3200) |
| **EMIF (QDR-IV)** | Quad Data Rate SRAM controller | Avalon-MM | 1066 MHz |
| **EMIF (RLDRAM 3)** | Reduced-latency DRAM controller | Avalon-MM | 1200 MHz |
| **HBM2 Controller** | High Bandwidth Memory (in-package) | Avalon-MM | 256 GB/s (8-hi stack) |
| **On-Chip Memory** | M10K/M20K-based RAM/ROM | Avalon-MM | Up to 1.4 Mb (device-dependent) |

### Processors

| IP | ISA | LUTs | fmax | Use Case |
|---|---|---|---|---|
| **Nios II/e** | 32-bit RISC | ~700 | 80 MHz | Smallest footprint, basic control |
| **Nios II/s** | 32-bit RISC | ~1,200 | 120 MHz | 5-stage pipeline, moderate perf |
| **Nios II/f** | 32-bit RISC | ~1,800 | 200+ MHz | 6-stage pipeline, caches, branch prediction |
| **Nios V/m** | RV32IMC | ~1,200 | 150+ MHz | RISC-V replacement for Nios II |
| **Nios V/g** | RV32IMC + FPU | ~2,500 | 150+ MHz | RISC-V with hardware FPU |

### Ethernet

| IP | Speed | Interface | Features |
|---|---|---|---|
| **Triple-Speed Ethernet** | 10/100/1000 Mbps | Avalon-ST + MDIO | MII/GMII/RGMII/SGMII |
| **Low Latency Ethernet 10G MAC** | 10 Gbps | Avalon-ST | XFI/DXAUI, PTP timestamping |
| **25G Ethernet MAC** | 25.78 Gbps | Avalon-ST | RS-FEC (Clause 74), PTP |
| **100G Ethernet MAC+PCS** | 103.1 Gbps | Avalon-ST (4×25G) | CAUI-4, RS-FEC (Clause 91) |
| **TSN (Time-Sensitive Networking)** | 1 Gbps | Avalon-ST + Avalon-MM | 802.1Qbv (EST), 802.1AS (gPTP), 802.1Qci (PSFP) |

### PCI Express

| IP | Gen | Hard/Soft | Interface | Features |
|---|---|---|---|---|
| **Avalon-MM DMA** | Gen1–Gen3 | Hard | Avalon-MM | Simple register access + DMA |
| **Avalon-ST** | Gen1–Gen3 | Hard | Avalon-ST | Packet-level (TLP) access |
| **P-Tile** | Gen3–Gen5 | Hard IP tile | Avalon-ST | SR-IOV, CXL 1.1, up to ×16 |
| **F-Tile** | Gen3–Gen4 | Hard IP tile | Avalon-ST | Multiple protocols per tile |
| **R-Tile** | Gen5 ×16 | Hard IP tile | Avalon-ST | Agilex 7 only, 32 GT/s |

### DSP

| IP | Function | Data Width | Latency (typical) |
|---|---|---|---|
| **FFT** | Radix-2/4 FFT/IFFT | 8–32 bit fixed/float | 200+ cycles |
| **FIR II** | Programmable FIR filter | Up to 32 bit | 6–14 cycles |
| **NCO** | Numerically Controlled Oscillator | 8–32 bit | 3 cycles |
| **CIC** | Cascaded Integrator-Comb | Up to 32 bit | Variable (decimation-dependent) |
| **CORDIC** | Coordinate Rotation | 8–48 bit | ~20 cycles |
| **Floating-Point** | Add/Mul/Div/Sort | 32/64-bit IEEE 754 | 6–35 cycles |

---

## Tcl Generation Commands

Automate IP instantiation for CI/CD flows:

```tcl
# Create PLL IP
create_ip -name altera_pll -module_name my_pll
set_property -dict [list \
  CONFIG.reference_clock_frequency {50.0 MHz} \
  CONFIG.number_of_clocks {3} \
  CONFIG.output_clock_frequency0 {100.0 MHz} \
  CONFIG.output_clock_frequency1 {200.0 MHz} \
  CONFIG.output_clock_frequency2 {25.0 MHz}] [get_ips my_pll]
generate_target all [get_ips my_pll]

# Create EMIF DDR4 IP
create_ip -name altera_emif -module_name ddr4_ctrl
set_property -dict [list \
  CONFIG.mem_mem_type {DDR4} \
  CONFIG.mem_speedbin {DDR4-2400} \
  CONFIG.mem_density {8G} \
  CONFIG.interface_width {64}] [get_ips ddr4_ctrl]
generate_target all [get_ips ddr4_ctrl]
```

---

## IP Licensing Tiers

| Tier | Cost | Includes | Typical Users |
|---|---|---|---|
| **Free (Quartus Lite)** | $0 | Nios II, basic memory, simple DSP, basic Ethernet | Hobbyists, students, small companies |
| **Standard** | ~$1,000–$3,000/yr | 10G/25G/100G Ethernet, PCIe Gen3, advanced DSP | Mid-size companies, industrial |
| **Pro** | ~$5,000–$15,000/yr | P-Tile/F-Tile PCIe Gen4/5, HBM2, TSN, CXL | Enterprise, data center, defense |

---

## Best Practices

1. **Use Avalon-ST for streaming data paths** — zero overhead, clock-cycle-accurate
2. **Tcl-generate your Qsys system** — GUI-dragging is not reproducible
3. **Don't fragment address space** — group peripherals by function
4. **Test with Nios II before HPS** — Nios II brings up faster for initial proto
5. **Use EMIF debug toolkit for DDR issues** — it provides per-byte-lane eye diagrams and margin analysis
6. **Generate IP from Tcl scripts** — `create_ip` + `generate_target` enables CI/CD without GUI

---

## Cross-References

| Topic | Article |
|---|---|
| Transceiver architecture | [Transceiver Basics](../transceivers/transceiver_basics.md) |
| Xilinx IP comparison | [Xilinx IP](xilinx_ip.md) |
| Lattice IP comparison | [Lattice IP](lattice_ip.md) |
| Microchip IP comparison | [Microchip IP](microchip_ip.md) |
| Open-source alternatives | [Open-Source IP](../open_source_ip/README.md) |

---

## References

- Intel Quartus Prime Handbook Vol 1: Platform Designer
- Intel AN 794: Component Interface Tcl Reference
- Intel IP Catalog Documentation (online)
- Avalon Interface Specifications (Intel)
