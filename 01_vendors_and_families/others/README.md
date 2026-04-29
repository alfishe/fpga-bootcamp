[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-F — Other FPGA Vendors

The broader FPGA landscape beyond the Big Five — including emerging vendors, niche specialists, and high-performance challengers. These vendors occupy specific niches: Efinix (easy-timing FPGAs), QuickLogic (ultra-low-power eFPGA sensor hubs), Achronix (high-end 7nm with 2D NoC), NanoXplore (European rad-hard space FPGAs), and Cologne Chip (German open-source-friendly FPGA).

---

## Why These Vendors Matter

Each "other" vendor solves a specific problem the Big Five don't address well:

| Vendor | Niche | Why You'd Choose Them Over Intel/Xilinx |
|---|---|---|
| **Efinix** | Easy timing closure | Over-provisioned routing fabric — designs close timing faster. Good for teams where FPGA engineers are scarce |
| **QuickLogic** | Ultra-low-power sensor hub | Sub-µA always-on + hard Cortex-M4F + tiny eFPGA. SymbiFlow open-source bitstream. Only commercial FPGA with fully open bitstream |
| **Achronix** | High-end 7nm with 2D NoC | Speedster7t competes with Versal: 2D NoC, ML processors, 112G PAM4, GDDR6. Independent from Intel/Xilinx at the high end |
| **NanoXplore** | European rad-hard space | SEL-immune by design. Used in Ariane 6, OneWeb, ESA Galileo. Sovereign European supply chain |
| **Cologne Chip** | European logic sovereignty | German-designed FPGA, Yosys+nextpnr open flow, QFN64 package. Alternative to US/China supply chains |

---

## Vendor Profiles

### Efinix — Easy Timing, Over-Provisioned Routing

Efinix's core innovation is the **Quantum eXchange** routing fabric: over-provisioned interconnect that makes timing closure significantly easier than traditional FPGAs. Their Efinity IDE wraps Yosys synthesis with proprietary P&R.

| Family | Process | LEs (max) | SERDES | Unique |
|---|---|---|---|---|
| **Trion T4–T20** | 40nm | 4K–20K | None | Low-power, Efinity Yosys flow, T4 at $4 |
| **Titanium Ti60** | 16nm | 60K | 12.5 Gbps | PCIe Gen3 ×4, DDR4, 16nm power efficiency |
| Titanium Ti180 | 16nm | 180K | 25 Gbps | PCIe Gen4 ×4, highest Efinix density |

**Key trait:** Over-provisioned routing + Efinity's timing-driven P&R means designs that struggle to close timing on Artix-7 may close easily on Trion/Titanium.

**Best for:** Teams with limited FPGA expertise, designs with moderate complexity but tough timing constraints.

---

### QuickLogic — eFPGA + Sensor Hub

The EOS S3 is a unique device: a hard Cortex-M4F (80 MHz) + 916 LUT4 embedded FPGA (eFPGA) + sub-µA always-on domain. It's the **only commercial FPGA with a fully open-source bitstream** via SymbiFlow.

| Device | CPU | eFPGA | Key Features |
|---|---|---|---|
| **EOS S3** | Cortex-M4F @ 80 MHz | 916 LUT4 | Always-on <1 µW, I²C/SPI/UART/PDM, SymbiFlow open bitstream |

**Key trait:** Sub-µA always-on sensor hub that wakes the M4F when interesting data arrives. The eFPGA handles sensor fusion and preprocessing at near-zero power.

**Best for:** Wearables, hearables, IoT sensor nodes, always-listening voice triggers.

---

### Achronix — High-End 7nm with 2D NoC

Speedster7t is a 7nm high-end FPGA with a hardened 2D network-on-chip (NoC) running at 2 GHz — similar in concept to Versal's NoC but from an independent vendor. Targets smart NICs and AI inference acceleration.

| Device | LUTs | ML Processors | SERDES | Memory |
|---|---|---|---|---|
| AC7t1500 | 692K | 256 (INT8/FP16/BF16) | 112G PAM4 (×32) | GDDR6, DDR4 |
| AC7t700 | 2,500K | 1,536 | 112G PAM4 | GDDR6, DDR4/5 |

**Key trait:** Hardened ML processors (not soft logic) + 2 GHz NoC for deterministic data movement. Competing with Versal without being locked into the AMD ecosystem.

**Best for:** 400G smart NICs, AI inference at line rate, high-frequency trading, telco infrastructure.

---

### NanoXplore — European Rad-Hard Space FPGAs

French-designed, European-manufactured radiation-hardened FPGAs for space applications. SEL-immune by design (not by process shielding). Used across the European space industry.

| Device | LUTs (equiv) | SERDES | Rad-Hard Spec |
|---|---|---|---|
| NG-Medium | ~48K | None | SEL immune, TID >100 Krad |
| NG-Large | ~144K | None | SEL immune, TID >100 Krad |
| NG-Ultra | ~576K | 28 Gbps | SEL immune, largest EU rad-hard FPGA |

**Key trait:** European sovereign supply chain — no US ITAR restrictions. ESA and CNES qualified.

**Best for:** European space programs (Ariane, OneWeb, Galileo), defense satellites, high-reliability avionics.

---

### Cologne Chip GateMate — German Open-Source FPGA

A small German FPGA (20K logic cells) with first-class Yosys+nextpnr open-source toolchain support. Available in a hobbyist-friendly QFN64 package.

| Device | Logic Cells | Package | Toolchain |
|---|---|---|---|
| CCGM1A1 | 20K | QFN64 | Yosys + nextpnr (fully open) |

**Key trait:** European-designed, fully open-source toolchain, hobbyist-friendly QFN64 (hand-solderable). A European alternative to Lattice iCE40 for open-source FPGA projects.

**Best for:** European logic sovereignty projects, education, hobbyist open-source FPGA designs.

---

## Family Directories

| Directory | Coverage |
|---|---|
| [efinix/](efinix/README.md) | **Efinix Trion (40nm) & Titanium (16nm)** — over-provisioned routing for easy timing closure, Efinity Yosys flow, T4–T20 (Trion), Ti60/Ti180 (Titanium with PCIe Gen3/Gen4, 12.5/25G SERDES) |
| [quicklogic/](quicklogic/README.md) | **QuickLogic EOS S3** — embedded FPGA (eFPGA, 916 LUT4) + Cortex-M4F sensor hub. Only commercial FPGA with fully open-source bitstream via SymbiFlow. Sub-µA always-on |
| [achronix/](achronix/README.md) | **Achronix Speedster7t (7nm)** — 2D NoC @ 2 GHz, ML processors (256–1,536 blocks), 112G PAM4, PCIe Gen5, GDDR6. Smart NIC and AI inference. Dev kits ~$10K |
| [nanoxplore/](nanoxplore/README.md) | **NanoXplore** — European rad-hard space FPGAs (SEL immune). Used in Ariane, OneWeb, ESA Galileo. NG-Medium to NG-Ultra, up to 28G SERDES |
| [cologne_chip/](cologne_chip/README.md) | **Cologne Chip GateMate** — German FPGA, 20K logic cells, Yosys+nextpnr open flow, QFN64. European logic sovereignty |

---

## Comparison Matrix

| Vendor | Flagship Device | Process | Logic Density | SERDES | CPU | Open Toolchain | Niche |
|---|---|---|---|---|---|---|---|
| **Efinix** | Ti180 | 16nm | 180K LEs | 25 Gbps | None | Efinity (Yosys-based, proprietary P&R) | Easy timing closure |
| **QuickLogic** | EOS S3 | 40nm | 916 LUT4 | None | Cortex-M4F (hard) | ✅ SymbiFlow (fully open) | Ultra-low-power sensor hub |
| **Achronix** | AC7t700 | 7nm | 2,500K LUTs | 112G PAM4 | None | ACE (proprietary) | High-end NoC FPGA |
| **NanoXplore** | NG-Ultra | 28nm? | ~576K LUTs | 28 Gbps | None | NanoXmap (proprietary) | European rad-hard space |
| **Cologne Chip** | CCGM1A1 | 28nm? | 20K cells | None | None | ✅ Yosys+nextpnr (fully open) | European open-source FPGA |

---

## Best Practices

1. **Efinix when timing closure is your bottleneck** — the over-provisioned routing fabric genuinely reduces P&R iteration time compared to equivalent-density Xilinx/Intel parts.
2. **QuickLogic EOS S3 for always-on sensor processing** — if your design wakes on a sensor event and processes data at <1 mW, no other FPGA comes close. The open-source bitstream is a bonus.
3. **Achronix if you need high-end but can't use Versal** — Speedster7t provides 2D NoC + ML processors + 112G PAM4 without AMD vendor lock-in. Independent supply chain.
4. **NanoXplore for European space programs** — ITAR-free, SEL-immune, ESA-qualified. The default choice for European institutional space projects.
5. **Cologne Chip for European open-source FPGA** — Yosys+nextpnr supported, QFN64 hand-solderable, German/European supply chain.

## Pitfalls

1. **Smaller ecosystems = less community support** — none of these vendors have the forum activity, tutorial libraries, or IP catalogs of Intel/Xilinx.
2. **Efinix Efinity P&R is proprietary** — only synthesis uses Yosys. The place-and-route engine is closed-source, so you can't inspect or modify routing decisions.
3. **EOS S3 eFPGA is tiny (916 LUT4)** — enough for sensor fusion and simple preprocessing, but not for complex accelerators. Think "programmable peripheral," not "FPGA SoC."
4. **Achronix dev kits are expensive (~$10K+)** — the barrier to entry is high. Speedster7t is an enterprise/telecom play, not a hobbyist platform.
5. **NanoXplore is ITAR-controlled in the US** — if you're a US-based company, export restrictions may apply even though it's a European product.
6. **Vendor longevity risk** — smaller FPGA companies have historically been acquired or discontinued (Tabula, SiliconBlue, Achronix's earlier struggles). Evaluate supply chain stability.

---

## References

| Source | Description |
|---|---|
| Efinix | https://www.efinixinc.com — Trion/Titanium families, Efinity IDE |
| QuickLogic | https://www.quicklogic.com — EOS S3, SymbiFlow open-source bitstream |
| Achronix | https://www.achronix.com — Speedster7t, 2D NoC architecture |
| NanoXplore | https://www.nanoxplore.com — European rad-hard FPGAs |
| Cologne Chip | https://www.colognechip.com — GateMate, German FPGA |
| SymbiFlow (QuickLogic) | https://github.com/SymbiFlow/symbiflow-ql — fully open EOS S3 flow |
