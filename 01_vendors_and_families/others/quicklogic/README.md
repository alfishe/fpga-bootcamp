[← Others Home](../README.md) · [← Section Home](../../README.md)

# QuickLogic — Embedded FPGA (eFPGA) & Sensor Hubs

QuickLogic sells **embedded FPGA cores** (eFPGA) and low-power sensor hubs. The EOS S3 is the **only commercial FPGA with fully open-source bitstream documentation** — Google funded the SymbiFlow reverse-engineering effort and QuickLogic actively supports it.

---

## EOS S3 — Sensor Processing Platform

```
┌────────── EOS S3 Die ──────────┐
│  ┌─────────────┐               │
│  │ Cortex-M4F  │               │
│  │ 80 MHz       ├──► AHB Bus    │
│  └─────────────┘               │
│         │                      │
│  ┌──────▼──────────────────┐   │
│  │  Embedded FPGA (eFPGA)  │   │
│  │  916 LUT4 + 144 Kb RAM  │   │
│  │  + 8 DSP slices         │   │
│  │  Always-on, sub-µA       │   │
│  └─────────────────────────┘   │
└────────────────────────────────┘
```

| Feature | Specification |
|---|---|
| **eFPGA** | 916× 4-LUT + 8× DSP + 144 Kb RAM |
| **MCU** | ARM Cortex-M4F at 80 MHz |
| **Always-on power** | ~15 µW (mic wake-word detect) |
| **Open-source flow** | **SymbiFlow** — fully open-sourced bitstream documentation |

---

## Development Boards

### QuickLogic (First-Party)

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **QuickFeather Dev Kit** | EOS S3 | 916 + Cortex-M4F | Onboard sensors (mic, accel, pressure, temp), USB, GPIO, open-source SymbiFlow toolchain | ~$30 | Only board for EOS S3, open-source MCU+FPGA |

### Choosing a Board

| You want... | Get... |
|---|---|
| EOS S3 open-source eFPGA + MCU | QuickFeather (~$30) — the only option |

---

## References

| Source | Path |
|---|---|
| QuickLogic EOS S3 | https://www.quicklogic.com/products/eos-s3 |
| SymbiFlow for QuickLogic | https://symbiflow.readthedocs.io |
