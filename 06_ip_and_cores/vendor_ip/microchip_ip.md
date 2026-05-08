[← 06 IP And Cores Home](../README.md) · [← Vendor IP Home](README.md) · [← Project Home](../../../README.md)]

# Microchip FPGA IP — Libero SoC SmartDesign & CoreIP Catalog

Microchip's IP ecosystem is defined by its defense-grade security, radiation-tolerant design, and the SmartDesign block-diagram integration tool within Libero SoC. Unlike Xilinx and Intel, Microchip uses ARM AMBA buses (CoreAXI, CoreAHB, CoreAPB) as its primary interconnect fabric and integrates hardened ARM Cortex and RISC-V processors. The IP catalog targets Microchip's niche markets: space, defense, industrial safety, and secure communications — where SEU mitigation, TMR, and crypto acceleration matter more than raw LUT count.

> [!NOTE]
> For clock management IP (PLL, clock conditioning), see [Clock Management IP](../clocking_ip/clock_management_ip.md). For analog/mixed-signal capabilities (ADC, DAC, comparators), see [Analog/Mixed-Signal FPGA](../../02_architecture/hybrid/analog_mixed_signal.md). For safety-critical design (DO-254, TMR), see [Safety-Critical Design](../../16_advanced_topics/safety_critical_design.md).

---

## SmartDesign Architecture

SmartDesign is Microchip's block-diagram IP integration tool — conceptually similar to Xilinx Block Design or Intel Platform Designer, but with SmartDesign's own AMBA-centric approach.

```
Libero SoC → SmartDesign
    │
    ├─ Drag IP from CoreIP Catalog
    ├─ Connect via CoreAXI / CoreAHB / CoreAPB fabric
    ├─ Configure parameters (GUI or Tcl)
    ├─ Auto-generate HDL wrapper + address map
    └─ Export to synthesis (Synplify Pro or Microchip Synthesis)
```

### SmartDesign vs Xilinx Block Design vs Intel Platform Designer

| Feature | SmartDesign (Microchip) | Block Design (Xilinx) | Platform Designer (Intel) |
|---|---|---|---|
| Bus fabric | CoreAXI/CoreAHB/CoreAPB | AXI4 Interconnect | Avalon/MM |
| Processor integration | Cortex-M3, RISC-V U54/E51 | MicroBlaze, Cortex-A/R | Nios II/V, Cortex-A |
| Tcl scripting | Full Tcl API | Full Tcl API | Full Tcl API |
| Address map | Auto-generated | Auto-generated | Auto-generated |
| HDL export | Verilog/VHDL | Verilog/VHDL | Verilog/VHDL |
| CI/CD | Libero Tcl batch mode | Vivado batch mode | Quartus batch mode |

---

## Bus Fabric (CoreAXI / CoreAHB / CoreAPB)

Microchip uses ARM AMBA buses — not Avalon (Intel) or a proprietary bus. This means ARM's IP ecosystem is directly compatible.

| Bus | Width | Performance | Use Case | FPGA Families |
|-----|-------|-------------|----------|---------------|
| **CoreAXI4** | 32/64-bit | High (200+ MHz) | DDR, DMA, high-bandwidth peripherals | PolarFire, PolarFire SoC |
| **CoreAHB** | 32-bit | Mid (100+ MHz) | General peripherals, CPU subsystem | SmartFusion2, IGLOO2, PolarFire |
| **CoreAPB** | 8/16/32-bit | Low (50 MHz) | Register access, slow peripherals | All families |

### Bus Hierarchy

```
                    CoreAXI4
                   (high-perf)
                       │
           ┌───────────┼───────────┐
           │           │           │
       DDR Ctrl      DMA        PCIe
           │
     CoreAHB (mid-perf)
           │
     ┌─────┼──────┐
     │     │      │
   UART   SPI   Timer
     │
  CoreAPB (low-speed)
     │
   GPIO   I²C
```

---

## IP Catalog by Category

### Processors

| IP | Type | Families | LUT Savings vs Soft | Notes |
|---|---|---|---|---|
| **ARM Cortex-M3** | Hard (SmartFusion2) | SmartFusion2 | ~15K LUTs | 166 MHz, AHB bus, embedded Flash |
| **RISC-V U54 + E51** | Hard (PolarFire SoC) | PolarFire SoC | ~50K+ LUTs | 5-core: 4× U54 (RV64IMAC) + 1× E51 (monitor) |
| **Core8051s** | Soft | All | N/A | 8-bit MCU for legacy compatibility |
| **CoreRISCV** | Soft (Mi-V) | PolarFire, SmartFusion2 | N/A | RISC-V soft core for non-SoC devices |

> See [Hard Processor Integration](../../02_architecture/soc/hard_processor_integration.md) for CPU-FPGA coupling models.

### Memory Controllers

| IP | Description | Families | License |
|---|---|---|---|
| **DDR2/3 Controller** | Hard controller with calibration | SmartFusion2, IGLOO2 | Free |
| **DDR4/LPDDR4 Controller** | High-performance DDR4 with ECC | PolarFire, PolarFire SoC | Free |
| **Flash*Free** | eNVM controller for on-chip Flash | SmartFusion2, IGLOO2 | Free |

### PCIe

| IP | Description | Families | License |
|---|---|---|---|
| **PCIe Gen2 x1/x4** | Hard PCIe endpoint + DMA | PolarFire | Free |

### Ethernet

| IP | Description | Families | License |
|---|---|---|---|
| **10/100/1000 MAC** | Soft Tri-speed MAC | PolarFire, SmartFusion2 | Free |
| **XAUI MAC** | 10G XAUI with hard PCS | PolarFire | Free |

> See [Hard Ethernet MACs](../other_hard_ip/ethernet_mac.md) for cross-vendor MAC comparison.

### Security & Cryptography (Microchip's Differentiator)

| IP | Description | Families | License |
|---|---|---|---|
| **AES-256** | ECB/CBC/CTR/GCM encryption | PolarFire, SmartFusion2 | Free |
| **SHA-256** | Secure hash accelerator | PolarFire, SmartFusion2 | Free |
| **ECC** | Elliptic curve cryptography | PolarFire | Free |
| **TRNG** | True Random Number Generator | PolarFire, SmartFusion2 | Free |
| **PUF** | Physically Unclonable Function | PolarFire | Free |
| **Secure Boot** | Chain-of-trust from eNVM | All | Free |

> [!NOTE]
> Microchip's security IP is defense-grade. The AES-256, SHA-256, and TRNG blocks are hardened and certified. For commercial products requiring FIPS 140-2 compliance, Microchip's hardened crypto is significantly easier to certify than a soft-logic implementation.

### Space & Military (SEU Mitigation)

| IP | Description | Families | License |
|---|---|---|---|
| **SEU-hardened FFs** | Radiation-tolerant flip-flops | RTG4, RT PolarFire | Free |
| **TMR voters** | Triple Modular Redundancy voting logic | RTG4 | Free |
| **EDAC** | Error Detection And Correction (memory) | RTG4 | Free |
| **Scrubber** | Configuration memory scrubbing | RTG4 | Free |

> See [Safety-Critical Design](../../16_advanced_topics/safety_critical_design.md) for DO-254, SEU effects, TMR, and scrubbing patterns.

### DSP

| IP | Description | Families | License |
|---|---|---|---|
| **FFT** | Pipelined/burst FFT | PolarFire | Free |
| **FIR** | Configurable FIR filter | PolarFire | Free |
| **CORDIC** | Coordinate rotation | PolarFire | Free |

---

## PolarFire SoC Hard IP Advantage

PolarFire SoC integrates hardened blocks that save significant FPGA resources compared to soft implementations:

| Hard IP | Function | LUT Savings | Power Savings |
|---|---|---|---|
| **RV64IMAFDC (5 cores)** | Application processors | 50K+ LUTs vs soft RISC-V | ~2W vs soft |
| **DDR4 Controller** | Memory controller | 10K+ LUTs vs soft | ~0.5W vs soft |
| **PCIe Gen2** | Root complex or endpoint | 15K+ LUTs vs soft | ~1W vs soft |
| **Crypto (AES, SHA, ECC)** | Hardware acceleration | 20K+ LUTs vs soft | ~1.5W vs soft |
| **eNVM** | Embedded non-volatile memory | N/A (unique to Microchip) | Zero standby |

> PolarFire SoC is the only mid-range FPGA SoC with a hard RISC-V processor cluster. Other vendors (Xilinx, Intel) use ARM Cortex. If your project requires open-source ISA, PolarFire SoC is the natural choice.

---

## Libero SoC Tcl Scripting (CI/CD)

For continuous integration, script SmartDesign generation and synthesis:

```tcl
# Libero SoC Tcl: Generate SmartDesign and run synthesis
# Libero v2024.1

# Open project
open_project -project {my_design.prjx}

# Generate SmartDesign component
generate_component -component_name {my_soc} -recursive 1

# Run synthesis
run_tool -name {SYNTHESIZE}

# Run place and route
run_tool -name {PLACEANDROUTE}

# Export programming file
export_bitstream -file {my_design.bit}
```

---

## Best Practices

1. **Use hard Cortex-M3 on SmartFusion2** — free LUTs for your logic, not the CPU; the M3 has deterministic interrupt latency ideal for real-time control
2. **Leverage crypto blocks** — Microchip's security IP is defense-grade; no need to implement your own AES/SHA when hardened, certified blocks are free
3. **SmartDesign is GUI-heavy** — for CI, script with Libero Tcl commands (see example above)
4. **Use CoreAXI for high-throughput paths** — CoreAHB is sufficient for register access but lacks burst support; AXI4 handles DDR and DMA efficiently
5. **eNVM is unique** — SmartFusion2 and IGLOO2 have on-chip non-volatile Flash for secure boot and configuration storage; use it instead of external Flash when possible
6. **RTG4 for space** — if your design must survive radiation, RTG4's SEU-hardened flip-flops and TMR voters are production-proven; don't try to implement radiation mitigation in soft logic

---

## Pitfalls

### 1. CoreAHB Lacks Burst Support
CoreAHB (AHB-Lite) does not support burst transfers. If you connect a DDR controller behind a CoreAHB interconnect, you will get single-beat transfers only — destroying DDR throughput.

**Fix:** Use CoreAXI4 for any path involving DDR, DMA, or PCIe. Use CoreAHB only for low-speed peripherals.

### 2. PolarFire SoC RISC-V Boot is Multi-Stage
The 5-core RISC-V cluster on PolarFire SoC requires a multi-stage boot: eNVM → E51 monitor core → U54 application cores → Linux. This is more complex than ARM's single-stage U-Boot.

**Fix:** Use Microchip's provided SoftConsole examples and Hart Software Services (HSS) as your starting point. Do not attempt to write a custom boot loader from scratch.

### 3. SmartDesign Address Map Conflicts
When connecting multiple masters to the same CoreAXI interconnect, SmartDesign may generate overlapping address maps if you don't explicitly assign base addresses.

**Fix:** Always review the generated address map report before synthesis. Assign base addresses explicitly in SmartDesign or via Tcl.

---

## Cross-References

- Microchip Libero SoC User Guide
- Microchip SmartFusion2 / PolarFire IP Catalog (Microchip website)
- Microchip UG0663: SmartFusion2 Configuration Guide
- Microchip PolarFire SoC Documentation (UG0820)
- [Clock Management IP](../clocking_ip/clock_management_ip.md) — Clock conditioning and PLL
- [Analog/Mixed-Signal FPGA](../../02_architecture/hybrid/analog_mixed_signal.md) — ADC, DAC, comparators
- [Safety-Critical Design](../../16_advanced_topics/safety_critical_design.md) — DO-254, SEU, TMR
- [Hard Processor Integration](../../02_architecture/soc/hard_processor_integration.md) — CPU-FPGA coupling models
