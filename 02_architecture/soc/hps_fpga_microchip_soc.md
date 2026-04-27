[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# Microchip SoC FPGA — MSS-Fabric Interface Architecture

How the Microchip Microcontroller Subsystem (MSS) communicates with FPGA fabric across PolarFire SoC (RISC-V) and SmartFusion2/IGLOO2 (ARM Cortex-M3) families. Covers the coherent AXI4 bus matrix, fabric interface controllers, and the unique security model that differentiates Microchip from Intel and Xilinx.

---

## The Microchip MSS Model: Coherent by Default

Microchip's approach is architecturally distinct: **all CPU cores and the FPGA fabric share a unified coherent memory subsystem**. There is no optional coherency port — coherency is the default behavior.

```
        ┌───────────────────────────────────────────────┐
        │         PolarFire SoC MSS / Fabric            │
        │                                               │
        │  ┌─────────┐  ┌─────────┐  ┌───────────────┐ │
        │  │  U54×4  │  │   E51   │  │    L2 Cache   │ │
        │  │(Linux)  │  │(Monitor)│◄─┤  ( coherent   │ │
        │  └────┬────┘  └────┬────┘  │   across all )│ │
        │       │            │       └───────┬───────┘ │
        │       └────────────┴───────────────┘         │
        │                     │                        │
        │              ┌──────▼──────┐                 │
        │              │ Coherent    │                 │
        │              │ AXI4 Bus    │                 │
        │              │ Matrix      │                 │
        │              └──────┬──────┘                 │
        │                     │                        │
        │    ┌────────────────┼────────────────┐      │
        │    │                ▼                │      │
        │    │  ┌─────────┐ ┌─────────┐ ┌────▼───┐  │
        │    │  │  FIC0   │ │  FIC1   │ │  FIC2  │  │
        │    │  │AXI4 64-b│ │AXI4 64-b│ │AXI4    │  │
        │    │  │(master) │ │(master/ │ │(slave) │  │
        │    │  │         │ │ slave)  │ │        │  │
        │    │  └────┬────┘ └────┬────┘ └───┬────┘  │
        │    │       │           │          │       │
        │    │  ┌────▼───────────▼──────────▼────┐  │
        │    │  │        FPGA Fabric             │  │
        │    │  │  LUTs · BRAM · DSP · SerDes    │  │
        │    │  └────────────────────────────────┘  │
        │    │                                      │
        │    └──────────────────────────────────────┘
        └───────────────────────────────────────────────┘
```

**Key architectural principle:** All five RISC-V cores (four U54 + one E51) and the FPGA fabric connect to the same **coherent AXI4 bus matrix**. The FPGA is a first-class citizen in the coherency domain — not a peripheral that needs special ports to participate.

---

## PolarFire SoC: MSS-to-Fabric Interfaces (FIC)

The Microcontroller Subsystem exposes three **Fabric Interface Controllers (FIC)** that connect the coherent MSS bus matrix to the FPGA fabric.

| FIC | Width | Direction | Coherent | Primary Use |
|---|---|---|---|---|
| **FIC0** | 64-bit AXI4 | MSS → Fabric | Yes | FPGA slaves (control registers, memories) |
| **FIC1** | 64-bit AXI4 | Bidirectional | Yes | FPGA masters + slaves (DMA, shared memory) |
| **FIC2** | 64-bit AXI4 | Fabric → MSS | Yes | MSS slaves (DDR, eNVM, peripherals) |

> **Microchip terminology note:** Microchip uses "Initiator" and "Target" instead of AXI "Master" and "Slave" in recent documentation.

### FIC0 — MSS Initiator to Fabric Target

FIC0 is the primary control path from the RISC-V cores into the FPGA fabric. The E51 monitor core or U54 Linux kernel uses FIC0 to access registers and memories implemented in FPGA logic.

| Property | Value |
|---|---|
| Data width | 64-bit |
| Address width | 38-bit (256 GB space) |
| Protocol | AXI4 |
| Burst | Up to 256 beats |
| Clock | MSS clock (async to fabric) |
| Coherency | Full cache coherency |

### FIC1 — Bidirectional Interface

FIC1 is unique: it supports **both MSS-initiated and fabric-initiated transactions**. This makes it the most flexible interface for applications where control and data flow in both directions.

Typical use cases:
- FPGA DMA engine reads/writes MSS DDR through FIC1
- MSS CPU accesses FPGA on-chip RAM through FIC1
- Mailbox / command queue in both directions

### FIC2 — Fabric Initiator to MSS Target

FIC2 allows FPGA logic to act as AXI initiator, accessing MSS resources:
- MSS DDR memory
- eNVM (embedded non-volatile memory)
- MSS peripherals (SPI, I2C, UART, Ethernet MAC)
- Other FIC targets

---

## Coherent AXI4 Bus Matrix

The heart of PolarFire SoC is a **fully coherent AXI4 bus matrix** connecting all initiators to all targets.

### Initiators (Masters)

| Initiator | Cores | Cache Level | Purpose |
|---|---|---|---|
| U54 Core 0 | 1 | L1 I/D + L2 | Application processor 0 |
| U54 Core 1 | 1 | L1 I/D + L2 | Application processor 1 |
| U54 Core 2 | 1 | L1 I/D + L2 | Application processor 2 |
| U54 Core 3 | 1 | L1 I/D + L2 | Application processor 3 |
| E51 Core | 1 | L1 I/D only | Monitor / boot processor |
| FIC0/1/2 | — | — | FPGA fabric interfaces |

### Targets (Slaves)

| Target | Description |
|---|---|
| MSS DDR Controller | External DDR3/4 |
| eNVM | 128 KB embedded flash (boot code) |
| sNVM | 56 KB secure non-volatile memory |
| MSS Peripherals | Ethernet, USB, SPI, I2C, UART, CAN |
| FIC0/1/2 | FPGA fabric (via bridges) |

### Coherency Mechanism

Unlike Xilinx's ACP (which is an add-on to a non-coherent system), PolarFire SoC's coherency is **integral**:

1. All U54 cores have private L1 instruction and data caches
2. All four U54 cores share a unified L2 cache (inclusive)
3. The bus matrix includes a **snoop filter** that tracks which cores hold which cache lines
4. When the FPGA (via FIC) accesses a cacheable address:
   - The snoop filter checks if any core holds the line
   - If dirty in L1/L2, data is forwarded from cache
   - If clean, data comes from DDR or L2
   - Cache state is updated atomically

### Coherency vs Intel / Xilinx

| Property | Intel Cyclone V | Xilinx Zynq-7000 ACP | Microchip PolarFire SoC |
|---|---|---|---|
| Coherency default | None | Optional (ACP only) | Universal (all interfaces) |
| Coherency scope | N/A | L1+L2 via SCU | L1+L2 via bus matrix snoop filter |
| FPGA access | F2S bypasses cache entirely | ACP only coherent | All FIC ports coherent |
| Software overhead | Explicit flush/inv | None for ACP, flush for HP | None (always coherent) |
| Design complexity | Simple bridges | Must choose HP vs ACP | All traffic is coherent |

---

## Memory Map

PolarFire SoC uses a unified 38-bit physical address space shared by MSS and FPGA.

| Region | Address | Size | Description |
|---|---|---|---|
| DDR | 0x8000_0000 | Up to 8 GB | External DDR3/4 |
| eNVM | 0x2022_0000 | 128 KB | Embedded non-volatile memory |
| sNVM | 0x2022_1000 | 56 KB | Secure NVM |
| ENVM Config | 0x2022_3000 | 8 KB | eNVM config registers |
| MSS Peripherals | 0x2000_0000 | 2 MB | UART, SPI, Ethernet, etc. |
| FPGA Fabric (FIC) | 0x4000_0000 | 256 MB | Fabric slaves via FIC0/1 |
| FPGA Fabric (high) | 0x6000_0000 | 2 GB | Extended fabric region |
| L2 Cache Controller | 0x0201_0000 | 64 KB | L2 cache control regs |
| CLINT | 0x0200_0000 | 64 KB | RISC-V local interrupts |
| PLIC | 0x0C00_0000 | 4 MB | Platform-level interrupt controller |

### FPGA-Fabric Address Decoding

When the MSS accesses FPGA fabric addresses (0x4000_0000+), the bus matrix routes through FIC0/FIC1 to the fabric. Inside the fabric, the Libero SoC design tools generate an AXI4 crossbar that decodes addresses to individual IP blocks.

```
MSS Address              FPGA Fabric Destination
─────────────────────────────────────────────────
0x4000_0000 ──► 0x4000_FFFF   Custom peripheral 0 (ctrl regs)
0x4001_0000 ──► 0x4001_FFFF   Custom peripheral 1 (DMA engine)
0x4002_0000 ──► 0x4002_FFFF   FPGA on-chip RAM (128 KB)
0x4100_0000 ──► 0x41FF_FFFF   Video framebuffer region
```

---

## Libero SoC / SmartDesign Integration

Microchip's design tool (Libero SoC) uses **SmartDesign** to graphically connect MSS FIC ports to fabric IP.

### Typical SmartDesign Layout

```
┌─────────────────────────────────────────────┐
│           SmartDesign Canvas                │
│                                             │
│  ┌─────────┐      ┌─────────────────────┐  │
│  │  MSS    │──────► AXI4 Interconnect    │  │
│  │  IP     │◄─────│  (auto-generated)   │  │
│  │         │      │                     │  │
│  └─────────┘      └──┬─────┬─────┬─────┘  │
│                      │     │     │         │
│                   ┌──▼──┐ ┌▼───┐ ┌▼────┐  │
│                   │AXI  │ │AXI │ │AXI  │  │
│                   │DMA  │ │GPIO│ │Video│  │
│                   │     │ │    │ │     │  │
│                   └─────┘ └─────┘ └─────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

The MSS Configurator tool in Libero lets you:
- Enable/disable FIC0, FIC1, FIC2
- Set AXI4 width (all are 64-bit fixed on PolarFire SoC)
- Configure DDR controller parameters
- Assign interrupt lines from fabric to PLIC

### Clock Domains

| Domain | Typical Frequency | Source |
|---|---|---|
| MSS CPU | 667 MHz | MSS PLL |
| MSS bus | 333 MHz | Derived from CPU clock |
| FPGA fabric | 50-250 MHz | Fabric CCC (Clock Conditioning Circuit) |
| DDR | 800-1066 MHz (1600 MT/s) | DDR PLL |

The FIC bridges contain asynchronous FIFOs for clock crossing between MSS and fabric domains.

---

## SmartFusion2 / IGLOO2: AHB Bus Matrix

PolarFire SoC's predecessor uses a different architecture:

| Property | SmartFusion2 / IGLOO2 |
|---|---|
| CPU | Cortex-M3 @ 166 MHz |
| Bus | AHB-Lite (not AXI4) |
| FPGA interface | AHB bus matrix to fabric |
| Coherency | N/A (single core, no cache) |
| Fabric width | 32-bit AHB |

The Cortex-M3 has no cache, so coherency is a non-issue. The AHB bus matrix connects the M3's code bus, system bus, and DMA to FPGA fabric slaves. This is a much simpler model suitable for microcontroller-class applications.

### SmartFusion2 Fabric Interface

```
Cortex-M3
    │
    ├──► Code bus ──► AHB Matrix ──► Flash / SRAM
    │
    ├──► System bus ─► AHB Matrix ──► FPGA Fabric (AHB slaves)
    │                              ──► Peripherals (UART, SPI, etc.)
    │
    └──► DMA ────────► AHB Matrix ──► FPGA Fabric / DDR
```

The FPGA fabric appears as AHB-Lite memory regions. Custom IP implements AHB-Lite slave interfaces with `HREADY`, `HRESP`, `HWDATA`, `HRDATA` signals.

---

## Security: Fabric Isolation

PolarFire SoC includes hardware security features that affect HPS-FPGA communication:

### Design Serial Number (DSN)

Each PolarFire SoC device has a unique 128-bit **Design Serial Number**. The FPGA bitstream can be encrypted and bound to this DSN, preventing cloning. When the MSS loads a bitstream:

1. Bitstream is encrypted with AES-256
2. DSN is used as part of the key derivation
3. Only the target device can decrypt and configure the fabric

### Tamper Detection

- Voltage / temperature / clock glitch monitors
- Zeroization of sNVM and keys on tamper event
- JTAG disable via eFuse

### Secure Boot Chain

```
eNVM (encrypted HSS) ──► HSS verifies U-Boot ──► U-Boot verifies Linux kernel
         │                              │                    │
         │                              │                    │
    DSN-bound                    ECDSA signature       ECDSA signature
    encryption                   verification          verification
```

This security model means the FPGA fabric is part of a **trusted boundary** — the MSS can verify the integrity of the fabric configuration before enabling it.

---

## Bandwidth and Performance

### PolarFire SoC Fabric Bandwidth

| Path | Width | Clock | Theoretical | Realistic |
|---|---|---|---|---|
| FIC0 → Fabric | 64-bit | 167 MHz | 1.34 GB/s | ~1.0 GB/s |
| FIC1 → Fabric | 64-bit | 167 MHz | 1.34 GB/s | ~1.0 GB/s |
| Fabric → DDR (FIC2) | 64-bit | 167 MHz | 1.34 GB/s | ~1.0 GB/s |
| MSS DDR peak | 16-bit DDR3-1600 | 800 MHz | 3.2 GB/s | ~2.5 GB/s |

The FIC bandwidth (~1 GB/s per port) is lower than Intel F2S or Xilinx HP ports. However, **coherency eliminates software overhead** — for small, frequent shared data accesses, PolarFire SoC can outperform non-coherent systems.

### Comparison: Small Shared Buffer Access

| System | Latency (64-byte buffer) | Software overhead |
|---|---|---|
| Intel Cyclone V (F2S + flush) | ~200 ns + 5 µs flush | Explicit cache management |
| Xilinx Zynq-7000 (ACP) | ~150 ns | None |
| Microchip PolarFire SoC (FIC) | ~120 ns | None (always coherent) |

For accelerator workloads with frequent CPU-FPGA handshakes, PolarFire SoC's integrated coherency reduces total transaction time despite lower peak bandwidth.

---

## Interrupt Architecture

PolarFire SoC routes fabric interrupts through the **PLIC (Platform-Level Interrupt Controller)**:

```
FPGA Fabric IP
    │
    ├──► IRQ0 ──► PLIC IRQ 0 ──► U54 Core 0
    ├──► IRQ1 ──► PLIC IRQ 1 ──► U54 Core 1
    ├──► IRQ2 ──► PLIC IRQ 2 ──► U54 Core 2
    ├──► IRQ3 ──► PLIC IRQ 3 ──► U54 Core 3
    └──► IRQ4 ──► PLIC IRQ 4 ──► E51 Core
```

The PLIC supports:
- **Priority levels:** 7 levels per interrupt
- **Target selection:** Route any interrupt to any core
- **Threshold masking:** Cores ignore interrupts below their priority threshold
- **Vectoring:** Direct vs vectored mode

In Linux, the `riscv,plic0` device tree node declares the PLIC, and drivers request IRQs through the standard Linux IRQ framework.

---

## Reference Development Boards

### PolarFire SoC Boards

| Board | Vendor | Price Range | Key Features | Best For |
|---|---|---|---|---|
| **Icicle Kit** | Microchip | ~$500 | 1 GB LPDDR4, eMMC, SD, WiFi/BT module, MikroE click | RISC-V Linux, IoT gateway |
| **MPFS250T-EVAL-KIT** | Microchip | ~$1,200 | 2 GB DDR4, QSFP+, PCIe Gen2 x4 | High-speed comms, evaluation |
| **BeagleV-Fire** | BeagleBoard.org | ~$150 | BeagleBone form factor, 2 GB LPDDR4, eMMC | Open hardware, education |
| **MPFS-PROTO-KIT** | Microchip | ~$800 | Prototyping platform, FMC, multiple fabric sizes | Custom designs, evaluation |

> **Icicle Kit note:** The Icicle Kit is the primary development platform for PolarFire SoC. It includes a pre-built Linux image with Yocto and supports mainline Linux 5.10+ out of the box. The BeagleV-Fire brings PolarFire SoC to the popular BeagleBone ecosystem.

### SmartFusion2 / IGLOO2 Boards

| Board | Vendor | Price Range | Key Features | Best For |
|---|---|---|---|---|
| **SmartFusion2 KickStart Kit** | Microchip | ~$100 | Cortex-M3, 64 MB DDR, Ethernet, USB | Low-power IoT, motor control |
| **IGLOO2 Evaluation Kit** | Microchip | ~$150 | Flash-based FPGA, 1 MB SRAM, PCIe Gen2 | Space, radiation-tolerant designs |
| **SF2-STARTER-KIT** | Microchip | ~$200 | Full-featured, LCD touch, expansion headers | General evaluation |

> **SmartFusion2 note:** These boards target RTOS and bare-metal development. No Linux support — the Cortex-M3 is too resource-constrained. Flash-based FPGAs retain configuration without power, making them ideal for battery and space applications.

## Per-Family Comparison

| Feature | PolarFire SoC | SmartFusion2 / IGLOO2 |
|---|---|---|
| CPU | 4× U54 + 1× E51 (RISC-V) | 1× Cortex-M3 (ARM) |
| CPU clock | 667 MHz | 166 MHz |
| Bus protocol | Coherent AXI4 | AHB-Lite |
| Fabric interfaces | 3× FIC (64-bit AXI4) | AHB matrix |
| Coherency | Universal (all ports) | N/A (no cache) |
| Cache | L1 per core + shared L2 | No cache |
| Max DDR | 8 GB DDR3/4 | 2 GB DDR |
| Fabric LEs | 460K | 150K |
| Security | DSN, AES-256, tamper detect | Flash-based, FIPS 140-2 |
| Linux support | Full (5.10+ mainline) | No (RTOS / bare-metal) |

---

## Common Pitfalls

| Problem | Symptom | Fix |
|---|---|---|
| FIC not enabled in MSS Configurator | FPGA logic invisible to Linux | Enable FIC0/FIC1 in Libero MSS Configurator, regenerate design |
| Wrong AXI4 ID width | Bus hang, protocol error | Ensure fabric IP matches MSS AXI ID width (4-bit) |
| Fabric clock too slow for AXI4 | Timing violations in Libero | Increase fabric CCC frequency or add pipeline stages |
| RISC-V cache line size | Coherency bugs on sub-line writes | Use 64-byte aligned, 64-byte sized transactions for cacheable regions |
| PLIC IRQ not firing | FPGA events ignored by Linux | Verify PLIC device tree node, check `plic_claim` register |
| eNVM wear | Boot failures after many updates | eNVM has ~100K write cycles; use external QSPI for development |
| MSS DDR not trained | Linux kernel panic at boot | Verify DDR configuration in MSS Configurator matches board layout |

---

## Further Reading

| Document | Microchip Doc ID |
|---|---|
| PolarFire SoC MSS TRM | Available via Microchip documentation portal |
| PolarFire SoC FPGA Fabric User Guide | MPF100/250/460 |
| PolarFire SoC MSS Configurator UG | Libero SoC tool docs |
| PolarFire SoC Product Overview | 60001656 |
| SmartFusion2 MSS TRM | SF2-UM-	 |
| RISC-V Privileged ISA Spec | riscv.org |
