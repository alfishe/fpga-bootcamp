[← Section Home](../README.md) · [← Project Home](../../README.md)

# 02-C — SoC: Hard CPU + FPGA Integration

When a hardened CPU complex shares a die with FPGA fabric, the architecture shifts dramatically. This folder covers the integration patterns — AXI bridge topologies, shared memory hierarchies, cache coherency, boot sequencing — that define how software and hardware interact on FPGA SoCs.

---

## The Landscape: Every Vendor's SoC Offering

| Vendor | Family | CPU Architecture | Process | Max FPGA LEs | Unique Trait |
|---|---|---|---|---|---|
| **Intel** | [Cyclone V SoC](../../01_vendors_and_families/altera_intel/cyclone_v/soc/README.md) | Dual Cortex-A9 (32-bit ARMv7) | 28nm | 301K | MiSTer ecosystem, cheapest HPS entry |
| Intel | [Arria 10 SoC](../../01_vendors_and_families/altera_intel/arria_10/README.md) | Dual Cortex-A9 @ 1.2 GHz | 20nm | 660K | Same HPS as Cyclone V, faster fabric + 28G XCVR |
| Intel | [Stratix 10 SoC](../../01_vendors_and_families/altera_intel/stratix_10/README.md) | Quad Cortex-A53 (64-bit ARMv8) | 14nm | 5,510K | HyperFlex routing, HBM2 option |
| Intel | [Agilex 7 SoC](../../01_vendors_and_families/altera_intel/agilex/README.md) | Quad Cortex-A53 (ARMv8) | Intel 7 | up to ~4M | Chiplet (EMIB), PCIe 5.0, HBM2e option |
| Intel | [Agilex 5 SoC](../../01_vendors_and_families/altera_intel/agilex/README.md) | Dual A76 + Dual A55 | Intel 7 | up to ~1.7M | Lowest power Agilex, MIPI D-PHY, cost-optimized |
| **Xilinx** | [Zynq-7000](../../01_vendors_and_families/xilinx/7series/README.md) | Dual Cortex-A9 (32-bit ARMv7) | 28nm | 444K | **ACP** — FPGA cache-coherent access |
| Xilinx | [Zynq MPSoC](../../01_vendors_and_families/xilinx/ultrascale_plus/README.md) | Quad A53 + Dual R5F | 16nm | 1,143K | GPU (Mali-400), video codec (VCU) |
| Xilinx | [Zynq RFSoC](../../01_vendors_and_families/xilinx/ultrascale_plus/README.md) | Quad A53 + Dual R5F | 16nm | 930K | Direct RF ADCs/DACs on-die (→ [hybrid/](../hybrid/README.md)) |
| Xilinx | [Versal](../../01_vendors_and_families/xilinx/versal/README.md) | Dual A72 + Dual R5F | 7nm | ~2,000K | NoC interconnect, AI Engines (→ [hybrid/](../hybrid/README.md)) |
| **Microchip** | [SmartFusion2](../../01_vendors_and_families/microchip/smartfusion2_igloo2/README.md) | Hard Cortex-M3 | 65nm | 150K | Flash-based, FIPS 140-2 crypto, ADC |
| Microchip | [PolarFire SoC](../../01_vendors_and_families/microchip/polarfire/README.md) | 4× U54 + 1× E51 (64-bit RISC-V) | 28nm | 460K | Only RISC-V hard-SoC FPGA, instant-on flash |
| **Gowin** | [GW1NSR](../../01_vendors_and_families/gowin/littlebee/README.md) | Hard PicoRV32 | 55nm | 4.6K | $7 SoC FPGA, lowest cost |

---

## Common Architecture: The CPU-FPGA Coupling Model

Every FPGA SoC follows the same fundamental die partitioning:

```
┌────────────── FPGA SoC Die ──────────────┐
│                                          │
│  ┌────────── Processing System ────────┐ │
│  │  CPU Cores    L1 I/D Caches         │ │
│  │      └────────┬─────┘               │ │
│  │               ▼                     │ │
│  │  L2 Cache (shared)                  │ │
│  │               │                     │ │
│  │  ┌────────────▼───────────────────┐ │ │
│  │  │  L3 Interconnect (NIC/NoC)     │ │ │
│  │  └──┬─────────┬──────────┬────────┘ │ │
│  │     │         │          │          │ │
│  │  ┌──▼──┐ ┌───▼───┐ ┌───▼────────┐   │ │
│  │  │DDR  │ │Periph │ │CPU↔FPGA    │   │ │
│  │  │Ctrl │ │(USB,  │ │Bridges     │   │ │
│  │  │     │ │Eth,SD)│ │            │   │ │
│  │  └─────┘ └───────┘ └──┬─────────┘   │ │
│  └───────────────────────┼─────────────┘ │
│                          │               │
│  ┌───────────────────────▼─────────────┐ │
│  │  Programmable Logic (FPGA Fabric)   │ │
│  │  LUTs · BRAM · DSP · PLLs · SERDES  │ │
│  └─────────────────────────────────────┘ │
│                                          │
└──────────────────────────────────────────┘
```

Two domains, one die. The CPU side is called the **PS** (Processing System, Xilinx) or **HPS** (Hard Processor System, Intel). The FPGA side is the **PL** (Programmable Logic, Xilinx) or just "FPGA fabric" (Intel). Bridge ports connect them.

---

## Is an FPGA SoC a True SoC?

There is a nuanced distinction between the industry term "SoC FPGA" and a traditional monolithic SoC. In a smartphone application processor or automotive MCU, the CPU, GPU, memory controller, and peripherals are designed together as a single IP integration project — shared register maps, unified clock trees, co-validated subsystems. The FPGA SoC is different: the CPU complex and FPGA fabric are **separate IP blocks** connected through a handful of bridge ports. They share a die but not a design methodology.

| Property | Traditional SoC | FPGA SoC |
|---|---|---|
| CPU-fabric coupling | Tight (co-designed buses, shared reg maps) | Loose (standard AXI bridges, independent clock domains) |
| Memory coherency | Usually coherent (snoop-based) | Optional (ACP on Zynq, none on Cyclone V) |
| Fabric behavior | Fixed at tape-out | Reconfigurable at runtime |
| Peripherals | Custom IP blocks | Standard HPS peripherals + soft IP in fabric |
| Verification | Unified simulation model | CPU in QEMU, fabric in HDL simulator, co-sim bridge (→ [07 Verification](../../07_verification/co_simulation.md)) |

This is why an FPGA SoC demands a different design mindset: you're not writing software on a fixed SoC — you're building the hardware half of the SoC yourself, then writing software to control it.

---

## CPU Cores Across Vendors

| CPU Type | Vendor(s) | Architecture | MMU | FPU | Linux |
|---|---|---|---|---|---|
| **Cortex-A9** (32-bit ARMv7) | Intel (Cyclone V, Arria 10), Xilinx (Zynq-7000) | Dual-issue, 2.5 DMIPS/MHz | ✓ | NEON | ✓ Full |
| **Cortex-A53** (64-bit ARMv8) | Intel (Stratix 10), Xilinx (MPSoC) | In-order, 2.3 DMIPS/MHz | ✓ | NEON | ✓ Full |
| **Cortex-A72** (64-bit ARMv8) | Xilinx (Versal) | Out-of-order, 4.7 DMIPS/MHz | ✓ | NEON | ✓ Full |
| **Cortex-R5F** (32-bit ARMv7-R) | Xilinx (MPSoC, Versal) | Real-time, lockstep capable | MPU only | ✓ (SP) | ✗ RTOS/ bare-metal |
| **Cortex-M3** (32-bit ARMv7-M) | Microchip (SmartFusion2) | Microcontroller profile | MPU | ✗ | ✗ RTOS only |
| **RISC-V U54** (64-bit RV64GC) | Microchip (PolarFire SoC) | 5-stage, 1.7 DMIPS/MHz | ✓ | ✓ | ✓ Full |
| **PicoRV32** (32-bit RV32IMC) | Gowin (GW1NSR) | Minimal RV32, ~30 MHz | ✗ | ✗ | ✗ Bare-metal |

### Key Note: Zynq-7000 and Cyclone V SoC Share the Same ARM Core Type but Expose It Very Differently

Both use dual Cortex-A9 at the same 28nm node, running at similar frequencies (~800 MHz). From a benchmark perspective they are nearly identical. But the way the CPU connects to the FPGA fabric makes them architecturally divergent:

- **Cyclone V SoC HPS** has three AXI-3 bridge pairs (H2F 64-bit, LWH2F 32-bit, F2H 64-bit) plus six FPGA-to-SDRAM ports. FPGA access to DDR **bypasses the L2 cache**. Consistently non-coherent.
- **Zynq-7000** has 2 M_AXI_GP (32-bit PS→PL control), 4 S_AXI_HP (64-bit PL→DDR high-performance), 2 S_AXI_GP (32-bit PL→PS slave), and one **ACP** (64-bit cache-coherent). The ACP connects FPGA logic directly to the Cortex-A9 Snoop Control Unit (SCU), giving the FPGA **cache-coherent access** to the CPU's L2 cache. This means an FPGA accelerator can read/write CPU memory without explicit cache flush/invalidate operations — the hardware maintains coherency automatically.

| Property | Cyclone V SoC HPS | Zynq-7000 PS |
|---|---|---|
| Coherent FPGA access | ❌ F2S bypasses L2 | ✅ ACP snoops L2 via SCU |
| FPGA→DDR path count | 6× F2S ports | 4× S_AXI_HP ports |
| Control register path | LWH2F 32-bit | M_AXI_GP 32-bit (4 ports) |

Choosing between them: if your FPGA accelerator needs to share data structures with Linux userspace in real time without manual cache management, use **Zynq-7000**. If you're streaming bulk data (video frames, SDR samples) where cache is irrelevant, the **Cyclone V SoC** F2S ports provide more aggregate bandwidth. For retro computing and MiSTer, Cyclone V SoC has the ecosystem.

---

## AXI Bridges: The CPU-FPGA Interface

Every FPGA SoC uses ARM AMBA AXI for CPU-FPGA communication. Four patterns recur:

| Bridge Role | Cyclone V Name | Zynq-7000 Name | Width | Signature | Purpose |
|---|---|---|---|---|---|
| CPU **reads/writes FPGA** | HPS-to-FPGA (H2F) | M_AXI_GP | 32–64 bit | CPU is manager, FPGA is subordinate | Control registers, command queues |
| FPGA **reads/writes CPU memory** | FPGA-to-HPS (F2H) | S_AXI_HP | 64 bit | FPGA is manager, DDR is subordinate | DMA completion, status push |
| FPGA **direct DDR access** | FPGA-to-SDRAM (F2S) | (included in S_AXI_HP) | 64–256 bit | Bypasses L2 cache entirely | Framebuffer, data ingest |
| **Lightweight control** | Lightweight H2F (LWH2F) | (via M_AXI_GP) | 32 bit | Lower latency, fewer bits | GPIO, simple regs |

**AXI-3 vs AXI-4:** Intel uses AXI-3 (allows write interleaving via WID signal); Xilinx uses AXI-4 (removes WID). If you connect an Intel HPS to third-party AXI IP expecting AXI-4, write data ordering can break.

**Versal departs from AXI bridges entirely** — it replaces the traditional AXI crossbar with a hard 2D-mesh **NoC** (Network-on-Chip). The NoC provides QoS-guaranteed, deadlock-free routing between PS, PL, AI Engines, DDR controllers, and transceivers. This is covered in [hybrid/](../hybrid/README.md).

---

## Memory Hierarchy

```
Fastest ◄──────────────────────────────────► Largest

On-Chip RAM       L2 Cache        Hard DDR Ctrl      PL BRAM
(64-256 KB)     (512 KB-2 MB)    (DDR3/4/LPDDR4)    (scattered)
   │                  │                │                 │
   ▼                  ▼                ▼                 ▼
 Boot ROM,       Unified L2      Up to 4 GB       True dual-port,
 exception        shared across   (Cyclone V),     36 Kb blocks,
 vectors          all CPU cores   up to 32 GB       FPGA-local
                                  (MPSoC)
```

**Shared DDR bandwidth is not partitioned.** On Cyclone V SoC, six F2S masters share the hard DDR controller with the L3 interconnect — with **no QoS arbitration**. A tight FPGA read loop on one F2S port can starve the Linux kernel. Zynq-7000's HP ports similarly contend with CPU access to DDR. The solution across all vendors is the same: use FPGA-internal FIFOs as burst buffers.

**Cache coherency** is the biggest differentiator. Zynq-7000's ACP lets FPGA logic share the L2 cache. PolarFire SoC uses a coherent AXI4 bus matrix connecting all five RISC-V cores to the L2 cache and DDR — the FPGA fabric connects through this same coherent matrix. Cyclone V SoC offers no coherency at all: FPGA access always bypasses L2.

---

## Boot Architecture: CPU First, FPGA Follows

Every FPGA SoC follows the same multi-stage boot sequence:

```
1. Power-On Reset
   │
   ▼
2. CPU Boot ROM (on-chip, immutable)
   │  Reads BSEL/boot-mode pins
   │  Loads 1st-stage bootloader from flash/SD
   ▼
3. 1st Stage  (U-Boot SPL / FSBL)
   │  Configures: DDR, clocks, pin mux
   │  Optionally loads FPGA bitstream
   ▼
4. 2nd Stage  (U-Boot / Linux kernel)
   │  Complete OS boot
   │  FPGA Manager driver active (post-boot config)
   ▼
5. Userspace — FPGA active, bridges operational
```

| Stage | Intel (Cyclone V) | Xilinx (Zynq-7000) | Microchip (PolarFire SoC) |
|---|---|---|---|
| Boot ROM source | HPS internal ROM (64 KB) | PS internal BootROM (128 KB) | E51 monitor core from eNVM |
| 1st stage | U-Boot SPL (from SD/QSPI) | FSBL (First Stage Bootloader) | Hart Software Services (HSS) |
| FPGA config trigger | U-Boot or Linux FPGA Manager | FSBL or Linux devcfg/fpga_manager | Libero bitstream from eNVM/spi-flash |
| Boot device | SD, QSPI, NAND | SD, QSPI, NAND, NOR, JTAG | QSPI / eMMC / SD |

**Key difference:** on Cyclone V SoC, the HPS configures the FPGA as part of its normal boot flow (FPP ×16 via HPS). On Zynq-7000, the PL is in an **off** power domain after PS boot — you must explicitly enable it. Microchip PolarFire SoC is simpler: configuration is stored in internal flash, the FPGA is instant-on at power-up, and the E51 monitor core boots first.

---

## Unique Per-Vendor Features

### Cache-Aware Acceleration: Zynq-7000 ACP

The **Accelerator Coherency Port** is Zynq-7000's architectural crown jewel. It connects FPGA logic directly to the Cortex-A9 Snoop Control Unit (SCU), which maintains coherency between the two CPU cores' L1 caches and the shared L2 cache. When the FPGA issues a read through ACP:

1. The SCU checks if the data is dirty in either core's L1
2. If dirty, the SCU copies the modified line to L2 and then returns it to the FPGA
3. The FPGA sees the same memory state the CPUs see — no software cache management needed

This eliminates an entire class of bugs where the FPGA reads stale DDR values because Linux hasn't flushed a cache line yet. No other vendor offers this at the Zynq-7000's price point.

### RISC-V SoC FPGA: PolarFire SoC

Microchip PolarFire SoC is the only FPGA with **five hard RISC-V cores** on-die: four U54 application cores (RV64IMAFDC) running Linux, and one E51 monitor core (RV64IMAC) handling boot and system management. Combined with flash-based instant-on configuration (<1 ms) and SEU immunity, it is fundamentally a different design point from ARM-based competitors.

### PicoRV32: Gowin GW1NSR

Gowin integrates a minimal 32-bit RISC-V (PicoRV32) running at ~30 MHz directly into its $7 FPGA. It's not Linux-capable — it's a microcontroller replacement. The value proposition: you get a known-good CPU that doesn't consume FPGA LUTs, plus the FPGA for custom peripherals, on a $7 chip.

### Cortex-M3 + ADC + Crypto: SmartFusion2

Microchip SmartFusion2 combines a hard Cortex-M3 (166 MHz), 12-bit ADC, and FIPS 140-2 certified crypto chain. This is uniquely positioned for defense and secure embedded applications where you need a validated, tamper-resistant processor with FPGA I/O flexibility.

---

## Index

| File | Topic |
|---|---|
| [hard_processor_integration.md](hard_processor_integration.md) | CPU-FPGA coupling models: ARM Cortex-A9/A53, RISC-V U54, soft vs hard CPU tradeoffs |
| [axi_bridges_and_interconnect.md](axi_bridges_and_interconnect.md) | AXI-3/4 bridge architecture: HPS-to-FPGA, FPGA-to-HPS, FPGA-to-SDRAM, lightweight bridges, bandwidth budgets |
| [hps_fpga_intel_soc.md](hps_fpga_intel_soc.md) | **Intel deep dive:** H2F/F2H/LWH2F/F2S bridges, NIC-301, non-coherent model, Platform Designer integration |
| [hps_fpga_xilinx_zynq.md](hps_fpga_xilinx_zynq.md) | **Xilinx deep dive:** M_AXI_GP/S_AXI_HP/S_AXI_HPC/ACP ports, CCI-400 coherency, QoS, Vivado integration, Versal NoC |
| [hps_fpga_microchip_soc.md](hps_fpga_microchip_soc.md) | **Microchip deep dive:** FIC0/1/2 coherent interfaces, AXI4 bus matrix, PLIC interrupts, Libero SmartDesign, security |
| [memory_hierarchy.md](memory_hierarchy.md) | On-die memory topology: hard DDR controllers, L1/L2 caches, on-chip RAM, cache coherency (ACP vs non-coherent), DMA engines |
| [boot_architecture.md](boot_architecture.md) | SoC boot sequencing: Boot ROM → preloader → U-Boot → Linux, FPGA configuration via HPS, multi-stage bitstream loading |

---

## Why they are unique

Pure FPGA architecture (fabric + infrastructure) assumes the FPGA is the whole system. In a SoC:
- The **CPU boots first** — the FPGA is a peripheral from the CPU's view until configured
- **Memory is shared** — FPGA masters compete with CPU cores for DDR bandwidth
- **Cache coherency** matters — Zynq's ACP vs Cyclone V's non-coherent F2S bridges
- **Boot is multi-stage** — CPU firmware, FPGA bitstream, and OS image all interact

This is a fundamentally different architectural paradigm from standalone FPGA design.
