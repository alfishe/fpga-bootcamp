[← 12 Open Source Open Hardware Home](../README.md) · [← Initiatives Home](README.md) · [← Project Home](../../../README.md)

# OpenTitan — Open-Source Silicon Root of Trust

OpenTitan is the first open-source silicon Root of Trust (RoT) — a collaboration between lowRISC and Google to build a transparent, auditable security chip foundation.

---

## What is a Root of Trust?

A RoT is the foundational security component in a system — it verifies that boot firmware hasn't been tampered with before the main CPU runs. Every secure boot chain needs one.

OpenTitan's value: **every line of RTL, firmware, and documentation is open** — unprecedented transparency for a security chip.

## Architecture

| Component | Implementation |
|---|---|
| **CPU** | Ibex (RISC-V RV32IMC, 2-stage) |
| **Crypto Engine** | AES (128/192/256), HMAC, KMAC, SHA-3 |
| **Entropy Source** | Physical unclonable function (PUF) + conditioning |
| **OTP Memory** | One-time programmable, stores device secrets |
| **Secure Storage** | Isolated flash partition, key manager |
| **Alert System** | Hardware-level tamper detection |
| **Peripherals** | SPI host, I²C host/device, UART, GPIO, pinmux |

## FPGA Targets

| Board | FPGA | Use Case |
|---|---|---|
| **ChipWhisperer CW310** | Kintex-7 XC7K410T | Primary development target |
| **Nexys Video** | Artix-7 XC7A200T | Alternate dev board |

## Why It Matters for FPGA Developers

1. **Transparent security**: Every security mechanism is documented and auditable — unlike proprietary TPMs/secure elements
2. **RISC-V + Ibex**: A real-world example of a production-hardened open RISC-V core running security firmware
3. **Test infrastructure**: OpenTitan's DV (design verification) methodology is a model for how to verify security-critical FPGA designs
4. **Hardware/software co-design**: Shows how to architect a chip where firmware and hardware are co-designed around security invariants

---

## Original Stub Description

**OpenTitan** — lowRISC + Google, first open-source silicon root of trust (RoT), RISC-V Ibex core, FPGA targets (CW310/Nexys Video), transparent security design

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
