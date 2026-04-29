[← 06 Ip And Cores Home](../README.md) · [← Ip Reuse Home](README.md) · [← Project Home](../../../README.md)

# Xilinx IP Packaging — Vivado IP Integrator

Vivado's block-design flow expects IP packaged as IP-XACT components with `component.xml` metadata, AXI4 interfaces, and optional GUI customization. This article covers packaging custom RTL into reusable IP that integrates seamlessly into Vivado IP Integrator block designs.

---

## Packaging Workflow

```
Custom RTL (.v/.sv/.vhd)
    │
    ▼
Vivado: Tools → Create and Package New IP
    │
    ├─ Option A: Package a new AXI4 peripheral (template wizard)
    ├─ Option B: Package existing RTL project
    └─ Option C: Package a block design as IP (.bd → IP)
    │
    ▼
IP Packager GUI
    │
    ├─ Identification: vendor, library, name, version (VLNV)
    ├─ Compatibility: supported FPGA families
    ├─ File Groups: synthesis, simulation sources
    ├─ Customization Parameters: expose generics/parameters
    ├─ Ports and Interfaces: map RTL ports → AXI4, AXI4-Lite, AXI4-Stream
    ├─ Addressing and Memory: memory-map slave regions
    ├─ Customization GUI: layout, tooltips, validation
    └─ Review and Package → produces component.xml in IP repo
```

---

## IP-XACT component.xml Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<spirit:component xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009">
  <spirit:vendor>user.org</spirit:vendor>
  <spirit:library>communication</spirit:library>
  <spirit:name>my_uart</spirit:name>
  <spirit:version>1.0</spirit:version>
  <!-- VLNV: user.org:communication:my_uart:1.0 -->
  
  <spirit:busInterfaces>
    <spirit:busInterface>
      <spirit:name>S_AXI</spirit:name>
      <spirit:busType spirit:vendor="xilinx.com" 
          spirit:library="interface" spirit:name="aximm" spirit:version="1.0"/>
      <spirit:abstractionType spirit:vendor="xilinx.com"
          spirit:library="interface" spirit:name="aximm_rtl" spirit:version="1.0"/>
      <spirit:slave>
        <spirit:memoryMapRef memoryMapRef="S_AXI"/>
      </spirit:slave>
    </spirit:busInterface>
  </spirit:busInterfaces>
  
  <spirit:memoryMaps>
    <spirit:memoryMap>
      <spirit:name>S_AXI</spirit:name>
      <spirit:addressBlock>
        <spirit:baseAddress>0x0000</spirit:baseAddress>
        <spirit:range>4096</spirit:range>
        <spirit:width>32</spirit:width>
      </spirit:addressBlock>
    </spirit:memoryMap>
  </spirit:memoryMaps>
</spirit:component>
```

**VLNV (Vendor-Library-Name-Version)** uniquely identifies each IP in the Vivado catalog.

---

## AXI4-Lite Register Wizard

Vivado can auto-generate an AXI4-Lite slave wrapper for your custom logic:

1. **Tools → Create and Package New IP → AXI4 Peripheral**
2. Select interface type: Lite (register-mapped), Full (burst), Stream
3. Choose number of registers (e.g., 4 registers = 16 bytes)
4. Vivado generates:
   - `my_uart_v1_0_S_AXI.v` — AXI4-Lite slave state machine
   - `my_uart_v1_0.v` — top-level wrapper
   - User logic instantiated inside `// Add user logic here` block

**Register mapping example:**
| Register | Offset | Access | Function |
|---|---|---|---|
| slv_reg0 | 0x00 | R/W | TX data / control |
| slv_reg1 | 0x04 | RO | RX data / status |
| slv_reg2 | 0x08 | R/W | Baud rate divider |
| slv_reg3 | 0x0C | R/W | Interrupt enable mask |

---

## Parameterization

Expose parameters to the IP Configurator GUI:

```tcl
# In the IP Packager GUI (or via Tcl)
set_property value_format int [ipx::get_user_parameters DATA_WIDTH -of_objects $core]
set_property value 8 [ipx::get_user_parameters DATA_WIDTH -of_objects $core]
set_property value_format long [ipx::get_user_parameters CLK_FREQ_HZ -of_objects $core]

# Constrain to specific FPGA families
set_property supported_families {artix7 kintex7 zynq} [ipx::current_core]
```

---

## Tcl-First IP Packaging

For CI and repeatability, package IP via Tcl instead of GUI:

```tcl
# Create IP project
create_peripheral user.org communication my_uart 1.0

# Set IP location
set_property ip_repo_paths /path/to/ip [current_project]
update_ip_catalog

# Or: package existing project as IP
ipx::package_project -root_dir /path/to/ip_out -vendor user.org \
    -library communication -taxonomy /UserIP
ipx::create_xgui_files [ipx::current_core]
ipx::update_checksums [ipx::current_core]
ipx::save_core [ipx::current_core]
```

---

## IP Repository Structure

```
my_ip_repo/
└── communication/
    └── my_uart/
        └── 1.0/
            ├── component.xml          ← IP-XACT metadata
            ├── xgui/
            │   └── my_uart_v1_0.tcl   ← GUI customization
            ├── hdl/
            │   ├── my_uart_v1_0_S_AXI.v
            │   └── my_uart_v1_0.v
            └── doc/
                └── my_uart_v1_0.pdf
```

**IP Catalog discovery:** `Settings → IP → Repository → Add` or `set_property ip_repo_paths /path/to/repo [current_project]`

---

## Differences from Intel Packaging

| Aspect | Vivado IP Packager | Intel Platform Designer |
|---|---|---|
| Metadata | component.xml (IP-XACT) | _hw.tcl (Tcl script) |
| Interface standard | AXI4 / AXI4-Lite / AXI4-Stream | Avalon-MM / Avalon-ST |
| Register generation | AXI4-Lite wizard (auto-generates slave FSM) | Manual _hw.tcl port declaration |
| GUI customization | XGUI .tcl files | Tcl callbacks in _hw.tcl |
| IP repo discovery | Directory-based, auto-scanned | IP_SEARCH_PATHS assignment |
| Vendor-neutral format | IP-XACT is an IEEE standard (1685) | _hw.tcl is proprietary (Intel-only) |

---

## Best Practices

1. **Use the AXI4-Lite wizard for simple register-mapped peripherals** — saves ~200 lines of boilerplate AXI FSM code
2. **Manually package complex streaming/packet IP** — the wizard doesn't handle AXI4-Stream well
3. **Version your IP** — increment VLNV version when interfaces change
4. **Include simulation sources** — `add_fileset sim_1` with testbench files
5. **Set `supported_families`** — prevents IP from appearing for incompatible devices

---

## References

- Vivado UG1118: Creating and Packaging Custom IP
- Vivado UG1119: Vivado IP Integrator
- IP-XACT IEEE 1685-2014 Standard
- [Xilinx IP Packaging Tcl Commands](https://docs.xilinx.com/r/en-US/ug835-vivado-tcl-commands/ipx)
