[← Verilog & SV Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# SystemVerilog

SystemVerilog is a hardware description and hardware verification language (HDVL). It unifies the capabilities of Verilog for digital design with advanced features for testbench automation, assertion-based verification, and constrained-random stimulus generation — all within a single, openly standardized language.

The current edition of the standard is IEEE 1800-2023, published in March 2024.

---

## Why SystemVerilog?

By the late 1990s, three separate languages were required in a typical ASIC design flow:

| Task | Language | Issue |
|---|---|---|
| **RTL Design** | Verilog, VHDL | Proprietary simulators, well-supported |
| **Verification stimulus** | Vera, e, proprietary C | Closed-source, expensive, non-standard |
| **Assertions / formal** | PSL (Property Specification Language), proprietary | Multiple competing standards, limited tool integration |

The result was **fragmentation**. Design teams needed three or more separate tools, and verification IP couldn't be shared across vendors. SystemVerilog was the answer: a single language with the same simulator, the same license, and a single vendor path.

---

## Lineage: Multiple Parents, One Language

SystemVerilog is not a simple "Verilog 2.0." It is the product of merging **three** distinct language lineages into a single IEEE standard:

```
                          Verilog (1983–2005, IEEE 1364)
                               |
 Vera (Synopsys, 1990s) ───────┼─────── Superlog (Co-Design Automation, 1999)
                               |
                    Accellera SystemVerilog 3.0 (2003)
                               |
                    IEEE 1800-2005 (first formal standard)
                               |
                    IEEE 1800-2009 ... 1800-2023
```

### Vera (Synopsys)

Vera was a proprietary verification language developed by Synopsys in the 1990s. It introduced **object-oriented testbench constructs**, **constrained-random stimulus generation**, and **functional coverage** — concepts that were radically ahead of anything in plain Verilog. Synopsys donated key Vera intellectual property to Accellera for inclusion in SystemVerilog. The `rand`, `constraint`, `covergroup`, and `virtual interface` features in SystemVerilog trace directly to Vera.

### Superlog (Co-Design Automation)

Superlog was developed by Co-Design Automation (founded by Peter Flake and Simon Davidmann) in 1999. It was an ambitious attempt to create a "Verilog++" — extending Verilog with C-like structural enhancements while preserving full backward compatibility. Superlog contributed **interfaces**, **always_ff / always_comb / always_latch**, **enumerated types**, and enhanced **tasks and functions** to the SystemVerilog language.

In 2002, Co-Design donated Superlog to Accellera, and this donation formed the technical foundation of SystemVerilog 3.0.

### Accellera as Integrator

Accellera (itself the product of OVI + VHDL International merger) acted as the integrator. The organization merged the Superlog design features with the Vera verification features and the base Verilog-2001 semantics to produce SystemVerilog 3.1 (2003) and 3.1a (2004). These became the baseline for IEEE 1800-2005.

---

## Major Version Timeline

| Version | IEEE Std | Year | Key Additions |
|---|---|---|---|
| **SV 3.0** | Accellera | 2003 | Interfaces, always_comb/ff/latch, enum, packages, $clog2 |
| **SV 3.1** | Accellera | 2003 | Classes, constraints, randomization, SVA (SystemVerilog Assertions) |
| **SV 3.1a** | Accellera | 2004 | Functional coverage, clocking blocks, virtual interfaces |
| **IEEE 1800-2005** | 1800-2005 | 2005 | First IEEE standard; unified the Accellera 3.1a spec |
| **IEEE 1800-2009** | 1800-2009 | 2009 | Merged Verilog 1364-2005; added `let`, `checker`, enhanced assertions |
| **IEEE 1800-2012** | 1800-2012 | 2012 | Multiple inheritance via interface classes, `sequence` enhancements |
| **IEEE 1800-2017** | 1800-2017 | 2017 | Nested modules in interfaces, new net types, `checker` enhancements |
| **IEEE 1800-2023** | 1800-2023 | 2024 | Errata corrections, PSL assertion integration, source-level tool directives |

> The **IEEE 1800-2009** merger was critical: all of Verilog became a legal subset of SystemVerilog. Every `module` written in Verilog-2001 is a valid SystemVerilog module.

---

## The Two Sides of SystemVerilog

One of SystemVerilog's defining characteristics is that it serves **two distinct purposes** within a single language specification. Most engineers specialize in one side and only dabble in the other.

### Side 1: Synthesis / Design (RTL)

The design subset contains constructs that describe synthesizable hardware. The key improvements over Verilog-2001:

| Feature | Verilog-2001 Equivalent | Benefit |
|---|---|---|
| **always_ff** | `always @(posedge clk)` | Catches missing edge in sensitivity list at compile time |
| **always_comb** | `always @*` | Automatic sensitivity and zero-delay loop guarantees (no simulation-synthesis mismatch); prohibits latches |
| **always_latch** | `always @*` with latched output | Declares intent; synthesizer verifies latch is intentional |
| **logic** type | `reg` + `wire` | Single 4-state type; eliminates reg/wire confusion |
| **enum** | `parameter` + `localparam` | Type-safe state machines; no more bare numeric state values |
| **struct** | Flattened `reg` vectors | Bundle related signals; pass through ports as single unit |
| **packages** | `` `include `` | Namespace management; import selectively |
| **interfaces** | Separate port wires | Bundle hundreds of bus signals; connect in one line |
| **generate** enhancements | `generate` existing in 2001 | Nested generates, `genvar` inside `always_comb` context |
| **unique/priority case** | Plain `case` | Synthesis directive: "this case is one-hot" or "this case has priority order" |

### Side 2: Verification (TB)

The verification side brings object-oriented programming into hardware simulation. These constructs **do not synthesize** — they exist only in simulation:

| Feature | Equivalent in Vera / e | What It Does |
|---|---|---|
| **class** | Object type in Vera | OOP: inheritance, polymorphism, encapsulation in testbench |
| **constraint + rand** | Constraint solver in Vera | Describe legal input values; solver finds random values within constraints |
| **covergroup + coverpoint** | Functional coverage in Vera/e | Measure what scenarios your tests actually exercise |
| **assertions (SVA)** | PSL / OVL / proprietary | Inline and concurrent property checks; formal and simulation |
| **virtual interface** | `virtual port` in Vera | Connect class-based testbench to module wires at elaboration |
| **mailbox / semaphore / event** | IPC primitives in Vera | Thread-to-thread communication in simulation |
| **DPI (Direct Programming Interface)** | PLI / VPI | Call C functions from SV, and vice versa — no PLI boilerplate |

---

## Synthesis Subset vs Full Language

A critical concept for FPGA developers: **only a subset of SystemVerilog is synthesizable**. The standard does not delimit this subset; it is defined by what each vendor's synthesis tool actually supports.

| Category | Synthesizable? | Example Constructs |
|---|---|---|
| always_ff / always_comb / always_latch | Yes (all vendors) | Flip-flops, combinational logic, intentional latches |
| enum / struct / packed | Yes (widely) | Type-safe states, bus bundles |
| interfaces (modports) | Yes (Vivado, Quartus) | Group and connect bus signals |
| packages | Yes (all) | Code reuse, namespace isolation |
| classes | **No** | Simulation-only OOP testbench |
| constraints / randomization | **No** | Constraint-driven stimulus |
| assertions (SVA) | **Partial** | Some SVA can be synthesized for in-hardware checks; most are simulation-only |
| functional coverage | **No** | Coverage metric only |

> **Vendor support varies.** Vivado tends to support more SystemVerilog synthesis constructs than Quartus. Always check your vendor's synthesis user guide for the specific supported subset.

---

## Comparison: Verilog vs SystemVerilog

| Aspect | Verilog-2001 | SystemVerilog |
|---|---|---|
| **IEEE standard** | 1364-2001 | 1800-2023 |
| **Design entry** | `wire`, `reg`, `always`, `assign` | Adds `logic`, `always_ff/comb/latch`, `enum`, `struct` |
| **Port connections** | Manual per-signal listing | `interface` bundles; connect in single line |
| **Testbench** | Procedural `initial` + `$display` | Classes, randomization, coverage, assertions |
| **Verification** | Not built-in; need Vera/e/PSL externally | Built-in SVA, covergroups, constraint solvers |
| **C interoperability** | PLI 1.0 (verbose) | DPI (one-line call) |
| **Backward compatibility** | N/A | All Verilog-2001 code is valid SystemVerilog |

---

## UVM and the Ecosystem

SystemVerilog's verification capabilities spawned **UVM** (Universal Verification Methodology), the industry-standard testbench framework. UVM is a class library written entirely in SystemVerilog and provides:

- **Sequences**: Generate and control stimulus flow
- **Drivers / Monitors**: Connect testbench to DUT pins
- **Scoreboards / Coverage**: Check results and measure progress
- **Configuration database**: Runtime parameterization without recompilation

UVM is the dominant methodology for ASIC and complex FPGA verification worldwide.

---

## Standing vs VHDL

SystemVerilog picks up where Verilog left off with respect to VHDL:

| Aspect | VHDL | SystemVerilog |
|---|---|---|
| **Type system** | Strict: every width mismatch is an error | Lenient: implicit truncation/widening unless linted |
| **Verification** | VHDL assertion statements + PSL | Integrated SVA + functional coverage + constraint solving |
| **Abstraction** | Entity/architecture separation | Module; interface for structural bundling |
| **Military/aerospace** | Required by Mil Std | Not mandated; commercial preferred |
| **Testbench framework** | OSVVM, UVVM (third-party) | UVM (first-party, part of the standard ecosystem) |

---

## Further Reading

| Resource | Description |
|---|---|
| [IEEE Std 1800-2023](https://ieeexplore.ieee.org/) | Free via IEEE Get Program since March 2024 |
| [Stuart Sutherland: SystemVerilog for Design, 2nd Ed.](https://sutherland-hdl.com/) | Synthesis-focused guide to synthesizable SV constructs |
| [Chris Spear: SystemVerilog for Verification, 3rd Ed.](https://www.amazon.com/SystemVerilog-Verification-Learning-Testbench-Language/dp/1461407141) | Standard verification textbook |
| [Doulos: SystemVerilog KnowHow](https://www.doulos.com/knowhow/systemverilog/) | Free articles, webinars, reference guides |
| [Accellera](https://www.accellera.org/) | Standards development organization (IEEE Get Program for free LRM) |
| [Verilog article](verilog_basics.md) | The parent language — what SystemVerilog builds upon |
| [HDL & Synthesis Home](../README.md) | Cross-HDL topics: inference rules, CDC, pragmas |
