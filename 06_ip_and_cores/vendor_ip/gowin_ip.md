[← 06 Ip And Cores Home](../README.md) · [← Vendor Ip Home](README.md) · [← Project Home](../../../README.md)

# Gowin IP Catalog

Gowin EDA includes a built-in IP core generator with a limited but growing catalog. While smaller than Xilinx/Intel offerings, it covers essential functions for Gowin's target markets (edge computing, industrial, consumer, and retro computing). This article covers each IP category, configuration notes, integration patterns, and the limitations that Gowin developers must work around.

> [!NOTE]
> For Gowin toolchain details (IDE, synthesis, implementation), see [Gowin EDA](../../13_toolchains/gowin_eda.md). For Gowin FPGA families (GW1N, GW2A, GW5A), see [Gowin](../../01_vendors_and_families/gowin/README.md).

---

## IP Generator Overview

| Aspect | Detail |
|---|---|
| **Tool** | Gowin EDA → Tools → IP Core Generator |
| **Interface** | GUI wizard for each IP with parameter preview |
| **Output** | Verilog/VHDL wrapper files + SDC constraints |
| **License** | All IP included with Gowin EDA (no separate license) |
| **Customization** | Parameters set in wizard; some IP support post-generation editing |

---

## IP Categories

### Clocking IP

| IP | Description | Families | Notes |
|---|---|---|---|
| **PLL** | Phase-locked loop (multiply/divide) | All | 2–3 outputs, no fractional-N, no dynamic reconfiguration |
| **DLL** | Delay-locked loop | GW1N, GW2A | For precise phase alignment |
| **OSC** | On-chip RC oscillator | All | ~3–50 MHz, low accuracy (±30%), for watchdog/power-on |

**PLL Configuration (GW1N):**
- Input frequency: 3–375 MHz
- VCO range: 400–1200 MHz
- Outputs: 2 (CLKOP, CLKOS) or 3 (CLKOP, CLKOS, CLKOS2)
- Phase shift: Coarse only (90° steps)
- No dynamic reconfiguration

```verilog
// Gowin PLL instantiation — 27 MHz input, 54 MHz output
rPLL #(
    .FCLKIN   ("27.000"),
    .FCLKOUT0 ("54.000"),
    .IDIV_SEL (0),
    .FBDIV_SEL(1),
    .ODIV0_SEL(8)
) pll_inst (
    .CLKIN   (clk_27m),
    .CLKOUT0 (clk_54m),
    .LOCK    (pll_locked),
    .RESET   (1'b0)
);
```

### Memory IP

| IP | Description | Families | Notes |
|---|---|---|---|
| **SDRAM Controller** | SDR/DDR SDRAM | All | Supports standard SDRAM chips up to 166 MHz |
| **HyperRAM Controller** | HyperRAM 1.0/2.0 | GW2A, GW5A | **Standout IP** — 12-pin interface for 8–128 MB |
| **PSRAM Controller** | QSPI PSRAM | GW2A, GW5A | Octal PSRAM for higher bandwidth |
| **SPI Flash Controller** | Standard SPI flash | All | For configuration and data storage |
| **Block SRAM (BSRAM)** | Dual-port RAM, FIFO, ROM | All | Configurable: 1K–32K depth, 1–36 bit width |

**HyperRAM Controller — Key Differentiator:**

HyperRAM is Gowin's standout memory IP. It provides high-bandwidth external memory with minimal pin count:

| Parameter | Value |
|---|---|
| Interface | 12 pins (8 data + 4 control) |
| Clock | Up to 200 MHz DDR (400 Mbps/pin) |
| Capacity | 8 MB, 16 MB, 32 MB, 64 MB, 128 MB |
| Latency | ~80 ns initial, then sustained |
| Power | < 100 mW active |

Use case: external memory for retro computing cores (MiSTer-like) on Gowin Tang Nano / Siplanet boards.

### Bus Interface IP

| IP | Description | Mode | Max Speed |
|---|---|---|---|
| **I2C** | I2C master/slave | Master, Slave | 400 kHz |
| **SPI** | SPI master/slave | Master, Slave | 25 MHz |
| **UART** | 16550-compatible UART | TX + RX | 3 Mbps |
| **I2S** | I2S audio transmitter/receiver | TX, RX | 3.072 MHz bit clock |

### Video IP

| IP | Description | Output | Notes |
|---|---|---|---|
| **DVI TX** | TMDS video transmitter | HDMI/DVI | Up to 720p @ 60 Hz; popular for retro cores |
| **LVDS LCD** | LVDS panel interface | LCD panel | For embedded displays |
| **Camera Interface** | DVP camera input | CMOS sensor | 8-bit parallel input |

**DVI TX — Popular for Retro Computing:**
The DVI TX IP is widely used in the Gowin retro computing community (Tang Nano 20K, Siplanet boards). It generates TMDS signals directly from pixel data:

```verilog
// Gowin DVI TX — simplified usage
// Pixel clock = 25.2 MHz for 640×480 @ 60 Hz
// 10:1 serialization handled internally
dvi_tx #(
    .INPUT_MODE ("RGB"),
    .SERDES_MODE ("OSER10")
) dvi_inst (
    .pclk   (clk_pixel),
    .red    (pixel_r[7:0]),
    .green  (pixel_g[7:0]),
    .blue   (pixel_b[7:0]),
    .hsync  (h_sync),
    .vsync  (v_sync),
    .de     (data_enable),
    .tmds_p (tmds_p),  // Differential output pair
    .tmds_n (tmds_n)
);
```

### DSP IP

| IP | Description | Configurability |
|---|---|---|
| **FIR Filter** | Finite impulse response filter | Up to 256 taps, configurable coefficients |
| **FFT** | Fast Fourier Transform | 64–16384 points |
| **DDS** | Direct digital synthesis | Sinusoid output, configurable frequency resolution |
| **CORDIC** | Coordinate rotation | Sin/cos, magnitude/phase, hyperbolic |
| **Multiplier** | Parallel multiplier | Up to 36×36, signed/unsigned |

### Processor IP

| IP | Description | Architecture | Resources |
|---|---|---|---|
| **PicoRV32** | RISC-V soft core | RV32IMC | ~2,000 LUTs |
| **Gowin EMCU** | 8051-compatible MCU | MCS-51 | ~3,000 LUTs |

**PicoRV32** is the recommended RISC-V soft core for Gowin FPGAs. It is provided as a pre-configured IP in the generator.

### Security IP

| IP | Description | Standard |
|---|---|---|
| **AES** | Advanced Encryption Standard | AES-128/192/256, ECB/CBC modes |
| **SHA** | Secure Hash Algorithm | SHA-256 |
| **TRNG** | True Random Number Generator | Ring oscillator based |

### Connectivity IP

| IP | Description | Notes |
|---|---|---|
| **USB 2.0 Device** | Full-speed USB device | **Key differentiator** — rare in this price tier |
| **Ethernet MAC** | 10/100 Mbps MII/RMII | For embedded networking |

---

## Gowin IP vs Lattice iCE40/ECP5 IP

| IP Category | Gowin | Lattice iCE40 | Lattice ECP5 |
|---|---|---|---|
| **PLL** | Yes (2–3 outputs) | Yes (1 output) | Yes (3 outputs) |
| **DDR3 controller** | No | No | Yes |
| **HyperRAM** | ✅ Yes | No | No |
| **DVI/HDMI TX** | ✅ Yes | No (third-party) | Yes (HDMI TX) |
| **USB 2.0** | ✅ Yes | No | No |
| **RISC-V core** | PicoRV32 (built-in) | No (third-party) | No (third-party) |
| **DSP (FIR/FFT)** | Yes | No | Yes |
| **AES/SHA** | Yes | No | No |

**Gowin's advantages:** HyperRAM, USB 2.0, DVI TX, built-in PicoRV32, security IP
**Lattice's advantages:** DDR3 controller (ECP5), larger fabric, more mature open-source toolchain (Yosys/nextpnr)

---

## Integration Patterns

### Pattern 1: Retro Computing Core (Tang Nano 20K)

```
PLL (27 MHz → 50 MHz) → PicoRV32 (control) + Custom Core (CPU emulation)
                       → HyperRAM (frame buffer) → DVI TX (HDMI output)
                       → SPI Flash (core storage)
```

### Pattern 2: IoT Sensor Node

```
OSC (internal RC) → EMCU 8051 (application) → I2C (sensor)
                  → UART (debug)
                  → AES (encryption)
                  → SPI Flash (data logging)
```

### Pattern 3: USB Audio Device

```
PLL (12 MHz USB → 24 MHz) → I2S (audio codec interface)
                           → USB 2.0 Device (host interface)
                           → FIR (audio processing)
```

---

## Limitations and Workarounds

| Limitation | Impact | Workaround |
|---|---|---|
| **No AXI interconnect** | Cannot use AXI-based IP from Xilinx/Intel | Use Wishbone bus or custom bus; LiteX generates Wishbone interconnect for Gowin |
| **No DDR3/DDR4 controller** | No high-bandwidth external memory | Use HyperRAM (lower bandwidth but sufficient for retro computing); or external SDRAM controller |
| **No PCIe** | No high-speed host interface | Not relevant for Gowin's market; use USB 2.0 or Ethernet for host connectivity |
| **No dynamic PLL reconfiguration** | Cannot change clock frequencies at runtime | Use multiple PLLs with clock mux, or reconfigure entire FPGA |
| **Limited DSP depth** | FFT/FIR limited to 16K points | Implement custom DSP in fabric using DSP primitives |
| **IP not source-visible** | Cannot inspect or modify IP internals | Treat as black box; verify through simulation and ILA (GAO) |

---

## References

| Source | Description |
|---|---|
| Gowin UG286 — IP Core Generator User Guide | Complete IP catalog reference |
| Gowin UG287 — Gowin IP Catalog Data Sheet | Timing and resource specifications per IP |
| Gowin UG302 — HyperRAM Controller User Guide | HyperRAM configuration and usage |
| Gowin UG303 — DVI TX IP User Guide | HDMI/DVI output configuration |
| [Gowin EDA Toolchain](../../13_toolchains/gowin_eda.md) | Gowin toolchain overview |
| [Gowin FPGA Families](../../01_vendors_and_families/gowin/README.md) | GW1N, GW2A, GW5A device details |
| [Open-Source Flow](../../13_toolchains/open_source_flow.md) | Yosys + nextpnr for Gowin (alternative to Gowin EDA IP) |
