[← 12 Open Source Open Hardware Home](../README.md) · [← Initiatives Home](README.md) · [← Project Home](../../../README.md)

# FOSSi Foundation & CHIPS Alliance

The two major non-profit organizations driving open-source silicon: FOSSi (community-focused) and CHIPS Alliance (Linux Foundation, corporate-backed).

---

## FOSSi Foundation

**fossi-foundation.org** — Founded 2015, the grassroots organization for open-source silicon.

| Activity | Description |
|---|---|
| **ORConf** | Annual open-source digital design conference (Europe, ~200+ attendees) |
| **Latch-Up** | Portland, OR — North American counterpart of ORConf |
| **LibreCores** | Directory/registry of open-source IP cores (librecores.org) |
| **Google Summer of Code** | Mentors FPGA/RTL/VLSI student projects each year |
| **FOSSi Dial-Up** | Monthly virtual meetup since 2020 |

## CHIPS Alliance

**chipsalliance.org** — A Linux Foundation project, founded 2019, backed by Google, Intel, SiFive, Western Digital.

| Project | Description | FPGA Relevance |
|---|---|---|
| **Rocket Chip** | RISC-V SoC generator (Chisel) | Can target Kintex-7 / large FPGAs |
| **Chisel/FIRRTL** | Hardware construction language | FPGA + ASIC, Chisel → Verilog |
| **Verilator** | Fast open-source Verilog simulator | Critical for FPGA simulation |
| **OpenROAD** | Digital ASIC flow (RTL → GDS) | ASIC focus, but PDK concepts transfer |
| **FuseSoC** | IP package manager / build system | Directly used in FPGA projects |
| **Cocotb** | Python-based verification | FPGA verification framework |
| **SV-Tests** | SystemVerilog compliance test suite | Validates open-source SV tools |

## Relationship Map

```
FOSSi Foundation            CHIPS Alliance
(fossi-foundation.org)      (chipsalliance.org)
       │                           │
       ├─ ORConf ◄─────────────── shared events (co-located)
       ├─ LibreCores ◄─────────── core registry
       │                           │
       └─ community grassroots     ├─ corporate backing (Google, Intel)
                                   ├─ Verilator, Cocotb, FuseSoC → used by all FPGA devs
                                   └─ OpenROAD → ASIC, less FPGA-specific
```

Both organizations share many contributors and projects. **Verilator**, **Cocotb**, and **FuseSoC** are CHIPS Alliance projects used daily by the broader FOSSi community.

---

## Original Stub Description

**FOSSi Foundation** (ORConf, Latch-Up, LibreCores), **CHIPS Alliance** (Linux Foundation, Rocket Chip, Chisel, Verilator, OpenROAD), relationship map

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
