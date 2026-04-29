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

## Best Practices

1. **Use Avalon-ST for streaming data paths** — zero overhead, clock-cycle-accurate
2. **Tcl-generate your Qsys system** — GUI-dragging is not reproducible
3. **Don't fragment address space** — group peripherals by function
4. **Test with Nios II before HPS** — Nios II brings up faster for initial proto

---

## References

- Intel Quartus Prime Handbook Vol 1: Platform Designer
- Intel AN 794: Component Interface Tcl Reference
- Avalon Interface Specifications (Intel)
