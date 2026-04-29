[← UltraScale+ Home](../README.md) · [← Project Home](../../../../README.md)

# Zynq UltraScale+ MPSoC — PS-PL Architecture Deep Dive

The generational leap from 28nm dual Cortex-A9 to 16nm FinFET with quad Cortex-A53 (64-bit), dual Cortex-R5 real-time cores, GPU, and video codec. The MPSoC Processing System (PS) is a full heterogeneous compute platform sharing a die with UltraScale+ FPGA fabric.

> For general MPSoC family info (variants, dev boards, Zynq-7000 comparison), see the [parent README](../README.md). For RFSoC with direct-sampling ADCs/DACs, see [02_architecture/hybrid/](../../../02_architecture/hybrid/README.md).

---

## PS Block Diagram — Six Processing Units on One Die

```
┌──────────────── Zynq MPSoC PS (Processing System) ────────────────┐
│                                                                     │
│  ┌────────────── Application Processing Unit ──────────────────┐   │
│  │  Cortex-A53  Cortex-A53  Cortex-A53  Cortex-A53             │   │
│  │   Core 0      Core 1      Core 2      Core 3               │   │
│  │   32KB L1I/D each   NEON/FPU   ARMv8-A  64-bit             │   │
│  │   1.5 GHz max                                             │   │
│  └────────────────────┬──────────────────────────────────────┘   │
│                       │                                           │
│  ┌────────────────────▼──────────────────────────────────────┐   │
│  │                    CCI-400                                   │   │
│  │    Cache Coherent Interconnect (ARM CoreLink)               │   │
│  │    • Snoop filter (reduces unnecessary snoops)              │   │
│  │    • Coherent paths: APU L2, RPU, ACP, HPC ports          │   │
│  │    • 128-bit data width, up to 3 simultaneous transactions │   │
│  └──┬──────────┬──────────┬──────────┬──────────┬────────────┘   │
│     │          │          │          │          │                 │
│  ┌──▼──┐ ┌────▼────┐ ┌───▼────┐ ┌──▼───────┐ ┌▼───────────┐     │
│  │ L2  │ │Real-Time│ │  GPU   │ │  VCU     │ │ DDR Ctrl   │     │
│  │1 MB │ │  Unit   │ │Mali-400│ │H.264/265 │ │ DDR4/      │     │
│  │     │ │ 2× R5F  │ │ MP2    │ │ encode + │ │ LPDDR4     │     │
│  │     │ │600 MHz  │ │667 MHz │ │ decode   │ │ ECC, 32/64b│     │
│  └─────┘ └─────────┘ └────────┘ └──────────┘ └─────┬───────┘     │
│                                                     │             │
│  ┌──────────────────────────────────────────────────▼─────────┐  │
│  │                   PS↔PL AXI Interfaces                      │  │
│  │  HPC0/1 (coherent), HP0/1/2/3 (non-coherent),              │  │
│  │  ACP (coherent), ACE-Lite (coherent), GP ports             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Platform Management Unit (PMU)                              │  │
│  │  • MicroBlaze-based, dedicated boot + power manager          │  │
│  │  • Power domains: APU, RPU, GPU, PL, FPD, LPD               │  │
│  │  • Secure/non-secure partition                               │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AXI Port Inventory — Coherent vs Non-Coherent

MPSoC expands Zynq-7000's port count dramatically and introduces **coherent HPC ports**:

| Port | Direction | Width | Bandwidth | Coherent? | Notes |
|---|---|---|---|---|---|
| **S_AXI_HPC0_FPD** | PL → DDR slave | 128-bit | 9,600 MB/s | **Yes** (via CCI-400) | High-Performance Coherent port #0 |
| **S_AXI_HPC1_FPD** | PL → DDR slave | 128-bit | 9,600 MB/s | **Yes** (via CCI-400) | High-Performance Coherent port #1 |
| **S_AXI_HP0_FPD** | PL → DDR slave | 128-bit | 9,600 MB/s | No | Non-coherent, lower latency |
| **S_AXI_HP1_FPD** | PL → DDR slave | 128-bit | 9,600 MB/s | No | Non-coherent |
| **S_AXI_HP2_FPD** | PL → DDR slave | 128-bit | 9,600 MB/s | No | Non-coherent |
| **S_AXI_HP3_FPD** | PL → DDR slave | 128-bit | 9,600 MB/s | No | Non-coherent |
| **S_AXI_ACP_FPD** | PL → CCI-400 | 128-bit | — | Yes | Legacy ACP (superseded by HPC) |
| **S_AXI_ACE_FPD** | PL → CCI-400 | 128-bit | — | Yes + snoop filter | AXI Coherency Extension |
| **M_AXI_HPM0_FPD** | PS → PL master | 32/64/128-bit | — | No | CPU-initiated access to PL |
| **M_AXI_HPM1_FPD** | PS → PL master | 32/64/128-bit | — | No | Second independent PS→PL master |
| **S_AXI_LPD** | PL → LPD slave | 32/64-bit | — | No | Low-Power Domain (RPU, peripherals) |

### The CCI-400 Difference

Unlike Zynq-7000's SCU+PL310, MPSoC uses ARM's **CCI-400** (Cache Coherent Interconnect):

```
                         ┌─────────────┐
   APU L2 (1 MB) ───────┤             │
   RPU TCM (256 KB) ────┤   CCI-400   ├──── DDR Controller
   HPC0 (FPGA) ─────────┤  Snoop Filter├──── HPC1 (FPGA)
   ACP (FPGA) ──────────┤             ├──── ACE (FPGA)
                         └─────────────┘
```

**Key advantage over Zynq-7000 SCU**: The CCI-400 snoop filter tracks which cache lines are in which master's cache, avoiding broadcast snoops. Zynq-7000's SCU snoops both L1 caches on every ACP transaction. CCI-400 only snoops if the line might be cached — significantly better throughput at scale.

---

## Heterogeneous Processing — APU + RPU

MPSoC's unique value proposition is running Linux on the APU (A53s) and bare-metal/RTOS on the RPU (R5Fs) **simultaneously**, with the FPGA as a shared accelerator:

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  ┌──────── APU (Application) ────────┐                │
│  │  Linux on 4× Cortex-A53           │                │
│  │  • Userspace apps                 │                │
│  │  • Networking, filesystem         │                │
│  │  • FPGA Manager                   │                │
│  │  • OpenAMP → talks to RPU         │                │
│  └──────────────┬────────────────────┘                │
│                 │                                     │
│  ┌──────────────▼────────────────────┐                │
│  │         Shared Resources           │                │
│  │  DDR (partitioned), interrupts,    │                │
│  │  AXI ports, PL configuration       │                │
│  └──────────────┬────────────────────┘                │
│                 │                                     │
│  ┌──────────────▼──────── RPU (Real-Time) ────┐      │
│  │  FreeRTOS / bare-metal on 2× Cortex-R5     │      │
│  │  • Deterministic (<1 µs response)          │      │
│  │  • Motor control, safety-critical IO       │      │
│  │  • Tightly-Coupled Memory (TCM) 256 KB     │      │
│  │  • Can run lockstep for safety (ISO 26262) │      │
│  └─────────────────────────────────────────────┘      │
│                                                       │
│  ┌─────────── FPGA Fabric (PL) ───────────────┐       │
│  │  Shared accelerator for both APU and RPU    │       │
│  │  DMA engines, DSP pipelines, custom logic  │       │
│  └─────────────────────────────────────────────┘       │
└───────────────────────────────────────────────────────┘
```

| Criterion | APU (Cortex-A53) | RPU (Cortex-R5) |
|---|---|---|
| Architecture | ARMv8-A (64-bit) | ARMv7-R (32-bit) |
| Cores | 4 (SMP) | 2 (SMP or lockstep) |
| Clock | 1.2–1.5 GHz | 500–600 MHz |
| OS | Linux, VxWorks | FreeRTOS, bare-metal, VxWorks |
| Cache | 32KB L1 + 1MB L2 | 32KB L1 I/D + 256KB TCM |
| Use Case | Application processing, networking, UI | Real-time control, safety, low-latency IO |
| Interrupt latency | ~10–50 µs (Linux) | <1 µs (bare-metal) |

---

## Boot Flow — PMU-Orchestrated

MPSoC adds a **Platform Management Unit** (PMU) — a dedicated MicroBlaze processor that manages the boot sequence before any application core starts:

```
Power-On Reset
      │
      ▼
┌──────────────────────┐
│ PMU Boot ROM          │  PMU is first to execute
│ • Releases PS reset   │  Reads boot mode from eFUSE/straps
│ • Loads CSU firmware  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ CSU (Configuration    │
│  Security Unit)       │  • AES-GCM + RSA-4096 authentication
│ • Authenticates FSBL  │  • Decrypts FSBL if encrypted
│ • Loads FSBL to OCM   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ FSBL (ARM Trusted     │  First user code on APU
│  Firmware — ATF)      │  • Initializes DDR, clocks, PLLs
│ • Loads PMU Firmware  │  • MAY configure PL
│ • Loads U-Boot (or    │  • Secure/non-secure partition
│   direct Linux boot)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ U-Boot (SSBL)         │  Optional if FSBL boots Linux directly
│ • FPGA configuration  │
│ • Load kernel + DTB   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Linux + RPU firmware  │  APU runs Linux, RPU runs RTOS/bare-metal
│ • FPGA Manager        │
│ • OpenAMP for APU↔RPU │
└──────────────────────┘
```

| Boot Mode | Media | Notes |
|---|---|---|
| SD Card | SD 3.0 | Primary development mode |
| QSPI | 24/32-bit QSPI NOR | Production, fast boot |
| NAND | 8/16-bit NAND | Large capacity |
| eMMC | eMMC 5.1 | Production, wear-leveling |
| JTAG | — | Debug |

---

## Power Domains — Fine-Grained Control

MPSoC splits the PS into independently controllable power domains:

| Domain | Contains | Can be gated? |
|---|---|---|
| **FPD** (Full-Power Domain) | APU (A53s), GPU, CCI-400, DDR, HP/HPC ports | Yes (suspend) |
| **LPD** (Low-Power Domain) | RPU (R5Fs), PMU, CSU, low-speed peripherals | No (always-on) |
| **PL** (Programmable Logic) | FPGA fabric, transceivers | Yes (off by default) |

The PMU manages these transitions. At boot, only LPD is powered. FPD and PL are powered on in stages. This enables deep-sleep modes: gate FPD and PL, keep LPD alive to wake on interrupt from always-on peripherals.

---

## MPSoC vs Zynq-7000 vs Cyclone V SoC

| Criterion | Cyclone V SoC | Zynq-7000 | Zynq MPSoC |
|---|---|---|---|
| CPU | 2× Cortex-A9 (32-bit) | 2× Cortex-A9 (32-bit) | 4× Cortex-A53 (64-bit) + 2× Cortex-R5 |
| Max clock | 925 MHz | 866 MHz | 1.5 GHz |
| Coherency | None | SCU + PL310 (ACP) | CCI-400 + snoop filter |
| Coherent FPGA ports | 0 | 1 (ACP, 64-bit) | 2 (HPC, 128-bit) + ACP + ACE |
| GPU | None | None | Mali-400 MP2 |
| Video codec | None | None | H.264/H.265 (VCU) |
| Max FPGA LEs | 301K | 444K | 1,143K |
| Max transceiver speed | 6.144 Gbps | 12.5 Gbps | 28.2 Gbps (GTY) |
| DDR | DDR3/DDR3L | DDR3/DDR3L/LPDDR2 | DDR4/LPDDR4 with ECC |
| Secure boot | — | AES-256 | AES-GCM + RSA-4096 |
| Power management | Coarse | Coarse | PMU-controlled fine-grained |
| Process | 28nm | 28nm | 16nm FinFET |

---

## Best Practices

1. **HPC for coherent, HP for streaming** — same ACP/HP logic as Zynq-7000 but with 128-bit ports and 8× more bandwidth.
2. **RPU for real-time, APU for Linux** — the killer MPSoC feature. Offload hard-real-time tasks to R5F cores in lockstep for safety.
3. **Use PMU for power sequencing, not manual register writes** — let the PMU firmware manage power domains.
4. **FSBL → ATF → U-Boot chain is deeply vendor-specific** — don't try to replace FSBL with a generic bootloader.
5. **LPD peripherals stay alive in sleep** — design always-on wake sources (UART, GPIO) in the LPD domain.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| PL not powered before access | AXI bridge timeout | PMU must enable PL power island first |
| HPC bandwidth lower than expected | ~2 GB/s vs 9.6 GB/s theoretical | Check CCI-400 QoS register settings; unfair arbitration starves HPC |
| RPU and APU DDR overlap | Corruption | Partition DDR in device tree; use reserved-memory for RPU |
| Secure boot blocks debug | JTAG locked out | Set boot mode to JTAG or use RSA authentication bypass in dev |
| VCU not clocked | Codec IP greyed out | VCU needs separate PLL; check clock wizard in Vivado |

---

## References

| Source | Link |
|---|---|
| Zynq UltraScale+ MPSoC Technical Reference Manual (UG1085) | [AMD Docs](https://docs.amd.com/r/en-US/ug1085-zynq-ultrascale-trm) |
| Zynq UltraScale+ MPSoC Data Sheet (DS925) | AMD/Xilinx documentation |
| ARM CCI-400 Technical Reference Manual | ARM documentation |
| PMU Firmware User Guide | AMD/Xilinx documentation |
| PetaLinux Tools for MPSoC | AMD/Xilinx documentation |

> **Related:** [Zynq-7000 SoC Deep Dive](../../7series/soc/README.md) | [PolarFire SoC (RISC-V)](../../../microchip/polarfire/soc/README.md) | [SoC Architecture Overview](../../../../02_architecture/soc/README.md)
