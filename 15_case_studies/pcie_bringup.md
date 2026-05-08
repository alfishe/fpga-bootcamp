[← 15 Case Studies Home](README.md) · [← Project Home](../../README.md)

# PCIe Link Training Debug — LTSSM, Equalization, and Endpoint Bring-Up

## Overview

PCI Express (PCIe) is the backbone of high-bandwidth FPGA-to-Host communication. Before a Linux host can enumerate the FPGA as an endpoint (via `lspci`), the PCIe hard block (e.g., Xilinx PCIe Gen3/Gen4 Subsystem or Intel P-Tile) must successfully negotiate a link with the root complex. This negotiation is governed by the Link Training and Status State Machine (LTSSM). Understanding the LTSSM is critical, because if the link fails to reach the **L0 (active)** state, the FPGA simply does not exist to the host OS. Debugging this requires interrogating the LTSSM to find out exactly where the handshake failed.

## Architecture / The LTSSM Sequence

The LTSSM is a complex state machine, but physical link debugging almost always centers around the first four major states. 

```mermaid
graph TD
    A[Reset / PERST# Deasserted] --> B[Detect]
    B -->|Termination Found| C[Polling]
    B -->|No Receiver| B
    C -->|Bit/Symbol Lock| D[Configuration]
    C -->|No Lock| E[Polling.Compliance]
    D -->|Lane & Speed Agreed| F[L0: Link Active]
    D -->|Negotiation Failed| C
    F -->|Errors/Equalization| G[Recovery]
    G -->|Fixed| F
    G -->|Failed| B
    
    style B fill:#e8f4fd,stroke:#2196f3
    style C fill:#fff9c4,stroke:#f9a825
    style D fill:#fff9c4,stroke:#f9a825
    style E fill:#ffcdd2,stroke:#f44336
    style F fill:#c8e6c9,stroke:#4caf50
```

1.  **Detect:** The FPGA transmitter checks for a receiver on the other end by detecting a common-mode impedance. If stuck here, the physical electrical connection is broken.
2.  **Polling:** The transceivers send out TS1/TS2 (Training Sequences) to achieve bit-lock and symbol-lock. The link speed is locked to Gen1 (2.5 GT/s) here.
3.  **Configuration:** The link partner and FPGA negotiate the link width (e.g., x1, x4, x8) and assign lane numbers. 
4.  **L0 (Active):** The link is up at Gen1 speed. If higher speeds (Gen2/3/4) are supported, the link immediately drops into **Recovery** to negotiate the speed upgrade and perform equalization.

## Vendor Context & Cross-Platform Comparison

| Debug Tooling | Xilinx Vivado (Integrated Block for PCIe) | Intel Quartus (L-/H-/P-Tile) |
|---|---|---|
| **State Visibility** | `cfg_ltssm_state[5:0]` port directly exposes the state. Viewable via ILA. | EMIF/PCIe Debug Toolkit provides a GUI showing LTSSM transitions. |
| **PHY Debug** | The JTAG-to-AXI master can interrogate the PCIe DRP (Dynamic Reconfiguration Port). | SignalTap can probe the core, and Toolkit provides eye diagrams. |
| **Common IP Types** | XDMA (Memory Mapped) or QDMA (Queue-based). | Avalon-MM PCIe Hard IP or P-Tile Avalon-ST. |

## Pitfalls & Common Mistakes

### 1. The PERST# Timing Violation
The host PC motherboard asserts a physical reset signal (`PERST#`) across the PCIe slot. FPGAs often boot slower than the host PC expects.

> [!WARNING]
> **PCIe Specification Limit:** An endpoint must be ready to link train within **100 ms** of power rails stabilizing and `PERST#` deasserting.

**Bad Design:**
Loading the FPGA bitstream from a slow SPI flash memory (e.g., standard x1 SPI) takes 500ms. The host PC boots, asserts `PERST#`, gives up waiting for the FPGA, and drops the PCIe slot before the FPGA is even configured.

**Good Design:**
Use QSPI (Quad SPI) flash or tandem configuration (where the PCIe hard block is configured first, and the rest of the fabric loads later) to meet the 100ms requirement.

### 2. Missing REFCLK Constraints
The 100 MHz PCIe reference clock (`REFCLK`) is provided by the motherboard. It must be routed to dedicated transceiver clock pins (MGTREFCLK).

**Bad Code:**
Routing the REFCLK through standard fabric logic to reach the PCIe IP. This adds massive jitter and guarantees Polling failure.

**Good Code (Xilinx XDC):**
```tcl
# Instantiate a dedicated IBUFDS_GTE to route REFCLK directly into the transceiver
set_property LOC IBUFDS_GTE4_X0Y0 [get_cells refclk_ibuf]
create_clock -name sys_clk -period 10.000 [get_ports sys_clk_p]
```

### 3. Lane Reversal (Tx/Rx Swaps)
Sometimes the PCB designer routes Lane 0 of the host to Lane 3 of the FPGA to make the layout cleaner. While the PCIe spec allows for automatic Lane Reversal, not all FPGA IP configurations enable it by default. If it is disabled, the link gets stuck in **Configuration**.

## API / Interface Reference: Debugging the Link

If the card is plugged in but `lspci` shows nothing, you must debug from the FPGA side. 

### 1. Checking the Host (Linux)
```bash
# Check if the host sees the device at all
lspci -vd 10ee:  # 10ee is the Xilinx Vendor ID

# If it shows up but misbehaves, check the kernel ring buffer for AER (Advanced Error Reporting) logs
dmesg | grep PCIe
```

### 2. Checking the FPGA (Vivado ILA)
You should connect an Integrated Logic Analyzer (ILA) to the PCIe IP core's `cfg_ltssm_state` bus.

```tcl
/* Vivado LTSSM Decoding (Gen3/Gen4 cores) */
0x00 : Detect.Quiet
0x01 : Detect.Active
0x02 : Polling.Active
0x03 : Polling.Compliance
0x04 : Polling.Configuration
0x10 : L0 (Link Up!)
0x11 : Recovery.RcvrLock
```
*If the ILA shows the state bouncing between `0x11` (Recovery) and `0x10` (L0), the link has marginal signal integrity and is trying to renegotiate equalization.* 

## When to Use Protocol Analyzers vs ILA

| Criterion | FPGA Internal Logic Analyzer (ILA) | Hardware PCIe Protocol Analyzer (e.g., LeCroy) |
|---|---|---|
| **Cost** | Free (uses FPGA fabric resources) | Extremely expensive ($10k - $50k+) |
| **Visibility** | Perfect visibility into LTSSM states and AXI bus transactions inside the FPGA. | Perfect visibility into the analog physical layer and TS1/TS2 ordered sets on the wire. |
| **When to use** | 90% of debugging: checking if resets are correct, checking if link reaches L0, debugging DMA logic. | The last 10%: obscure signal integrity issues, interoperability bugs with specific host chipsets, or debugging ASPM (power management) failures. |

## PCIe Configuration Space Debug

Even after the link reaches L0, the host must successfully read the FPGA's configuration space:

```bash
# Check if device appears in lspci
lspci -nn | grep 10ee   # Xilinx vendor ID
lspci -nn | grep 1172   # Intel/Altera vendor ID

# Detailed device info
lspci -vvv -s 01:00.0   # Replace with actual bus:dev.func

# Read configuration space directly
setpci -s 01:00.0 0.l   # Vendor ID + Device ID (offset 0x00)
setpci -s 01:00.0 8.l   # Revision ID + Class Code (offset 0x08)
setpci -s 01:00.0 10.l  # BAR0 (offset 0x10)

# Check for AER (Advanced Error Reporting) errors
grep -i pcie /proc/interrupts
dmesg | grep -i "AER\|pcieport"
```

### Common Configuration Space Problems

| Symptom | Cause | Fix |
|---|---|---|
| Device appears but BAR shows 0x00000000 | BAR not sized by BIOS | Add `pci=realloc` to kernel boot args |
| Device appears but wrong class code | IP misconfiguration | Check PCIe IP core class code setting |
| `lspci` shows “Unassigned class” | Subsystem ID not set | Configure subsystem_vendor/subsystem_device in IP core |
| Device disappears after warm reboot | FPGA not re-configured | Add bitstream reload in U-Boot/BIOS |

---

## PCIe DMA Debugging

Once the link is up and BARs are assigned, the next step is DMA:

### XDMA (Xilinx DMA)
```bash
# Load XDMA driver
modprobe xdma

# Check if DMA engine is accessible
ls /dev/xdma*

# Simple DMA test
dma_to_device -d /dev/xdma0_h2c_0 -s 4096 -c 1
dma_from_device -d /dev/xdma0_c2h_0 -s 4096 -c 1
```

### QDMA (Queue-based DMA)
```bash
# Load QDMA driver
modprobe qdma-pf
modprobe qdma-vf

# Configure queues
dma-ctl qdma0 q add idx 0 mode st dir h2c
qdma0-q0 --data test.bin
```

### Common DMA Problems

| Symptom | Cause | Fix |
|---|---|---|
| DMA hangs (no completion) | Descriptor ring misconfigured | Check descriptor table alignment (4 KB aligned) |
| Wrong data received | Byte ordering / endianness | Check `DMA_DATA_WIDTH` and byte-swap settings |
| DMA works on one host but not another | IOMMU / IOTLB issues | Add `intel_iommu=off` to kernel args; check IOMMU mapping |
| Completion timeout | PCIe completion timeout on host | Increase `pcie_completion_timeout` in kernel parameters |

---

## Tandem Configuration for PCIe Boot

For designs where the FPGA must meet the 100 ms PERST# requirement:

### Stage 1 (Tandem Boot)
```
1. Minimal bitstream loads first (~10 ms)
   - Contains ONLY PCIe hard block + clocking
   - Link trains at Gen1 immediately
   - Host sees the device and enumerates it

2. Stage 2 (Full bitstream loads via PCIe DMA)
   - Host driver triggers full bitstream download
   - FPGA reconfigures remaining fabric via ICAP
   - DMA engines become active
```

| Device | Tandem IP | Stage 1 Config Time | Stage 2 Method |
|---|---|---|---|
| UltraScale+ | Tandem PCIe (PG238) | ~15 ms | ICAP write from host driver |
| Zynq MPSoC | PCAP via FSBL | ~30 ms (FSBL loads PL) | PCAP from PMU firmware |
| Agilex 7 | P-Tile self-test | ~20 ms | SDM via host mailbox |

---

## PCIe Power Management Debug

| ASPM State | Latency | Power Savings | Common Problem |
|---|---|---|---|
| **L0** | Active | 0 | None (fully operational) |
| **L0s** | <100 ns | ~50 mW per lane | RX detect failures on wake; check clock recovery |
| **L1** | ~1–10 µs | ~200 mW total | Entry requires both sides to agree; stuck in L1 if one side can't exit |
| **L1.2** | ~100 µs | ~500 mW | Requires CLKREQ# signal; check PCB routing |

**Debug tip:** If the link drops after being idle, disable ASPM with `pcie_aspm=off` in kernel boot args. If the problem goes away, it's an ASPM issue.

---

## Cross-References

| Topic | Article |
|---|---|
| Transceiver architecture | [Transceiver Basics](../06_ip_and_cores/transceivers/transceiver_basics.md) |
| Board bring-up sequence | [Bring-Up Checklist](bring_up_checklist.md) |
| Boot architecture & timing | [Boot Architecture](../02_architecture/soc/boot_architecture.md) |
| Constraint reference | [Constraint Quickref](../14_references/constraint_quickref.md) |
| DDR bring-up (often concurrent with PCIe) | [Debugging DDR](debugging_ddr.md) |

---

## References

- [PCI Express Base Specification Revision 4.0](https://pcisig.com/)
- [Xilinx PG195: PCIe Gen3 Subsystem Product Guide](https://docs.xilinx.com/)
- [Xilinx PG238: Tandem Configuration](https://docs.xilinx.com/)
- [Intel L-Tile/H-Tile/P-Tile PCIe User Guides](https://www.intel.com/)
- [Xilinx PG195: XDMA/QDMA Product Guide](https://docs.xilinx.com/)
