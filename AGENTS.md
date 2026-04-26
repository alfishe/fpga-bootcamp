# AGENTS.md — Technical Article Quality Standards

> **Audience**: AI coding assistants and human contributors.
> Read this before writing or expanding any `.md` file in this repository.

---

## Language & Spelling

- **American English only** — `color`, `behavior`, `initialize`, never `colour`, `behaviour`, `initialise`
- Use clear, direct technical prose — no filler, no hedging, no marketing language
- Prefer active voice: "The PLL locks to the reference clock" not "The reference clock is locked to by the PLL"
- **Hexadecimal**: Use Verilog-style (`'hDEAD`) or C-style (`0xDEAD`) depending on context — be consistent within an article. For register addresses in datasheets, prefer the vendor's documented notation.

---

## Pre-Flight: Knowledge Base Scan (MANDATORY)

Before writing or expanding any article, you **must**:

1. **Read the root [README.md](README.md)** — it contains the full Documentation Map with every article in the repository. Understand what already exists to avoid duplicating content and to identify cross-linking opportunities.
2. **Scan the section's `README.md`** — know what sibling articles exist in the same folder. Your article should complement, not repeat, adjacent content.
3. **Search for related content** — use grep or file listing to find existing mentions of your topic across the repository. If another article already covers a subtopic in depth, link to it rather than rewriting it.
4. **Check for established patterns** — look at 2–3 exemplary articles in the repository (see "What Makes an Exemplary Article" below) to match style, depth, and structure.

> [!IMPORTANT]
> Every article must exist within the knowledge graph. Orphaned articles are unacceptable. Update the root README's Documentation Map when adding new articles.

---

## Article Structure

Every article must follow this skeleton. Omit sections that genuinely don't apply, but the **Overview** and **Navigation** are mandatory.

### 1. Navigation Breadcrumb (line 1)

```markdown
[← Home](../README.md) · [Section Name](README.md)
```

### 2. Title

Use a single `#` heading. Include the subject and a subtitle with key subtopics:

```markdown
# Clock Domain Crossing — Synchronizers, FIFOs, and Handshake Protocols
# Vivado Non-Project Mode — Tcl Scripting and CI/CD Integration
# AXI4-Lite Interconnect — Address Decoding and Arbitration
```

### 3. Overview

The first section after the title. Must answer in **one dense paragraph**:
- **What** is this subsystem/IP/feature?
- **Where** does it live in the system? (which vendor family, which tool, which layer)
- **Why** does it exist? What problem does it solve?
- **Key constraints** the reader must internalize immediately

Good example:
> The DSP48E2 slice is a hardened arithmetic unit in Xilinx 7-series and UltraScale+ FPGAs that performs 27x18 multiply-accumulate operations at the fabric clock rate. It exists because soft-multiplier implementations consume hundreds of LUTs and cannot match the speed or power efficiency of dedicated silicon. Every DSP48E2 shares input routing with adjacent slices and includes a 48-bit accumulator with pattern detection — understanding these coupling constraints is essential for high-performance filter design.

Bad example:
> This document describes the DSP48E2. The DSP48E2 is used for math.

### 4. Architecture / How It Works

- Use **Mermaid diagrams** for system relationships, data flows, and state machines
- Show where the component sits in the overall system (fabric, hard IP, tool flow)
- Explain the **hardware backing** — which silicon resources, which clock domains, what bus interactions
- For tool flows: show the pipeline stages and file artifacts at each step

### 5. Data Structures & Register Tables

- Show the **actual RTL struct/package** or **Linux kernel struct** with inline comments
- Follow with a **field description table** for non-obvious fields
- Include the source attribution: `/* linux/drivers/fpga/fpga-region.h */` or `/* Vivado IP XCI */`
- Annotate critical constraints inline: `/* Requires clock-enabled BRAM! */`
- **Hardware Registers / Pinouts**: Documentation must use the following table format, including the R/W capability:
  ```markdown
  | Offset    | Name      | R/W | Description |
  |-----------|-----------|-----|-------------|
  | `0x00`    | CTRL      | RW  | Control register: bit 0 = enable, bit 1 = reset |
  ```

### 6. API / Interface Reference

- Show function prototypes, module ports, or Tcl command signatures
- Include version/tool context: `/* Vivado 2023.2 */` or `/* Quartus Prime 23.1 */`
- Include practical usage snippets immediately after each prototype
- Group related functions/commands together

### 7. Decision Guides & Comparison Tables

When multiple approaches exist, provide a **decision matrix**:

```markdown
| Criterion | Option A | Option B |
|---|---|---|
| When to use | ... | ... |
| Limitation | ... | ... |
```

### 8. Vendor Context & Cross-Platform Comparison (MANDATORY)

This is **not optional** for any article covering a fundamental or architectural concept.

**Vendor perspective:**
- Include a **vendor comparison table** when discussing features that vary across Xilinx/Intel/Lattice/Gowin/Microchip
- Explain what makes each vendor's approach distinctive (or restrictive) relative to alternatives
- Provide **pros/cons analysis** in the context of cost, power, tooling quality, and ecosystem

**Open-source analogies:**
- Add a **comparison table** mapping vendor-tool concepts to open-source equivalents (Yosys vs Vivado, nextpnr vs Vivado PnR, LiteX vs Zynq)
- Explain **why** the analogy holds and where it breaks down
- Help developers build intuition by connecting proprietary workflows to open-source alternatives they may already know

### 9. Practical Examples

- Every article must include at least one **complete, working code example**
- Examples must be valid RTL, valid Tcl, or valid C — no pseudocode unless explicitly marked
- Show the full lifecycle: init → use → cleanup (or: instantiation → configuration → verification)
- Annotate non-obvious lines with inline comments

### 10. When to Use / When NOT to Use

Every IP, tool feature, or design pattern article must include explicit guidance on:
- **When to use** — the ideal scenarios, applicability ranges, sweet spots
- **When NOT to use** — situations where a different approach is better, with explanation of why
- **Applicability ranges** — quantify limits (e.g., "AXI4-Lite is suitable for register maps up to ~64 registers; beyond that, consider AXI4 full with burst support")

### 11. Best Practices & Antipatterns

- **Best practices**: Numbered list of actionable recommendations. Each item should be one line.
- **Antipatterns**: Common bad habits that compile/synthesize but produce subtle bugs, poor timing, or silicon inefficiency. Show the antipattern and the correct alternative side by side.

### 12. Pitfalls & Common Mistakes

- Use a dedicated **Pitfalls** section near the end
- Each pitfall gets a numbered subsection with:
  - A **bad code/example** showing the bug
  - An explanation of **why** it fails
  - The **correct** version

### 13. Use Cases

Provide real-world use cases that demonstrate practical application:
- What kind of designs use this feature?
- Which well-known open-source projects or commercial products relied on it?
- What are the common integration patterns?

### 14. FAQ (when topic resonates)

For topics that commonly generate questions (timing closure, CDC, DDR calibration, PCIe bringup), include a short FAQ section addressing the most frequent developer questions.

### 15. References

- Vendor documentation links (UG, DS, AC, PG, WP numbers where applicable)
- Cross-links to related articles in this repository
- External links where authoritative (RISC-V specs, Linux kernel docs, IEEE standards)
- Open-source project references (GitHub repos, commit hashes for reproducibility)

---

## Formatting Standards

### Memory Maps & Register Layouts

- When illustrating register maps, address spaces, or packet formats, use **monospace ASCII box-drawing** (`┌─┐`) rather than Mermaid flowcharts. Mermaid is for logic/state; ASCII boxes are for byte-precise memory layouts.
- For FPGA address maps, show base address, offset, and aperture size explicitly.

### Timing Diagrams

- Use ASCII timing diagrams or WaveDrom JSON snippets for signal timing relationships
- Include clock, data, valid, and ready signals where applicable
- Show setup/hold violation windows where relevant

### Tables

- Use tables for structured comparisons, flag lists, register maps, field descriptions
- Always include a header row and separator
- Keep cells concise — one concept per cell

### Code Blocks

- Use fenced code blocks with language tags: ` ```verilog `, ` ```vhdl `, ` ```tcl `, ` ```c `, ` ```python `
- Include source attribution in struct/module definitions
- Use `/* comment */` for inline annotations in RTL/C code
- Use `# comment` for Tcl and Python

### Mermaid Diagrams

- Use for architecture diagrams, data flow, state machines, and system relationships
- Apply consistent styling: `fill:#e8f4fd,stroke:#2196f3` for hard IP blocks, `fill:#fff9c4,stroke:#f9a825` for soft logic
- Keep diagrams readable — no more than ~15 nodes per diagram

### Alerts

Use GitHub-style alerts sparingly for critical information:

```markdown
> [!NOTE]
> Background context that aids understanding

> [!WARNING]
> Common mistake that causes synthesis failure, timing violation, or hardware damage
```

- **The Timing Constraint Alert**: Any IP, interface, or design pattern that requires explicit timing constraints must be highlighted with a `> [!WARNING]` block explicitly stating **Requires SDC/XDC constraint**.
- **The Clock Domain Alert**: Any signal crossing clock domains must be highlighted with a `> [!WARNING]` block explicitly stating **CDC: requires synchronizer or FIFO**.

### Horizontal Rules

Use `---` to separate major sections. Don't use between subsections.

---

## Depth Expectations

### Shallow (unacceptable)

A module port list with no context, no explanation of relationships, no examples, no pitfalls. This is an instantiation template, not documentation.

### Adequate

Overview + port/parameter descriptions + one example + references. Functional but not a learning resource.

### Deep (target quality)

Everything above, plus:
- Architectural diagrams showing hardware relationships
- Vendor context and competitive landscape
- Open-source analogies for accessibility
- Decision guides for choosing between approaches
- Multiple examples covering common and edge cases
- Comprehensive pitfalls with bad/good code pairs
- Timing analysis with quantified costs
- Cross-references to related articles

**Every article in this repository should target "Deep" quality.**

---

## What Makes an Exemplary Article — Key Differentiators

Analysis of the best technical articles reveals consistent patterns that separate deep technical writing from shallow reference stubs:

### 1. The "Why It Exists" Opening

Every great article opens by answering *why* someone should care — not just what the thing is. Compare:

- ✗ *"AXI is a bus protocol used in ARM systems."*
- ✓ *"When a MicroBlaze CPU needs to read from a DDR controller while a DMA engine streams data to an Ethernet MAC, something must arbitrate those requests without deadlocking. AXI4 was designed to solve exactly this — providing separate read and write channels with independent handshake flow control so that latency on one path never stalls the other."*

### 2. Multi-Phase Architecture Diagrams

Great articles don't just describe a process — they break it into **numbered phases** with Mermaid diagrams at each stage. Example: a DDR initialization article walks through 10 discrete steps of the calibration sequence, each with its own code block and explanation. This transforms opaque behavior into a debuggable mental model.

### 3. Named Antipatterns with Bad/Good Pairs

The best articles give antipatterns memorable names:
- "The Latch Lagoon" (incomplete sensitivity list creating unintended latches)
- "The Clock Ghetto" (routing a clock through LUTs instead of dedicated clock networks)
- "The CDC Chasm" (direct signal crossing between domains without synchronization)

Each antipattern shows the **broken code**, explains **why it breaks**, and provides the **corrected version**. This pattern is far more effective than generic warnings.

### 4. Decision Flowcharts

When multiple approaches exist, the best articles include a Mermaid decision flowchart that guides the reader to the correct choice. See a "BRAM vs URAM vs Distributed RAM" flowchart — it encodes the decision logic visually.

### 5. Use-Case Cookbooks

Beyond toy examples, exemplary articles include a **cookbook** of real-world patterns:
- AXI4-Lite register bank with auto-generated decoder
- Clock-domain-crossing FIFO with asymmetric widths
- Multi-rate FIR filter using DSP48 cascades
- PCIe BAR0 register map with Linux UIO driver

These are copy-paste-ready patterns that solve actual developer problems.

### 6. Quantified Performance Tables

Great articles don't just say "this is slow" — they provide concrete numbers:
- "LUT-based multiplier: ~400 LUTs, 100 MHz max vs DSP48: 1 slice, 450 MHz max"
- "BRAM18: 18 Kb, dual-port, 1 clock cycle latency vs distributed RAM: variable depth, async read possible"
- "Yosys synthesis of ECP5: ~2 minutes vs Vivado for Artix-7: ~8 minutes for equivalent design"

### 7. Cross-Platform Comparison Tables

The best articles include a comparison table that maps vendor-specific concepts to their equivalents on other platforms (both vendor and open-source). This serves two purposes:
- **Vendor context** — shows what is unique vs standardized
- **Open-source accessibility** — helps developers using Yosys/LiteX build intuition

### 8. Timing Safety Checklists

For any design involving clocks, IO, or multiple domains, exemplary articles include a **risk/cause/prevention** table that acts as a pre-flight checklist.

### 9. The "Impact on Open Source" Section

Since this repository targets both vendor-tool and open-source (Yosys/nextpnr/LiteX) developers, the best articles note implementation concerns for open-source reproduction: unsupported features, workarounds, equivalent constructs.

### What Mediocre Articles Are Missing

Compare the above with shallow articles that typically lack:
- No "why" — just "what"
- No architecture diagrams
- No decision guides — reader doesn't know when to use the feature
- No pitfalls — reader will hit every bug the hard way
- No antipatterns — reader will write bad code that synthesizes
- No timing data — reader has no performance budget intuition
- No cross-platform context — reader can't connect to existing knowledge
- No use-case cookbook — reader can describe the IP but can't solve problems with it

---

## Research Methodology

Before writing or expanding an article:

1. **Web research** — Search for real-world usage, developer forum discussions, and existing technical analyses. Ground the article in how practitioners actually use the technology, not just what the reference manual says.
2. **Cross-reference vendor documentation** — Verify register addresses, parameter defaults, and tool behavior against actual user guides and datasheets (UG, DS, PG, AC, WP documents).
3. **Study real designs** — Reference well-known open-source projects (LiteX, PicoSoC, ZipCPU, NEORV32) and commercial applications that use the feature. Cite specific examples when possible.
4. **Verify with silicon errata** — Cross-check against vendor errata sheets. Document known silicon bugs and workarounds.
5. **Check open-source parallels** — Research whether the concept has open-source equivalents; this improves accessibility and reveals design insights.
6. **Scan this repository first** — Follow the Pre-Flight Knowledge Base Scan procedure above before creating any new content.

---

## Content Principles

1. **Silicon grounding** — Always explain which hard IP block, which fabric resource, which clock buffer. FPGAs are hardware platforms; software/docs without hardware context are incomplete.

2. **No placeholders** — Every code example must be complete enough to synthesize or simulate. Every register table must show real offsets. Every constraint must show real syntax.

3. **Tool Versioning** — Always specify the minimum tool version required for a feature (e.g., 'Requires Vivado 2020.1+'). If behavior changed between versions, document the modern baseline.

4. **Big-Endian Awareness** — Any article dealing with AXI, PCIe TLPs, or register access from processors must explicitly note endianness behavior. ARM cores are little-endian; some legacy FPGA interfaces expect big-endian byte order.

5. **Honest trade-offs** — When a vendor provides an IP that most professional designs bypass, say so. When a feature has scaling problems, quantify them. Don't oversell.

6. **Cross-linking** — Every article should link to at least 2–3 related articles. The documentation is a graph, not a list.

7. **Source attribution** — Cite vendor document numbers (UG953, DS190, PG057), GitHub repos, and IEEE standards. This is a technical reference, not folklore.

8. **De-abbreviation** — When introducing abbreviations (CDC, BRAM, DSP, LUT, CLB, MMCM), always provide the full name on first use and include a full-name column in summary tables.

9. **Real-world grounding** — Every feature must be contextualized with real use cases, applicability ranges, and honest guidance on when to use alternatives. Avoid documenting IPs or tools in a vacuum.

---

## README Index Maintenance

When creating or significantly expanding an article:
- Update the section's `README.md` index table
- Update the root `README.md` Documentation Map if the article is new
- Index entries should be descriptive, not just the topic name:
  - ✗ `AXI, interconnect, crossbar`
  - ✓ `AXI4 interconnect design: crossbar vs shared bus, address decoding, QoS arbitration, deadlock avoidance`

---

## Commit Messages

!!!DO NOT make any commits without user asking!!!

Use conventional commit format:

```
docs(fpga): <concise description of what changed>
```

!!!DO NOT include co-authored-by trailers!!!
