[← Verilog & SV Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# Verilog

Verilog is a hardware description language (HDL) used to model, design, simulate, and synthesize digital electronic systems. Originally created as a proprietary simulation language, it became the industry's most widely adopted HDL and the foundation upon which SystemVerilog was built.

---

## Origin and History

### Birth at Gateway Design Automation (1983–1984)

Verilog was created in 1983–1984 by **Phil Moorby** and **Prabhu Goel** at Gateway Design Automation (GDA) in Acton, Massachusetts. It was originally designed as the input language for **Verilog-XL**, a logic simulator that was dramatically faster than existing gate-level simulators of the era. Moorby's key insight was to invent a *simulation language* that also served as a *design language* — the same description could be simulated and, later, synthesized into gates.

The language borrowed its syntactic style from **C**, making it accessible to engineers already familiar with C programming. It modeled hardware using three core abstractions that remain central today:

| Abstraction | Verilog Construct | What It Models |
|---|---|---|
| **Net** | `wire`, `tri` | Physical connections between gates; continuous assignment |
| **Register** | `reg` | Storage elements (flip-flops, latches) in procedural blocks |
| **Behavioral** | `always`, `initial` | Time-ordered procedural execution for simulation and modeling |

### Cadence Acquisition and Public Domain (1989–1990)

In 1989, **Cadence Design Systems** acquired Gateway Design Automation, gaining Verilog-XL and the Verilog language. The VHDL community, backed by the U.S. Department of Defense, was pushing aggressively; Cadence feared losing the language war. In 1990, Cadence placed Verilog into the **public domain**, making it openly available for anyone to implement, standardize, or extend.

This decision proved pivotal. It allowed competing simulator vendors to build Verilog tools and guaranteed the language a future beyond any single company.

### OVI, Accellera, and IEEE Standardization (1991–1995)

**Open Verilog International** (OVI) was formed in 1991 to steward the language toward IEEE standardization. OVI later merged with VHDL International to form **Accellera**, which continues to maintain Verilog and SystemVerilog standards today.

In December 1995, Verilog became **IEEE Std 1364-1995**, also known as **Verilog-95**. This was the first formal standard, codifying the language as it existed in practice.

### The Verilog-2001 Leap

The language was massively successful in ASIC design, and users identified many missing features. The IEEE working group split into three sub-teams:

| Sub-team | Focus | Key Deliverable |
|---|---|---|
| **ASIC Task Force** | Design productivity | ANSI-style module ports, `generate`, multi-dimensional arrays |
| **Behavioral Task Force** | Better modeling | `automatic` tasks/functions, `signed` arithmetic |
| **System Task Force** | File I/O, VCD, PLI | `$readmemh`, `$fopen/$fclose`, enhanced timing checks |

IEEE Std 1364-2001 (**Verilog-2001**) was the result, and it remains the **synthesis baseline** for nearly all FPGA and ASIC tool flows today. Almost every synthesizable Verilog design targets Verilog-2001 or a vendor subset of it.

### Merge with SystemVerilog (2009)

IEEE Std 1364-2005 made only minor corrections. In 2009, the IEEE formally merged Verilog (1364) into the SystemVerilog standard (**IEEE 1800-2009**). Verilog 1364 ceased to exist as an independent standard. All legal Verilog code is also legal SystemVerilog — SystemVerilog is a true syntactic superset.

---

## Language Philosophy

Verilog code looks like C, but it executes like hardware. This duality is the source of the most common beginner mistakes.

| Concept | Verilog | C / Software |
|---|---|---|
| **Execution model** | Concurrent by default (`always` blocks run in parallel) | Sequential instruction execution |
| **Assignment** | Non-blocking (`<=`) for sequential logic, blocking (`=`) for combinational | All assignments are blocking |
| **Time** | Physical time (`#5` = 5 time units), clock edges (`posedge clk`) | Queue time, event-driven |
| **4-value logic** | `0`, `1`, `x` (unknown), `z` (high-impedance) | Boolean only |

### Four Levels of Abstraction

Verilog supports design entry at multiple levels in a single file:

| Level | Abbreviation | Constructs | Typical Use |
|---|---|---|---|
| **Switch-level** | — | `tran`, `nmos`, `pmos` | Used for cell characterization, not synthesis |
| **Gate-level** | — | `and`, `or`, `not`, `buf`, instantiated primitives | Post-synthesis netlist, rarely hand-coded |
| **Dataflow (RTL)** | RTL | Continuous `assign`, operators (`+`, `*`, `?:`) | Typical for most FPGA design |
| **Behavioral** | RTL / Behavioral | `always @(posedge clk)`, `case`, `if-else` | Used for sequential logic and FSMs, synthesizable with care |

---

## Major Version Timeline

| Version | IEEE Std | Year | Key Contributions |
|---|---|---|---|
| **Verilog-95** | 1364-1995 | 1995 | First IEEE standard; `wire`, `reg`, `always`, `initial`, `module`, `$display`, PLI 1.0 |
| **Verilog-2001** | 1364-2001 | 2001 | ANSI C-style ports, `generate`, `signed` arithmetic, `automatic` tasks, multi-dimensional arrays, enhanced file I/O, `@*` wildcard sensitivity list |
| **Verilog-2005** | 1364-2005 | 2005 | Minor corrections and clarifications only |
| **Merged into SV** | IEEE 1800 | 2009 | Verilog becomes a subset of SystemVerilog; independent 1364 designation retired |

> **Verilog-2001 is the synthesis baseline.** No major FPGA vendor synthesizer targets plain Verilog-95 today. If you write `always @(a or b or c)` instead of `always @*`, you are writing Verilog-95.

---

## Companion Standards and Extensions

### Verilog-AMS

**Verilog-AMS** (Analog and Mixed-Signal) extends Verilog with constructs for modeling continuous-time and mixed-signal systems — voltage, current, frequency response, and discrete-event interaction. It is used in mixed-signal ASIC verification (`wreal` models) but is not synthesizable.

| Standard | Name | Domain |
|---|---|---|
| IEEE 1364-1995/2001/2005 | Verilog | Digital |
| Accellera Verilog-AMS 2.4 | Verilog-AMS | Analog + Mixed-Signal |
| IEEE 1800-2023 | SystemVerilog | Digital (superset) |

### Open-Source Simulation: Icarus Verilog, Verilator

The public-domain release enabled open-source implementations:

| Tool | Type | Notes |
|---|---|---|
| **Icarus Verilog** | Simulator | Full IEEE 1364-2005, partial SystemVerilog |
| **Verilator** | Verilog → C++ compiler | Cycle-accurate, extremely fast; offers SystemVerilog synthesis subset |
| **Yosys** | Synthesis | Verilog-2005 synthesis input, some SV constructs |

---

## Regional and Industry Adoption

Verilog dominates in:

- **North America**: U.S. semiconductor and FPGA companies overwhelmingly prefer Verilog/SystemVerilog
- **ASIC design**: Virtually all commercial ASIC flows run on Verilog or SystemVerilog
- **Startup / IP ecosystem**: Most commercial IP cores are delivered in Verilog
- **Generative/script-generated HDL**: C-like syntax makes Verilog easier to emit from Python/Perl generators

VHDL remains stronger in:

- **Europe**: Defense, aerospace, and automotive prefer VHDL for its strong typing and DoD heritage
- **Safety-critical systems**: The strong type system reduces design errors
- **FPGA prototype education**: Many European universities teach VHDL first

On GitHub as of 2024, open-source Verilog repositories outnumber VHDL repositories roughly 2:1. For FPGA-only projects, the gap narrows to approximately 1.5:1.

---

## Historical Context

Verilog was not the first HDL. It coexists with a long lineage:

| Language | Era | Description |
|---|---|---|
| **PALASM** | 1978 | First widely used HDL; fuse-map equations for PALs |
| **ABEL** | 1983 | Data I/O; truth tables, state diagrams for CPLDs |
| **AHDL** | 1990s | Altera proprietary; Boolean equations + state machines |
| **VHDL** | 1987 (IEEE) | U.S. DoD VHSIC program; Ada-based, strongly typed |
| **Verilog** | 1995 (IEEE) | Gateway/Cadence; C-like, event-driven |
| **SystemVerilog** | 2005 (IEEE) | Verilog + Superlog + Vera; unified design+verification |
| **SystemC** | 2005 (IEEE) | C++ class library for system-level modeling |

---

## Further Reading

| Resource | Description |
|---|---|
| [IEEE Std 1364-2001](https://ieeexplore.ieee.org/) | Verilog-2001 Language Reference Manual (the synthesis benchmark) |
| [Stuart Sutherland: Verilog HDL Quick Reference Guide](https://sutherland-hdl.com/) | Compact guide to synthesizable Verilog |
| [Samir Palnitkar: Verilog HDL, 2nd Ed.](https://www.amazon.com/Verilog-HDL-Samir-Palnitkar/dp/0130449113) | Standard textbook, covers 1995/2001 |
| [Doulos: Verilog KnowHow](https://www.doulos.com/knowhow/verilog/) | Free technical articles |
| [SystemVerilog article](../verilog_sv/systemverilog.md) | Verilog's successor — what carries forward and what is new |
| [VHDL article](../../vhdl/vhdl_basics.md) | Comparison: turn the telescope around |
