[← VHDL Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# VHDL

VHDL (VHSIC Hardware Description Language) is a hardware description language that models the behavior and structure of digital systems. It was the first HDL to become an IEEE standard and remains dominant in defense, aerospace, and European FPGA design.

---

## Origin: The VHSIC Program

VHDL was born from a crisis. By the late 1970s, the U.S. Department of Defense (DoD) faced what was called the **hardware life-cycle crisis**:

- Electronic components in military systems became **obsolete faster than replacements could be procured**
- Each contractor used its own **proprietary simulation language** and toolchain
- There was **no portable documentation format** — the function of a circuit existed only in the specific simulator's representation, not as a transferable specification

In 1981, the DoD launched the **VHSIC** program (Very High-Speed Integrated Circuits) with a mandate that included creating a common hardware description language. The requirement was:

> A language with a wide range of descriptive capability that works the same on any simulator, independent of technology or design methodology.

Three contractors led the development:

| Organization | Role |
|---|---|
| **IBM** | Language design and formal specification |
| **Texas Instruments** | Hardware design and verification test cases |
| **Intermetrics** | Compiler and language tooling infrastructure |

The language drew heavily on **Ada** — the DoD's standard programming language — for its syntax, strong typing philosophy, and package/module architecture.

---

## The Road to IEEE and Industry Adoption

### Version 7.2 Milestone (1985)

A baseline language definition (VHDL 7.2) was published **two years before** the formal IEEE standard. This unusual step allowed EDA tool vendors to begin developing commercial VHDL simulators before the standard was finalized. By the time IEEE 1076-1987 was ratified, multiple simulators were ready.

### Unique IP Release

The DoD gave away **all rights** to the VHDL language definition to the IEEE, making it an open standard with no government ownership. This was a decisive move: it encouraged EDA industry investment without fear of DoD licensing or control.

### ASIC Mandate (MIL-STD-454)

The DoD mandated that every ASIC delivered to the government must include a **comprehensive VHDL description**. This meant VHDL was used from the beginning to the end of the design process. The mandate created a generation of VHDL-literate design engineers across the defense industrial base.

---

## Major Version Timeline

| Version | IEEE Std | Year | Key Philosophy |
|---|---|---|---|
| **VHDL-1987** | 1076-1987 | 1987 | First IEEE standard; entity/architecture, strong typing baseline |
| **VHDL-1993** | 1076-1993 | 1993 | Shared variables, report statements, pulse rejection in timing, shift/rotate operators, group syntax, foreign attribute |
| **VHDL-2000** | 1076-2000 | 2000 | Protected types (key for OSVVM and shared code) |
| **VHDL-2002** | 1076-2002 | 2002 | Relaxed buffer port rules; minor clarifying changes |
| **VHDL-2008** | 1076-2008 | 2008 | **Major revision**: fixed-point and floating-point packages, enhanced generics, external names, PSL integration, enhanced bit string literals, `??` operator, `process(all)`, simplified sensitivity lists |
| **VHDL-2019** | 1076-2019 | 2019 | Interfaces (records in ports), conditional analysis (`if generate`, `if use`), file system API, OSVVM API interop, verification API improvements |

> **VHDL-2008 is the current practical baseline** for modern FPGA design, though many shops still target 1993 due to legacy reuse and older tool constraints. VHDL-2019 support is nascent — Vivado 2024.2 supports a readable subset; Quartus Prime Pro 24.3 supports most 2008 with partial 2019.

---

## Geographic Split: The VHDL/Verilog Divide

VHDL adoption follows a **stark geographic line** rooted in history:

| Region | Dominant HDL | Reason |
|---|---|---|
| **United States** | Verilog / SystemVerilog | Cadence commercial influence; Silicon Valley startup ecosystem |
| **Canada** | Verilog / SV | Northern California proximity, commercial ASIC flows |
| **Western Europe** | **VHDL** | DoD NATO influence, defense industry, strong Ada culture |
| **Eastern Europe** | VHDL + Verilog | Mixed; academic preference for VHDL |
| **South America** | **VHDL** | European engineering education lineage |
| **Southeast Asia / India** | VHDL + Verilog | Mixed; manufacturing-oriented |

On VHDLwhiz surveys in 2024, global search volume for Verilog is approximately **2x** that for VHDL, but VHDL remains stronger in defense/aerospace and European university curricula.

---

## Strong Typing: The Defining Design Philosophy

VHDL's most distinguishing feature from Verilog is its **strong type system**:

| Concept | VHDL | Verilog |
|---|---|---|
| **Vector assignment** | Width-mismatched assignment is a compile-time **error** | Implicitly truncates to LSBs (may produce warning) |
| **Signed vs unsigned** | Explicit `numeric_std` package; `signed` and `unsigned` types | Implicit from operators; context-dependent |
| **Enumerations** | Built-in enum types since 1987 | No enum until SystemVerilog (via parameter in Verilog-2001) |
| **Port modes** | `in`, `out`, `inout`, `buffer` — compiler-enforced | `input`, `output`, `inout` — looser rules for internal use |
| **Array direction** | `downto` vs `to` is part of the type | Direction not inherent in the vector concept |
| **Subtypes and constraints** | Rich `subtype` and range constraints on ports | No subtype concept; parameter-based sizing |

This rigor comes at a cost: VHDL code is more verbose. A simple FIFO might require 3–4x as many source lines as equivalent Verilog. The argument in return is **design correctness** — fewer simulation mismatches and fewer synthesis-tool bugs where two HDLs compile the same construct into different hardware.

---

## Levels of Abstraction in VHDL

VHDL supports three distinct coding styles, all permitted within the same architecture:

| Style | Description | Synthesis? |
|---|---|---|
| **Structural** | Instantiate components and wire them together; netlist-like | Yes (every component/entity must be synthesizable) |
| **Dataflow** | Concurrent signal assignment: `a <= b and c after 5 ns;` | Yes (minus `after` delays) |
| **Behavioral** | Process-based: `process(clk) begin` with if/case/for loops | Yes (within the synthesis-legal subset) |

---

## Synthesis Subset of VHDL

Not all VHDL is synthesizable. The synthesizable subset has grown across standards:

### Synthesizable (IEEE 1076.6 guidance)

| Construct | Status | Notes |
|---|---|---|
| `entity` / `architecture` | Always synthesizable | Fundamental design unit |
| `signal`, `variable`, `constant` | All synthesis | |
| `process` (clocked) | All synthesis | Edge-triggered logic |
| `process` (combinational) | All synthesis | Sensitivity list must be complete or use `(all)` in VHDL-2008 |
| `if / case / for` | All synthesis | Loop bounds must be resolvable at synthesis time |
| `generic` | All synthesis | Compile-time parameters |
| `generate` (for, if) | All synthesis | Replicate hardware, exclude conditionally |

### Not Synthesizable

| Construct | Why Not |
|---|---|
| `after`, `wait for` | Physical time not synthesizable; synthesizer ignores or errors |
| `file` type I/O | Simulation concept; no hardware equivalent |
| Access types (pointers) | Dynamic memory allocation has no corresponding hardware |
| Guarded signal assignment | Tri-state not supported inside FPGA fabric (IO pads only) |
| Waveforms (`<= a after 1 ns, b after 2 ns`) | Delay not synthesizable |

---

## VHDL-2008: The Modernization Leap

Before VHDL-2008, designers lived with significant limitations:

- No fixed-point arithmetic package: any DSP implementation required rolling your own integer scaling or the `ieee_proposed` add-on
- `process(all)` did not exist: every combinational process required manually listing every signal in the sensitivity list (a source of simulation-synthesis bugs)
- **External names** were impossible: you couldn't reference a signal deep inside a design hierarchy without bringing it out through ports
- Generic types were limited: you couldn't write a generic reusable component with flexible types

VHDL-2008 addressed all of these, and many more. The 2019 standard builds on this momentum adding interfaces, conditional compilation, and better C interop.

---

## Assertion-Based Verification

VHDL includes a **concurrent assertion statement** (built into the core since 1987) and **PSL** (Property Specification Language) integration since VHDL-2008. These are analogous to SVA in SystemVerilog but with a different syntax:

```vhdl
-- VHDL concurrent assertion
assert (req = '1' and ack = '0')
  report "Illegal protocol state: req and ack both high"
  severity error;

-- PSL property (VHDL-2008 and later)
-- psl property handshake is always (req -> next (ack));
```

Combined with third-party verification frameworks like **OSVVM** and **UVVM**, there is a capable VHDL-only functional verification path that mirrors UVM in SystemVerilog.

---

## Tools and Open Source Equivalents

| Category | Commercial | Open Source |
|---|---|---|
| Simulator | Questa SIM (Siemens), Riviera-PRO | GHDL, nvc |
| Synthesizer | Vivado, Quartus, Precision | Yosys with GHDL plugin |
| Linter | Aldec ALINT, Questa Lint | VSG (VHDL Style Guide) |
| Verification framework | OSVVM, UVVM | Open source libraries: OSVVM.org, UVVM.org |

GHDL and nvc are mature alternative simulators tackling full VHDL-2008 and partial 2019. The GHDL + Yosys synergy provides an open-source synthesis path from VHDL to FPGA netlist.

---

## Comparison: VHDL vs Verilog vs SystemVerilog

| Aspect | VHDL | Verilog / SV |
|---|---|---|
| Lineage | DoD VHSIC (1981), Ada heritage | Gateway (1983), C heritage |
| First IEEE Std | 1076-1987 | 1364-1995 |
| Type safety | Strong: every mismatch is an error | Weak / lenient: implicit conversion |
| Verification | Concurrent assertions + PSL, OSVVM/UVVM | SVA, functional coverage, UVM |
| Learning curve | Steep: verbose, strict | Shallow entry, harder to master |
| Design reliability | Compiler catches more errors early | Relies more on linting and code review |
| Primary market | Europe, defense, aerospace, automotive | North America, ASIC, startups, open source IP |
| Testbench abstraction | OSVVM (record-based, weakly typed) | UVM (full OOP, strongly typed) |

Neither language is "better" in absolute terms. The choice is path-dependent: what the team knows, what the ecosystem requires, and what the toolchain supports.

---

## Further Reading

| Resource | Description |
|---|---|
| [IEEE Std 1076-2019](https://standards.ieee.org/) | Current VHDL standard |
| [VHDL 2008: Just the New Stuff by Ashenden and Lewis](https://www.elsevier.com/books/vhdl-2008/ashenden/978-0-12-374249-0) | The definitive reference for VHDL-2008 features |
| [Doulos: VHDL KnowHow](https://www.doulos.com/knowhow/vhdl/) | Free technical articles and quick reference guides |
| [OSVVM](https://osvvm.org/) | Open Source VHDL Verification Methodology |
| [UVVM](https://uvvm.org/) | Universal VHDL Verification Methodology |
| [GHDL](https://github.com/ghdl/ghdl) | Open-source VHDL simulator with synthesis plugin for Yosys |
| [Verilog article](../verilog_sv/verilog.md) | Compare: the language war, from the other side |
| [SystemVerilog article](../verilog_sv/systemverilog.md) | Compare what the verification-unified language does |

---

## See Also

- [Synthesis overview](../../03_design_flow/synthesis.md) — how VHDL feeds into FPGA and ASIC synthesis flows
- [Vendor pragmas](../../vendor_pragmas.md) — synthesizer-specific attributes in VHDL
- [Inference rules](../../inference_rules.md) — what RTL pattern infers what hardware in both VHDL and Verilog
