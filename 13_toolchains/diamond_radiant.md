[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Lattice Diamond & Radiant — Two Toolchains, One Vendor

Lattice maintains two parallel toolchains for different device families. Choosing the right one depends on which FPGA you're targeting — they're not interchangeable.

---

## Diamond vs Radiant

| Feature | Diamond | Radiant |
|---|---|---|
| **Target devices** | ECP5, MachXO2/3, iCE40 (older), CrossLink | CertusPro-NX, CrossLink-NX, Avant, iCE40 UltraPlus (newer) |
| **Synthesis engine** | Synplify Pro (included) | Synplify Pro (included) |
| **Simulator** | Active-HDL Lattice Edition (included) | QuestaSim (limited free license) |
| **Debug** | Reveal Inserter + Analyzer | Reveal Inserter + Analyzer (same) |
| **Constraint format** | LPF (Lattice Preference Format) | LPF + SDC (some SDC support) |
| **OS support** | Windows, Linux (limited) | Windows, Linux |
| **Yosys/nextpnr compat** | Yes (ECP5 has excellent open-source flow) | Not yet (CertusPro-NX, Avant) |
| **Status** | Maintenance mode (no new device support) | Active development (new devices only) |

---

## Which Toolchain for Which Device?

| Device Family | Use | Notes |
|---|---|---|
| **ECP5** | Diamond 3.12+ | Best open-source support (Yosys + nextpnr) |
| **MachXO2/MachXO3** | Diamond | Stable; no Radiant support |
| **iCE40 (LP/HX)** | Diamond or Yosys | Excellent open-source flow (icestorm/nextpnr) |
| **iCE40 UltraPlus** | Radiant or Yosys | Both work |
| **CrossLink-NX** | Radiant | 28nm FD-SOI, no open-source flow yet |
| **CertusPro-NX** | Radiant 3.0+ | 28nm FD-SOI, SerDes up to 10.3 Gbps |
| **Avant** | Radiant 5.0+ | Mid-range 16nm, PCIe Gen4 |

---

## Key Features

### Reveal Debugger

Lattice's on-chip logic analyzer:
- Insert via GUI or HDL instantiation (`REVEAL_INSERT` attribute)
- Triggers: basic, advanced (state machine, counters)
- Waveform viewer integrated
- No incremental compile (full recompile required to change probes)

### LPF Constraint Format

```tcl
# LPF example (ECP5)
LOCATE COMP "clk_pin" SITE "A9";
IOBUF PORT "clk_pin" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk_pin" 100 MHz;
```

LPF is simpler than SDC but less expressive — no multi-cycle paths, no generated clocks.

---

## Best Practices

1. **Use Diamond for ECP5 unless Radiant adds features you need** — Diamond is more mature for ECP5.
2. **Export to open-source flow for CI** — Yosys + nextpnr for ECP5 is faster, fully scriptable, and free.
3. **Reveal probe signals need `(* preserve *)`** — synthesis may optimize them away otherwise.

## References

| Source |
|---|
| Lattice Diamond User Guide |
| Lattice Radiant User Guide |
| Lattice Reveal User Guide |
