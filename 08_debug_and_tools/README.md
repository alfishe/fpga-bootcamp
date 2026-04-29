[← Home](../README.md)

# 08 — Debug & Tools

What to do when the simulation passes but the hardware doesn't work. Covers embedded logic analyzers (ILA/SignalTap), JTAG debugging with OpenOCD, boundary scan testing, external logic analyzers, remote Linux debugging on SoC FPGAs, and Tcl scripting for tool automation.

## Index

| File | Topic |
|---|---|
| [ila_signaltap.md](ila_signaltap.md) | Xilinx ILA vs Intel SignalTap: trigger setup, probe routing, memory depth trade-offs, Tcl control |
| [openocd.md](openocd.md) | OpenOCD for FPGA JTAG: configuration scripts, SVF/XSVF bitstream playback, flash programming |
| [jtag_boundary_scan.md](jtag_boundary_scan.md) | Boundary scan (IEEE 1149.1), BSDL files, EXTEST/SAMPLE/PRELOAD, board-level interconnect test |
| [logic_analyzers.md](logic_analyzers.md) | External LA integration (Saleae, DSLogic, sigrok), decoding protocols (UART, SPI, I2C, AXI stream) |
| [remote_debugging.md](remote_debugging.md) | Debugging embedded Linux on SoC FPGAs: JTAG + GDB, kgdb, early printk, /dev/mem, devmem2 |
| [commercial_jtag_tools.md](commercial_jtag_tools.md) | Commercial ecosystem: XJTAG, Corelis, Lauterbach, ARM DSTREAM |
| [tcl_scripting.md](tcl_scripting.md) | Vendor tool automation: Vivado Tcl, Quartus Tcl (quartus_stp), non-project mode, report generation |
