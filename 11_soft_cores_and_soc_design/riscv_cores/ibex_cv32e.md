[← 11 Soft Cores And Soc Design Home](../README.md) · [← RISC-V Cores Home](README.md) · [← Project Home](../../../README.md)]

# Ibex / CV32E40P — Security-Hardened RISC-V Core

Ibex is a production-quality RV32IMCB core written in SystemVerilog, originally developed at ETH Zürich as "Zero-riscy" and now maintained by lowRISC as part of the OpenTitan project. It serves as the Root of Trust processor in Google's Titan security chip — making it the most security-audited and silicon-proven open RISC-V core available.

---

## Architecture

| Parameter | Value |
|---|---|
| **ISA** | RV32I/E + M + C + B (Zicsr, Zifencei, Zicntr) |
| **Pipeline** | 2-stage (micro/small) or 3-stage (maxperf with writeback) |
| **Register File** | Latch-based (FF-based option for FPGA) |
| **Multiplier** | Configurable: iterative (3-cycle), single-cycle (parallel) |
| **Bit Manipulation** | B extension (Zba, Zbb, Zbc, Zbs) — ratified + draft v0.93 |
| **PMP** | Up to 16 regions (NAPOT/NA4/TOR) |
| **Debug** | RISC-V debug spec v0.13 (JTAG), hardware breakpoints |
| **Security** | PMP, secure boot hooks, ECC on register file (CV32E40S variant) |

### Configuration Variants

| Config | ISA | Key Features | CoreMark/MHz | Area (Yosys kGE) | Verification |
|---|---|---|---|---|---|
| **micro** | RV32EC | Minimal, 2-stage, iterative mul | 0.904 | 16.85 | Red (minimal) |
| **small** | RV32IMC | 3-cycle mul, 2-stage | 2.47 | 26.60 | Green |
| **maxperf** | RV32IMC | 1-cycle mul, branch target ALU, writeback stage | 3.13 | 32.48 | Green |
| **maxperf-pmp-bmfull** | RV32IMCB | Full: PMP + B extension + writeback | 3.13 | 66.02 | Green |

> [!NOTE]
> The "micro" configuration (RV32EC) removes M extension and uses the E (embedded) variant with only 16 registers. This cuts area in half but is incompatible with standard RV32I software.

### Pipeline Detail

```
2-stage (micro/small):   IF (Fetch + Decode) → ID (Execute + Writeback)
3-stage (maxperf):      IF (Fetch + Decode) → ID (Execute) → WB (Writeback)
```

The writeback stage in `maxperf` enables operand forwarding (bypassing) that eliminates one stall cycle on data hazards, boosting IPC significantly.

```mermaid
graph LR
    IF["IF Stage\nFetch + Decode"] --> ID["ID Stage\nExecute + Writeback"]
    ID -- "maxperf: bypass" --> IF
    ID -- "maxperf: writeback stage" --> WB["WB Stage\nRegister Write"]
    WB -- "forward" --> ID
```

---

## CV32E Family Variants

The OpenHW Group maintains the **CORE-V** family of Ibex-derived cores with different specialization:

| Variant | Pipeline | Features | Target |
|---|---|---|---|
| **Ibex (original)** | 2-stage | RV32IMC, PMP optional | General embedded, OpenTitan |
| **CV32E40P (RI5CY)** | 4-stage | RV32IMFC + custom DSP extensions (post-increment, SIMD, MAC) | Higher performance, PULP platform |
| **CV32E40S** | 2-stage | RV32IM + PMP + ECC on regfile + security hardening | Safety-critical, automotive, OpenTitan RoT |
| **CV32E40X** | 4-stage | RV32IMC + eXtension interface for custom coprocessors | Custom accelerator integration |

**Key distinction:** CV32E40P adds DSP extensions from the PULP platform — SIMD, post-increment load/store, and hardware loops — that are not part of the standard RISC-V ISA. CV32E40S adds ECC and security hardening at the cost of performance.

---

## Security Features

Ibex's role as the OpenTitan Root of Trust processor demands rigorous security design:

### Physical Memory Protection (PMP)

PMP allows firmware to define memory regions with specific access permissions (R/W/X). In OpenTitan, PMP enforces:

- **ROM protection** — Boot firmware region is read-only and executable, preventing code injection
- **RAM no-execute** — Data memory is marked non-executable to prevent shellcode execution
- **Peripheral isolation** — Only privileged code can access security-critical peripherals

```
PMP Region Layout (OpenTitan example)
┌──────────────────────────────┐ 0x1000_0000
│ MMIO Peripherals (RW, M-mode)│  PMP Region 15
├──────────────────────────────┤ 0x4000_0000
│ RAM (RW, no-execute)         │  PMP Region 14
├──────────────────────────────┤ 0x1000_0000
│ ROM (RX, read+execute only)  │  PMP Region 0
└──────────────────────────────┘ 0x0000_0000
```

### Secure Boot Integration

Ibex's reset vector is configurable — in OpenTitan, it points to ROM that contains the boot ROM code. The boot ROM:

1. Verifies the first-stage bootloader signature using RSA-PSS or ECDSA
2. If verification passes, jumps to the bootloader
3. If verification fails, enters secure fault state (alert handler triggers)

### Alert Handler Interface

Ibex integrates with OpenTitan's alert handler to detect and respond to security violations:
- **Integrity errors** — ECC single-bit correction, double-bit detection
- **Access violations** — PMP violations trigger alerts
- **Glitch detection** — Critical signals have glitch detectors

### Countermeasures Against Physical Attacks

| Countermeasure | Target Attack |
|---|---|
| **Latched register file** | Reduces EM side-channel vs FF-based |
| **PMP + ePMP** | Prevents unauthorized memory access |
| **Scrambled SRAM** | Defends against bus probing |
| **Glitch detectors on clocks/resets** | Fault injection attacks |
| **Constant-time crypto** (in firmware) | Timing side-channel mitigation |

---

## FPGA Mapping

| FPGA | Configuration | LUTs | FFs | fmax | Notes |
|---|---|---|---|---|---|
| **Artix-7 (A100T)** | small (RV32IMC) | ~3,000 | ~1,800 | 100+ MHz | Ibex Demo System target |
| **Artix-7 (A100T)** | maxperf (RV32IMC) | ~4,000 | ~2,200 | 90+ MHz | Branch target ALU adds area |
| **Cyclone V** | small | ~2,800 ALMs | — | 80+ MHz | OpenTitan CW310 alternate |
| **Kintex-7 (K410T)** | maxperf-pmp-bmfull | ~6,000 | ~3,500 | 80+ MHz | OpenTitan CW310 primary target |

> [!WARNING]
> Ibex uses a **latch-based register file** by default (smaller area in ASIC). For FPGA, switch to the **FF-based register file** (`RegFileFF` parameter) — latches do not map well to FPGA LUT/FF pairs and cause timing issues.

### Ibex Demo System (Arty A7)

The Ibex repository includes a Demo System targeting the Digilent Arty A7:

```bash
# Build Ibex Demo System for Arty A7
git clone https://github.com/lowRISC/ibex.git
cd ibex
# Requires Vivado 2020.2+
make -C hw synthesize_top_vivado FPGA_TARGET=artya7
```

The Demo System includes: Ibex core, RISC-V debug module, UART, GPIO, SPI, timer, and 256 KB BRAM — enough to run bare-metal test programs and debug via OpenOCD over USB.

---

## Verification Methodology

Ibex is one of the most rigorously verified open-source CPU cores:

| Verification Method | Coverage |
|---|---|
| **RISC-V DV (Google)** | Random instruction generation, runs millions of test sequences |
| **Formal verification** | FPV proofs for pipeline control, PMP, and CSR logic |
| **RISC-V compliance tests** | Official ISA test suite — verifies instruction accuracy |
| **CoreMark / EMBench** | Performance benchmarking across configurations |
| **Co-simulation** | Spike ISA simulator reference model comparison |
| **Nightly CI** | ~50K+ test vectors per configuration per night |

### Verification Status by Configuration

- **Green** (small, maxperf): Near-complete verification, suitable for production use
- **Red** (micro): Minimal verification, experimental only
- The `maxperf-pmp-bmfull` configuration is verified for OpenTitan use but the B extension draft sub-extensions are not ratified

---

## When to Use / When NOT to Use

### When to Use

- **Security-critical designs** — PMP + formal verification + OpenTitan pedigree
- **Production ASIC** — Multiple tape-outs (Google Titan, OpenTitan chip)
- **Safety-critical applications** — CV32E40S variant with ECC and verification artifacts
- **RISC-V compliance testing** — Ibex passes the full official test suite

### When NOT to Use

- **You need maximum performance** — 3.13 CoreMark/MHz is modest; VexRiscv achieves higher IPC with deeper pipelines
- **You need 64-bit** — Ibex is RV32 only
- **You need FPU** — No floating-point support; use VexRiscv or CV32E40P (F extension)
- **You want minimal LUTs** — Ibex starts at ~3K LUTs; PicoRV32 fits in ~750

---

## Best Practices

1. **Use the FF-based register file for FPGA** — Set `RegFile` parameter to `RegFileFF`; latch-based register files cause FPGA timing problems
2. **Start from `small` configuration** — It's the best-verified; only move to `maxperf` if you need the writeback stage performance
3. **Enable PMP for any security application** — Without PMP, any code can access all memory; configure PMP regions in your boot firmware
4. **Use the Ibex Demo System as a reference integration** — Don't integrate Ibex from scratch; the Demo System shows correct clock/reset/debug wiring
5. **Pin your Ibex commit** — The `master` branch moves fast; tag a specific commit for production use

## Antipatterns

| Antipattern | Why It Fails | Correct Approach |
|---|---|---|
| **Using latch-based register file on FPGA** | Latches map to LUT+FF with poor timing and unreliable behavior | Set `RegFile = RegFileFF` for all FPGA targets |
| **Skipping PMP in a security design** | Without PMP, a compromised peripheral can overwrite boot ROM | Configure PMP regions before jumping to application code |
| **Using `micro` config for production** | Minimal verification (Red status); unknown bug surface | Use `small` (Green) even if you don't need M extension |
| **Assuming B extension is stable** | Draft v0.93 sub-extensions are not ratified; encoding may change | Use only the ratified sub-extensions (Zba, Zbb, Zbc, Zbs) |

---

## Pitfalls

### 1. Latch-Based Register File on FPGA

Ibex defaults to a latch-based register file for ASIC area savings. On FPGA, this causes:
- Incorrect inference — synthesis tools may not implement latches correctly
- Timing violations — latch timing is not well-analyzed by FPGA timing engines
- Increased resource usage — each latch costs ~2 LUTs vs 1 FF

**Fix:** Always set `RegFile` to `RegFileFF` for FPGA targets. The area increase is ~200 LUTs but timing is reliable.

### 2. SystemVerilog Compatibility

Ibex uses SystemVerilog features (interfaces, packages, enum types) that not all synthesis tools support equally:
- **Yosys**: Partial SV support; requires specific `read_systemverilog` flags or preprocessing
- **Vivado**: Full support (recommended)
- **Quartus**: Full support

**Fix:** Use Vivado or Quartus for synthesis. For Yosys, use the open-source Ibex synthesis flow or pre-process with Verible/SV2V.

### 3. Debug Module Integration

Ibex's debug module follows the RISC-V Debug Specification v0.13, but the integration is not trivial — the debug module requires a dedicated bus master port and specific clock domain handling.

**Fix:** Use the PULP RISC-V debug module from the Ibex Demo System, which handles the integration correctly.

---

## Use Cases

| Use Case | Configuration | Why Ibex |
|---|---|---|
| **OpenTitan Root of Trust** | maxperf-pmp-bmfull | Production silicon, security-audited, PMP, B extension for crypto |
| **Embedded controller** | small | Well-verified, modest area, sufficient for control tasks |
| **FPGA security module** | maxperf + PMP | Hardware isolation between trusted and untrusted code |
| **RISC-V learning/teaching** | small | Clean SystemVerilog codebase, extensive documentation |
| **Safety-critical (automotive)** | CV32E40S | ECC, PMP, ISO 26262 verification artifacts |

---

## Vendor Cross-Reference

| Feature | Ibex (SystemVerilog) | VexRiscv (SpinalHDL) | PicoRV32 (Verilog) | NEORV32 (VHDL) |
|---|---|---|---|---|
| **Language** | SystemVerilog | Scala → Verilog | Pure Verilog | Pure VHDL |
| **Min area** | ~3K LUTs | ~500 LUTs | ~750 LUTs | ~2K LUTs |
| **Security features** | PMP, ECC, glitch detect | None | None | Limited PMP |
| **Formal verification** | Extensive (FPV) | Limited | None | Limited |
| **Production ASIC** | Google Titan, OpenTitan | No tape-outs | No tape-outs | No tape-outs |
| **FPU** | No (CV32E40P has F) | F32/F64 | No | No |
| **Best for** | Security, ASIC, safety | Flexible SoC, Linux | Minimal control | Documentation |

---

## References

- [Ibex GitHub Repository](https://github.com/lowRISC/ibex) — source code, demo system, documentation
- [Ibex User Manual (ReadTheDocs)](https://ibex-core.readthedocs.io/) — configuration, integration, verification
- [OpenTitan Project](https://opentitan.org/) — production SoC using Ibex as RoT processor
- [OpenHW Group CV32E40P](https://github.com/openhwgroup/cv32e40p) — PULP DSP-enhanced variant
- [OpenHW Group CV32E40S](https://github.com/openhwgroup/cv32e40s) — safety/security variant
- [RISC-V Debug Specification v0.13](https://riscv.org/specifications/) — JTAG debug interface
- [RISC-V ISA](../riscv/riscv_isa.md) — instruction set reference
- [OpenTitan](../../../12_open_source_open_hardware/initiatives/opentitan.md) — open-source silicon root of trust
