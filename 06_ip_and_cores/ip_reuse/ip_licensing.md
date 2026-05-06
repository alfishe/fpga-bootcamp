[← 06 Ip And Cores Home](../README.md) · [← Ip Reuse Home](README.md) · [← Project Home](../../../README.md)

# IP Licensing Landscape — Vendor, Open-Source, and Hybrid

FPGA IP licensing is a minefield. You're mixing vendor-proprietary soft IP (with node-locked or seat-locked licenses), open-source HDL cores (with permissive or copyleft terms), and your own RTL — all in one bitstream. Understanding the legal and practical implications of each license type is non-negotiable for commercial products. A single GPL-licensed core in a proprietary bitstream can create unquantifiable legal risk.

> [!NOTE]
> For IP packaging and delivery methods, see [Intel IP Packaging](intel_packaging.md) and [Xilinx IP Packaging](xilinx_packaging.md). For open-source hardware catalogs with license annotations, see [Core Catalogs](../../12_open_source_open_hardware/cores_catalog/README.md).

---

## Vendor IP Licensing Types

| License Type | How It Works | Typical Cost | When to Use |
|---|---|---|---|
| **Seat-Locked** | Tied to a specific machine (MAC address / dongle). One user at a time. | $0 (included with tool) – $50K+ | Single-developer projects |
| **Node-Locked** | Tied to a license server. Concurrent seats. | $2K–$100K+ (annual) | Teams with multiple developers |
| **Project-Locked** | Tied to a specific project/bitstream. IP usage limited to one product. | $5K–$200K+ (one-time) | Commercial products — pay per project |
| **Site-Wide** | Unlimited use at one physical site. | $50K–$500K+ (annual) | Large organizations |
| **Evaluation (Time-Bombed)** | Hardware eval timeout (typically 1–4 hours). Bitstream stops working. | Free (time-limited) | Evaluation before purchase |
| **No-License (Included)** | Free with tool purchase (e.g. FIFO, BRAM controller, basic GPIO) | Included | Standard infrastructure IP |

**Key insight:** Most Xilinx and Intel IP is "no-license" for basic blocks (FIFO, BRAM, clocking, GPIO) but requires a paid license for complex cores (10G/100G MAC, PCIe DMA, DDR4 controller — though DDR controllers are increasingly included).

---

## Open-Source HDL Licenses

Unlike software, HDL (hardware description) licensing is still a legal grey area in many jurisdictions. Here's what each license means for FPGA gateware:

| License | Type | Can I use in proprietary bitstream? | Must I release my RTL? | Must I release modified IP? | FPGA-Specific Notes |
|---|---|---|---|---|---|
| **MIT** | Permissive | ✅ Yes | ❌ No | ❌ No | Safest choice. No restrictions. |
| **BSD 2-Clause** | Permissive | ✅ Yes | ❌ No | ❌ No | Like MIT, slightly more formal. |
| **Apache 2.0** | Permissive + patent | ✅ Yes | ❌ No | ❌ No (for gateware) | Patent grant clause protects you from IP owner suing for patent infringement. Preferred for corporate use. |
| **LGPL** | Weak copyleft | ✅ Yes (as "library") | ❌ No (if dynamically linked) | ✅ Yes | Concept of "dynamic linking" fuzzy for HDL. Generally safe. |
| **GPL v2/v3** | Strong copyleft | ⚠️ Risky | ✅ Yes (if "derived work") | ✅ Yes | **"Derived work" untested in court for FPGA bitstreams.** Many companies ban GPL HDL. |
| **CERN OHL v2 (S)** | Strongly Reciprocal | ❌ No (must release all) | ✅ Yes | ✅ Yes | "S" = Strongly Reciprocal. Like GPL for hardware. |
| **CERN OHL v2 (W)** | Weakly Reciprocal | ✅ Yes | ❌ No | ✅ Yes (only the IP itself) | "W" = Weakly Reciprocal. Like LGPL for hardware. |
| **Solderpad v2.0** | Permissive (Apache 2.0 variant) | ✅ Yes | ❌ No | ❌ No | CERN's permissive option. Similar to Apache 2.0 but adapted for hardware. |

---

## Practical Gateware Licensing Scenarios

### Scenario 1: Commercial Product with Open-Source IP
```
Your proprietary RTL (closed source)
  + Xilinx MIG DDR controller (no-license, included)
  + LiteX SoC (BSD 2-Clause) ← OK, permissive
  + VexRiscv CPU (MIT) ← OK, permissive
  = ✅ Safe for closed-source commercial product
```

### Scenario 2: GPL-Licensed CPU Core
```
Your proprietary RTL (closed source)
  + OpenRISC mor1kx CPU (GPL v2)
  = ⚠️ RISK: GPL "derived work" status untested for FPGA
     Conservative approach: Don't use GPL cores in commercial products
```

### Scenario 3: CERN OHL Strongly Reciprocal
```
Your proprietary RTL (closed source)
  + CERN OHL v2-S BERT core (Strongly Reciprocal)
  = ❌ DANGER: Your entire bitstream may need to be open-sourced
     The "S" variant is designed to propagate openness
```

---

## "Black Box" vs "White Box" IP Delivery

| Delivery Method | What You Get | Protection Level | FPGA Example |
|---|---|---|---|
| **Source RTL (Verilog/VHDL)** | Human-readable code | None — anyone can read/modify | Open-source cores (LiteX, VexRiscv) |
| **Encrypted RTL (IEEE 1735)** | Encrypted source, tool decrypts at synth | Moderate — tool vendors honor encryption | Most paid Xilinx/Intel IP |
| **Netlist (EDIF/DCP)** | Synthesized netlist, not source | High — reverse engineering difficult | Paid IP, ASIC handoff |
| **Bitstream (partial)** | Pre-placed-and-routed block | Highest — bitstream reverse engineering extremely difficult | Some defense-grade IP |

**IEEE 1735:** Standard for IP encryption. Both Vivado and Quartus support it. Encrypted with a tool vendor's public key — only that vendor's tool can decrypt. Note: IEEE 1735 had a critical vulnerability (CVE-2017-13097) — verify your toolchain is patched.

---

## License Compatibility Matrix

Can I combine IP-A (row) with IP-B (column) in the same bitstream?

| | MIT | BSD | Apache 2.0 | LGPL | GPL v3 | CERN OHL-W | CERN OHL-S |
|---|---|---|---|---|---|---|---|
| **MIT** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| **Apache 2.0** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| **LGPL** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **GPL v3** | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| **Proprietary** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |

⚠️ = Untested in court for FPGA gateware. Legal risk.

---

## Best Practices

1. **Default to MIT/BSD/Apache 2.0 for in-house reusable IP** — permissive licenses maximize reuse
2. **Solderpad v2.0 for open-source hardware releases** — designed for hardware, includes patent grant
3. **Never use GPL or CERN OHL-S in a commercial product** — untested legal territory
4. **Audit your IP manifest before tape-out / production** — one GPL core can taint the entire bitstream (legally, at minimum)
5. **Check vendor IP license terms annually** — terms change. What was included last year may be paid this year.
6. **Maintain an IP manifest file** — create a `.ip_manifest.yml` or spreadsheet listing every IP core, its version, source (vendor/open-source/in-house), and license
7. **Use Solderpad or Apache 2.0 for your own open-source releases** — both include patent grants, critical for corporate adoption

---

## Pitfalls

### 1. The GPL "Derived Work" Ambiguity
The GPL's concept of "derived work" has never been tested in court for FPGA bitstreams. A conservative reading suggests that any GPL-licensed HDL core in your design makes your entire bitstream a derived work, requiring you to release all source RTL.

**Fix:** Avoid GPL-licensed HDL cores in commercial products. If you must use one (e.g., mor1kx OpenRISC), isolate it behind a well-defined bus interface and consult legal counsel about the "aggregation exception."

### 2. IEEE 1735 Encryption Expiry
IEEE 1735-encrypted IP is tied to a specific tool version. When you upgrade Vivado or Quartus, the encryption keys may change, and old encrypted IP may no longer decrypt.

**Fix:** Keep the exact tool version used during IP integration in your CI/CD pipeline. Pin tool versions in your build scripts.

### 3. Vendor IP "Free with Tool" Can Become Paid
Xilinx and Intel periodically move IP from "included" to "paid license" categories. A design that compiled last year may fail synthesis this year because an IP block now requires a license.

**Fix:** Check the IP catalog license status after every tool upgrade. Keep a license server running if you depend on paid IP.

---

## IP Manifest Template

For every FPGA project, maintain an IP manifest:

```yaml
# ip_manifest.yml — Track all IP cores in your design
project: my_fpga_design
date: 2026-05-04

ip_cores:
  - name: DDR4_MIG
    vendor: Xilinx
    version: 2.2
    license: Free (included with Vivado)
    source: Vendor IP
    
  - name: VexRiscv
    vendor: SpinalHDL
    version: 1.9.0
    license: MIT
    source: Open-source (GitHub)
    url: https://github.com/SpinalHDL/VexRiscv
    
  - name: PCIe_DMA
    vendor: Xilinx
    version: 4.1
    license: Paid (requires Xilinx license server)
    source: Vendor IP
    license_server: 27000@license01.local
    
  - name: custom_crc32
    vendor: In-house
    version: 1.0
    license: Proprietary
    source: Internal
```

---

## References

- [CERN Open Hardware Licence FAQ](https://cern-ohl.web.cern.ch/)
- [Solderpad Hardware Licence](https://solderpad.org/licenses/)
- [FOSSi Foundation: Licensing for Open Source Silicon](https://fossi-foundation.org/)
- IEEE 1735-2014: Recommended Practice for Encryption of Electronic Design Intellectual Property
- [Open-Source Core Catalogs](../../12_open_source_open_hardware/cores_catalog/README.md) — License-annotated core listings
- [Intel IP Packaging](intel_packaging.md) — IEEE 1735 encryption details
- [Xilinx IP Packaging](xilinx_packaging.md) — DCP and encrypted IP delivery
