[← 06 Ip And Cores Home](../README.md) · [← Ip Reuse Home](README.md) · [← Project Home](../../../README.md)

# Intel IP Packaging — Platform Designer (Qsys)

Intel's IP integration tool (Platform Designer, formerly Qsys) expects IP to be packaged as a component with Avalon interfaces, `_hw.tcl` metadata, and optional GUI customization. This article covers the packaging workflow for custom RTL so it appears as a first-class block alongside Intel's catalog IP.

---

## Packaging Workflow

```
Custom RTL (.v/.sv/.vhd)
    │
    ▼
Component Editor (Quartus GUI)
    │
    ├─ Define interfaces (Avalon-MM, Avalon-ST, Conduit, Clock, Reset)
    ├─ Map RTL ports to interface signals
    ├─ Set parameters (generics/parameters exposed to user)
    └─ Generate _hw.tcl
    │
    ▼
Platform Designer
    │
    ├─ Drag-and-drop your component
    ├─ Connect to other components via Avalon bus
    └─ Generate interconnect fabric
```

---

## Interface Types

| Interface | Signal Group | When to Use |
|---|---|---|
| **Avalon-MM (Memory-Mapped)** | address, read, write, readdata, writedata, waitrequest | Register access, DMA, memory-mapped slaves |
| **Avalon-ST (Streaming)** | data, valid, ready, channel, error, startofpacket, endofpacket | Packet processing, DSP pipelines |
| **Conduit** | Arbitrary user signals | Export to FPGA top-level (GPIO, external chip interface) |
| **Clock Input / Output** | clk | Clock domain input/output |
| **Reset Input / Output** | reset, reset_req | Reset domain |
| **Interrupt Sender / Receiver** | irq | Connect to HPS interrupt controller |
| **Memory-Mapped Clock Crossing** | (bridge) | Insert clock-domain crossing |

---

## _hw.tcl Anatomy

A minimal `_hw.tcl` for a UART Avalon-MM slave:

```tcl
# Module properties
set_module_property NAME my_uart
set_module_property VERSION 1.0
set_module_property DESCRIPTION "Simple UART with Avalon-MM interface"
set_module_property AUTHOR "me"
set_module_property GROUP "CustomIP/Communication"

# RTL files
add_fileset QUARTUS_SYNTH QUARTUS_SYNTH "" ""
set_fileset_property QUARTUS_SYNTH TOP_LEVEL my_uart_top
add_fileset_file uart_tx.sv SYSTEM_VERILOG PATH rtl/uart_tx.sv
add_fileset_file uart_rx.sv SYSTEM_VERILOG PATH rtl/uart_rx.sv
add_fileset_file uart_top.sv SYSTEM_VERILOG PATH rtl/uart_top.sv TOP_LEVEL_FILE

# Interfaces
add_interface clk clock sink
set_interface_property clk EXPORT_OF my_uart_top.clk
add_interface reset reset sink
set_interface_property reset EXPORT_OF my_uart_top.rst_n

add_interface avalon_slave avalon slave
set_interface_property avalon_slave ADDRESS_WIDTH 4
add_interface_port avalon_slave avs_address address Input 4
add_interface_port avalon_slave avs_read read Input 1
add_interface_port avalon_slave avs_readdata readdata Output 32
add_interface_port avalon_slave avs_write write Input 1
add_interface_port avalon_slave avs_writedata writedata Input 32
add_interface_port avalon_slave avs_waitrequest waitrequest Output 1

# External UART pins (conduit)
add_interface uart_pins conduit end
add_interface_port uart_pins tx export Output 1
add_interface_port uart_pins rx export Input 1
```

---

## Parameters and GUI

Expose Verilog parameters as user-configurable in Platform Designer:

```tcl
add_parameter BAUD_RATE INTEGER 115200 "UART baud rate"
set_parameter_property BAUD_RATE ALLOWED_RANGES {9600 19200 38400 57600 115200 921600}
set_parameter_property BAUD_RATE DISPLAY_NAME "Baud Rate"

add_parameter DATA_BITS INTEGER 8
set_parameter_property DATA_BITS ALLOWED_RANGES {5 6 7 8}

# Parameter validation callback
set_module_property VALIDATION_CALLBACK validate_uart
proc validate_uart {} {
    set clk [get_parameter_value CLK_FREQ]
    set baud [get_parameter_value BAUD_RATE]
    if {$clk < [expr {$baud * 16}]} {
        send_message error "Clock too slow for baud rate"
    }
}
```

---

## Quartus IP Search Path

To make your IP appear in Platform Designer's IP Catalog:

1. Place `_hw.tcl` and RTL files in a directory
2. Add to Quartus IP search path:
   - **Quartus GUI:** Tools → Options → IP Search Path → Add
   - **Environment variable:** `QSYS_ROOTDIR=/path/to/my/ip`
   - **Project .qsf:** `set_global_assignment -name IP_SEARCH_PATHS /path/to/my/ip`

---

## Differences from Vivado IP Packager

| Aspect | Intel Platform Designer | Xilinx Vivado IP Packager |
|---|---|---|
| Metadata format | `_hw.tcl` (Tcl script) | `component.xml` (IP-XACT XML) |
| Interface standard | Avalon-MM / Avalon-ST | AXI4 / AXI4-Lite / AXI4-Stream |
| GUI customization | Tcl callbacks | Tcl + XGUI customization files |
| Parameter validation | Tcl callback proc | `xpm_cdc` style parameter validation |
| Bus width inference | Automatic from port width | Explicit in component.xml |
| Slave-side arbitration | Built into Avalon fabric | Separate AXI Interconnect IP |

---

## Best Practices

1. **Use `add_interface_port` not `add_interface_signal`** — the former auto-maps by name, reducing boilerplate
2. **Always set `VALIDATION_CALLBACK`** — catch parameter errors before generation
3. **Group IP under meaningful categories** — `set_module_property GROUP "CustomIP/Communication"` makes your IP findable
4. **Include simulation fileset** — `add_fileset SIM_VERILOG` or `SIM_VHDL` for testbench integration
5. **Don't mix Avalon-MM master and slave in one component** — split into separate modules for clarity

---

## References

- Intel AN 794: Component Interface Tcl Reference
- Intel Quartus Prime Handbook Vol 1: Design and Synthesis → Platform Designer
- [Avalon Interface Specifications (Intel)](https://www.intel.com/content/www/us/en/docs/programmable/683091/)
