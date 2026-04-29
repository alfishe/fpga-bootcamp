[← 06 Ip And Cores Home](../README.md) · [← Vendor Ip Home](README.md) · [← Project Home](../../../README.md)

# Microchip FPGA IP — Libero SoC SmartDesign

Microchip's IP integration uses SmartDesign, a block-diagram tool within Libero SoC. The IP catalog targets Microchip's niches: radiation-tolerant space, defense, security, and industrial safety.

---

## SmartDesign Architecture

```
Libero SoC → SmartDesign
    │
    ├─ Drag IP from catalog
    ├─ Connect via CoreAXI / CoreAHB / CoreAPB
    ├─ Configure parameters
    └─ Generate HDL wrapper
```

---

## Bus Fabric (CoreAXI / CoreAHB / CoreAPB)

Microchip uses ARM AMBA buses (not Avalon, not standard AXI):

| Bus | Use Case |
|---|---|
| **CoreAXI** | High-performance memory-mapped (DDR, DMA) |
| **CoreAHB** | Mid-performance peripherals |
| **CoreAPB** | Low-speed register access |

---

## Key IP Categories

| Category | IP Blocks | Notes |
|---|---|---|
| **Processors** | ARM Cortex-M3 (hard on SmartFusion2), RV64 (hard on PolarFire SoC), Core8051s | Hard CPUs are the differentiator |
| **Memory Controllers** | DDR2/3/4, LPDDR3/4 | Full-featured, good performance |
| **PCIe** | Gen2 x1/x4 (PolarFire) | Hard IP |
| **Ethernet** | 10/100/1000 MAC, XAUI (10G) | Soft MAC + hard XAUI PCS on PolarFire |
| **Security** | AES-256, SHA-256, ECC, TRNG, PUF | Microchip's biggest differentiator — defense-grade security |
| **DSP** | FFT, FIR, CORDIC | Standard DSP blocks |
| **Space/Mil** | SEU-hardened FFs, TMR voters, EDAC | For radiation environments |

---

## PolarFire SoC Hard IP Advantage

PolarFire SoC integrates hardened blocks that save significant FPGA resources:

| Hard IP | Function | LUT Savings |
|---|---|---|
| **RV64IMAFDC (5 cores)** | Application processors | 50K+ LUTs vs soft RISC-V |
| **DDR4 Controller** | Memory controller | 10K+ LUTs vs soft |
| **PCIe Gen2** | Root complex or endpoint | 15K+ LUTs vs soft |
| **Crypto (AES, SHA, ECC)** | Hardware acceleration | 20K+ LUTs vs soft crypto |

---

## Best Practices

1. **Use hard Cortex-M3 on SmartFusion2** — free LUTs for your logic, not the CPU
2. **Leverage crypto blocks** — Microchip's security IP is defense-grade, no need to implement your own
3. **SmartDesign is GUI-heavy** — for CI, script with Libero Tcl commands

---

## References

- Microchip Libero SoC User Guide
- Microchip SmartFusion2 / PolarFire IP Catalog
- Microchip UG0663: SmartFusion2 Configuration Guide
