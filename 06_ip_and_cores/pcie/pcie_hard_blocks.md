[← 06 IP & Cores Home](../README.md) · [← PCIe Home](README.md) · [← Project Home](../../../README.md)

# Integrated PCIe Hard Blocks — Endpoint & Root Port

PCI Express (PCIe) is the primary high-speed interconnect between FPGAs and host CPUs. Modern FPGAs integrate hardened PCIe controllers directly in silicon — no soft IP required. This article compares the integrated PCIe blocks across vendors and generations.

---

## Why Hardened PCIe Blocks Exist

A soft-PCIe implementation (in LUTs) would consume ~50,000 LUTs and top out at Gen1 speeds (2.5 GT/s). Hardened blocks:
- Leap directly to Gen3 (8 GT/s), Gen4 (16 GT/s), or Gen5 (32 GT/s)
- Include the entire **Physical Layer (PHY)**, **Data Link Layer**, and **Transaction Layer**
- Consume zero fabric LUTs (just a few for the AXI/Avalon bridge interface)
- Provide multi-function support with up to 4 Physical Functions (PFs) and hundreds of Virtual Functions (VFs)

---

## PCIe Block Architecture

```
┌──────────── Host CPU ────────────┐
│  Root Complex                    │
│    └── PCIe Root Port            │
└──────────┬───────────────────────┘
           │ PCIe Link (1–16 lanes)
           ▼
┌────────── FPGA PCIe Hard Block ───────────────────────┐
│                                                        │
│  ┌── PHY ──┐  ┌── Data Link ──┐  ┌── Transaction ──┐  │
│  │ SerDes   │  │ DLLP (ACK/  │  │ TLP routing,    │  │
│  │ PLL/CDR  │──│ NAK, flow   │──│ BAR matching,   │──┼──→ AXI4 / Avalon-MM
│  │ 8b/10b   │  │ control)    │  │ MSI/MSI-X       │  │    (fabric interface)
│  │ 128b/130b│  └─────────────┘  └─────────────────┘  │
│  └──────────┘                                         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

All three layers are hardened. The fabric interface (AXI4 for Xilinx/Microchip, Avalon-MM for Intel) is the only part exposed to user logic.

---

## Cross-Vendor Comparison

| Feature | Xilinx 7-series | Xilinx US+ | Xilinx Versal | Intel Arria 10 | Intel Agilex 7 | Microchip PolarFire |
|---|---|---|---|---|---|---|
| **Max Gen** | Gen2 (5 GT/s) | Gen4 (16 GT/s) | Gen5 (32 GT/s) | Gen3 (8 GT/s) | Gen5 (32 GT/s) | Gen2 (5 GT/s) |
| **Max lanes** | ×8 (Gen2), ×4 (Gen1) | ×16 | ×16 (CPM5) | ×8 | ×16 | ×4 |
| **Endpoint** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Root Port** | Yes (Zynq) | Yes | Yes | Yes | Yes | No |
| **Multi-function** | Yes (up to 4 PF) | Yes (4 PF, 252 VF) | Yes (4 PF, 252 VF) | Yes (4 PF) | Yes (4 PF, 2k VF) | Single function |
| **Fabric interface** | AXI4-Stream | AXI4-MM | AXI4-MM (NoC) | Avalon-MM | Avalon-MM / AXI4 | AXI4-MM |
| **Integrated DMA** | No (separate XDMA IP) | Yes (QDMA) | Yes (QDMA) | No (separate DMA IP) | Yes (MSI-X DMA) | No |
| **SR-IOV** | No (7-series) | Yes | Yes | No (Arria 10) | Yes | No |
| **CXL support** | No | No | Yes (CXL 1.1/2.0) | No | Yes (CXL 1.1) | No |

---

## Endpoint vs Root Port

| Role | Endpoint | Root Port |
|---|---|---|
| **Who initiates?** | Host CPU enumerates the endpoint | Root port enumerates downstream devices |
| **Typical use** | FPGA accelerator card connected to a server | FPGA acts as the host (e.g., Zynq MPSoC with PCIe root to connect an NVMe SSD) |
| **BARs** | Exposes BARs to the host for MMIO/DMA | Does not expose BARs; configures downstream BARs |
| **MSI/MSI-X** | Sends interrupts to host | Receives interrupts from downstream devices |
| **FPGA example** | Alveo accelerator card | Zynq UltraScale+ PS-PCIe root port connecting to an NVMe drive |

> **Most FPGA designs use Endpoint mode.** Root Port is primarily for SoC FPGAs where the ARM CPU needs to connect to PCIe peripherals (NVMe SSDs, network cards, GPUs).

---

## Gen-by-Gen: What Changes

| Gen | Data Rate (per lane) | Encoding | ×1 BW | ×16 BW | Key Change |
|---|---|---|---|---|---|
| **Gen1** | 2.5 GT/s | 8b/10b | 250 MB/s | 4 GB/s | Baseline |
| **Gen2** | 5.0 GT/s | 8b/10b | 500 MB/s | 8 GB/s | De-emphasis, faster CDR |
| **Gen3** | 8.0 GT/s | 128b/130b | ~1 GB/s | ~16 GB/s | Scrambling, equalization (CTLE+DFE) |
| **Gen4** | 16.0 GT/s | 128b/130b | ~2 GB/s | ~32 GB/s | Tighter jitter budget, better equalization |
| **Gen5** | 32.0 GT/s | 128b/130b (FLIT mode) | ~4 GB/s | ~64 GB/s | FLIT-based, FEC required, lower BER target |

> **Gen3 introduced link equalization** — the receiver trains the transmitter's de-emphasis and pre-shoot at link-up. This is fully automated in the hard block.

---

## Intel Hard Block: Arria 10, Stratix 10, Agilex

### Architecture

Intel's PCIe hard block is called the **Hard IP for PCI Express** (or "PCIe HIP"):

| Family | Block Name | Key Features |
|---|---|---|
| **Arria 10** | PCIe Gen3 ×8 HIP | 1 PF, up to 4 VFs (with SR-IOV IP), Avalon-MM or Avalon-ST interface |
| **Stratix 10** | PCIe Gen3 ×16 HIP | 4 PF, 2k VF, SR-IOV, AER/ECRC, TLP bypass mode |
| **Agilex 7** | PCIe Gen5 ×16 HIP (P-Tile) | 4 PF, 2k VF, CXL 1.1, integrated DMA, MSI-X, FLIT mode |

The Avalon-MM interface presents a flat memory space:

```verilog
// Reading from PCIe BAR0 via Avalon-MM
// Host writes to BAR0 → appears on Avalon-MM as:
//   avmm_bar0_address  (BAR-relative offset)
//   avmm_bar0_write    (write strobe)
//   avmm_bar0_writedata
//
// FPGA reads → translated into PCIe Memory Read TLPs back to Host
```

> [!WARNING]
> Intel Agilex documentation confusingly uses "HIP" for Hard IP. In Agilex context, the P-Tile PCIe block is sometimes called the "PCIe HIP" — this is the hardened PCIe controller in the P-Tile, not something in the FPGA fabric.

---

## Xilinx Hard Block: 7-series, UltraScale+, Versal

### 7-series (PCIe Gen2)

The 7-series Integrated Block for PCI Express supports up to Gen2 ×8:

```
┌── 7-series PCIe Block ──────────────────────┐
│                                              │
│  PHY (GTX transceivers) ──→ AXI4-Stream      │
│  (8 lanes max at 5 GT/s)       interface     │
│                                              │
│  Note: No AXI4-MM on 7-series!               │
│  Must use AXI Bridge for PCIe IP              │
└──────────────────────────────────────────────┘
```

### UltraScale+ (PCIe Gen4)

UltraScale+ introduced the **PCIe4 Integrated Block** with AXI4 Memory-Mapped:

```tcl
# Vivado: Configure UltraScale+ PCIe4 block
create_bd_cell -type ip -vlnv xilinx.com:ip:xdma:4.1 xdma_0
# or for the hard block directly:
create_bd_cell -type ip -vlnv xilinx.com:ip:pcie4_uscale_plus:1.3 pcie_0
```

### Versal (PCIe Gen5 with CXL)

Versal's CPM (Co-processor Module) integrates PCIe Gen5 + CXL into the hardened NoC:

```
CPM5 Block:
┌─────────────────────────────────────┐
│  PCIe Gen5 ×16 (32 GT/s)            │
│  CXL 1.1/2.0 .cache/.mem/.io        │
│  Integrated DMA (QDMA)              │
│  ──→ NoC (Network-on-Chip) ──→ DDR  │
│  ──→ AXI4-MM ──→ FPGA fabric        │
└─────────────────────────────────────┘
```

---

## Link Training & Status LEDs

The physical link trains automatically at power-up. The IP provides status signals:

```verilog
// Xilinx: Link status
wire        user_lnk_up;        // 1 = link is up (L0 state)
wire [5:0]  ltssm_state;        // LTSSM state machine encoding
wire [3:0]  negotiated_width;   // Actual link width (×1, ×4, ×8, ×16)
wire [2:0]  negotiated_speed;   // Actual speed (Gen1=1, Gen2=2, ...)
```

```verilog
// Intel: Link status
wire        tl_cfg_lnk_up;      // Configuration space link-up
wire [3:0]  tl_cfg_neg_width;   // Negotiated width (×1, ×2, ×4, ×8)
wire [2:0]  tl_cfg_link_speed;  // 0=Gen1, 1=Gen2, 2=Gen3
```

**LTSSM States (key ones):**
- **Detect** → Polling → Configuration → **L0** (normal operation)
- L0s (power saving), L1 (deeper sleep), L2 (power off)
- Recovery (retrain link after error), Hot Reset, Disabled

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **REFCLK frequency mismatch** | Link never trains past Detect | 100 MHz HCSL for Gen1/2/3; verify on oscilloscope |
| **Lane reversal not configured** | Link trains to ×1 instead of ×4/×8/×16 | Enable lane reversal in IP configuration if PCB routes are reversed |
| **PERST# assertion during config** | FPGA configuration corrupted | Ensure PERST# is deasserted ONLY after FPGA configuration completes |
| **AXI width mismatch to hard block** | TLP data corruption | Match AXI_DATA_WIDTH to hard block's internal width (128-bit or 256-bit) |
| **Max Payload Size too small** | Low throughput (PCIe overhead dominates) | Set to 256 bytes minimum (512 bytes recommended) |
| **Missing MSI/MSI-X** | No interrupts reach the host | Verify MSI capability in config space; check interrupt pin in AXI bridge |
| **BAR size too small** | Host can't map full address space | Set BAR size to power-of-2; 64-bit BAR for >2 GB |

---

## Further Reading

| Article | Topic |
|---|---|
| [pcie_configuration.md](pcie_configuration.md) | BAR setup, MSI/MSI-X, AER, IP parameterization |
| [pcie_dma.md](pcie_dma.md) | DMA engines (XDMA/QDMA), descriptor rings, scatter-gather |
| [transceivers/](../transceivers/README.md) | Multi-gigabit transceiver PHY deep dive |
| PCI-SIG Base Spec | PCI Express Base Specification (membership required) |
