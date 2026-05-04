[← Legacy HDL Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# Altera HDL (AHDL) — Altera's Proprietary Design Language

Altera HDL (AHDL) is a proprietary textual design entry language used exclusively with Altera (now Intel) MAX and older FPGA families. It describes logic using Boolean equations, truth tables, and state machine declarations, compiling directly to Altera-specific primitives like LCELL, SOFT, and TRI — a closer-to-silicon abstraction than Verilog or VHDL.

---

## Overview

AHDL was Altera's answer to the "how do designers enter logic?" question in the early 1990s. While Verilog and VHDL were vendor-neutral industry standards, AHDL was purpose-built for Altera devices — it mapped directly to MAX 7000 macrocells and FLEX 10K logic elements with zero ambiguity. The compiler didn't need to infer anything; every LCELL, SOFT buffer, and TRI-state was explicitly specified.

This explicitness made AHDL excellent for CPLD design (where resource constraints demand precise control) but impractical for FPGA design (where Verilog's higher-level abstraction is more productive). AHDL's decline coincided with the industry's shift from CPLDs to FPGAs in the mid-2000s.

---

## Language Features

| Feature | Syntax | Purpose |
|---|---|---|
| **Subdesign** | `SUBDESIGN name (...)` | Module declaration (equivalent to Verilog `module`) |
| **Logic section** | `BEGIN ... END;` | Combinatorial/registered equations |
| **If-Then-Else** | `IF cond GENERATE` | Conditional logic generation |
| **Truth tables** | `TABLE ... END TABLE;` | Direct truth table specification |
| **State machines** | `MACHINE ...` | FSM definition with explicit states |
| **Primitives** | `LCELL`, `SOFT`, `TRI`, `GLOBAL` | Direct Altera primitive instantiation |
| **Parameters** | `PARAMETERS (...)` | Configurable module parameters |

---

## Example — 3-State Buffer in AHDL

```ahdl
SUBDESIGN tri_state_example
(
    data_in[7..0]   : INPUT;
    enable          : INPUT;
    data_out[7..0]  : BIDIR;
)
BEGIN
    data_out[] = TRI(data_in[], enable);
END;
```

### Translation to Verilog

```verilog
// Same 3-state buffer in Verilog
module tri_state_example (
    input  [7:0] data_in,
    input        enable,
    inout  [7:0] data_out
);
    assign data_out = enable ? data_in : 8'bz;
endmodule
```

---

## Example — State Machine in AHDL

```ahdl
SUBDESIGN traffic_light
(
    clk, reset : INPUT;
    red, yellow, green : OUTPUT;
)
VARIABLE
    state : MACHINE WITH STATES (s_red, s_green, s_yellow);
BEGIN
    state.clk = clk;
    state.reset = reset;

    TABLE
        state     => red, yellow, green;
        s_red     => 1,   0,      0;
        s_green   => 0,   0,      1;
        s_yellow  => 0,   1,      0;
    END TABLE;

    CASE state IS
        WHEN s_red    => state = s_green;
        WHEN s_green  => state = s_yellow;
        WHEN s_yellow => state = s_red;
    END CASE;
END;
```

---

## Altera Primitives

AHDL compiles directly to Altera-specific primitives — this is its key differentiator from Verilog:

| Primitive | Function | Modern Equivalent |
|---|---|---|
| **LCELL** | Logic cell — explicit LUT instantiation | Verilog: inferred by synthesizer |
| **SOFT** | Soft buffer — breaks long combinatorial paths | Verilog: `(* dont_touch = "yes" *)` |
| **TRI** | Tri-state buffer | Verilog: `assign y = en ? a : 1'bz;` |
| **GLOBAL** | Global signal (clock, reset) | Verilog: constraint file assignment |
| **CARRY** | Carry chain primitive | Verilog: inferred from `+` operator |
| **CASCADE** | Cascade chain (AND-OR chain) | Verilog: inferred from wide gates |
| **OPNDRN** | Open-drain output | Verilog: `assign y = en ? 1'b0 : 1'bz;` |

---

## AHDL vs ABEL vs Verilog

| Feature | AHDL | ABEL | Verilog |
|---|---|---|---|
| **Vendor** | Altera-only | Vendor-neutral (PAL/CPLD) | Industry standard |
| **Abstraction** | Primitive-level (LCELL, TRI) | Fuse-map level | RTL level |
| **Hierarchy** | Subdesigns | Modules | Modules |
| **FPGA support** | FLEX 10K, Apex, Cyclone (limited) | None | All FPGAs |
| **CPLD support** | MAX 7000, MAX 3000A, MAX II | PAL, GAL, XC9500 | MAX II/V, XC9500 |
| **Last active** | ~2010 (Quartus II) | ~2005 (ispLEVER) | Current |
| **Learning curve** | Low (simple syntax) | Low (simple syntax) | Medium (richer semantics) |

---

## Legacy Status

| Aspect | Assessment |
|---|---|
| **Last actively used** | Early 2010s (MAX II/MAX V CPLDs) |
| **Tool support** | Quartus II (legacy editions) — still compiles AHDL in modern Quartus |
| **Current relevance** | Maintaining legacy Altera CPLD designs |
| **Migration path** | AHDL → Verilog for any new design |
| **Reason to learn** | Understanding legacy Altera designs, CPLD pin-level timing |

> **Note**: Modern Quartus Prime (23.1+) still supports AHDL compilation for backward compatibility, but Altera/Intel has not updated the AHDL language or documentation in over a decade.

---

## References

- [Altera AHDL Language Reference](https://www.intel.com/content/www/us/en/docs/programmable/683019/current/ahdl.html) — still available on Intel's website
- [Quartus Prime Documentation](https://www.intel.com/content/www/us/en/docs/programmable/683019/current/)
- [ABEL](abel.md) — the competing CPLD language
- [PALASM](palasm.md) — the predecessor to both
