[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Advanced Networking & SmartNICs

In High-Frequency Trading (HFT) and data centers, the latency of the Linux kernel network stack is unacceptable. FPGAs are used as **SmartNICs** — network interface cards where the data plane runs entirely in programmable logic, bypassing the host CPU for packet processing, routing, and protocol termination.

> **Prerequisites:** This article assumes familiarity with [transceiver basics](../06_ip_and_cores/transceivers/transceiver_basics.md), [hard Ethernet MACs](../06_ip_and_cores/other_hard_ip/ethernet_mac.md), and [PCIe hard blocks](../06_ip_and_cores/pcie/pcie_hard_blocks.md). For a higher-level overview of SmartNIC use cases, see [hardware_acceleration.md §2](hardware_acceleration.md).

---

## 1. Why FPGAs for Networking?

| Metric | Software NIC (kernel) | FPGA SmartNIC | ASIC NIC (e.g., ConnectX) |
|---|---|---|---|
| **Latency** | 10–50 µs (kernel stack) | 0.5–3 µs (wire-to-DMA) | 0.3–1 µs (hardwired) |
| **Determinism** | Jitter ±10 µs (scheduler) | Jitter ±1 ns (pipeline) | Deterministic |
| **Programmability** | Full (C, eBPF, XDP) | Full (RTL, P4, HLS) | Limited (firmware only) |
| **Protocol support** | Any (software) | Any (RTL) | Vendor-defined subset |
| **Time to market** | Weeks | Months | Years (tape-out) |
| **Cost (volume)** | $0 (software) | $500–$5,000/card | $200–$2,000/card |

**When FPGA wins:** You need line-rate packet processing at 100G+ with custom logic (encryption, market-data parsing, proprietary headers) that no ASIC NIC implements. FPGA sits in the "programmable but fast" gap between software and hardwired silicon.

---

## 2. SmartNIC Architecture

### 2.1 Inline Datapath Block Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FPGA SmartNIC                                   │
│                                                                         │
│  QSFP28 ──► Transceiver ──► MAC ──► Parser ──► Match-Action ──► DMA     │
│  (100G)                      (L2-L4)  (P4/RTL)  (TCAM/Hash)  (PCIe)     │
│               ◄──           ◄──     ◄──         ◄──          ◄──        │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │ PMA/PCS  │  │ Hard MAC │  │  Flow Cache  │  │  PCIe Gen4/5     │     │
│  │ (SerDes) │  │ + RS-FEC │  │  (BRAM/URAM) │  │  SR-IOV (PF+VF)  │     │
│  └──────────┘  └──────────┘  └──────────────┘  └──────────────────┘     │
│                                    │                       │            │
│                               ┌────▼────┐             ┌────▼────┐       │
│                               │ DDR4    │             │ Host    │       │
│                               │ (flow   │             │ Memory  │       │
│                               │  table) │             │ (DMA)   │       │
│                               └─────────┘             └─────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Inline vs Look-Aside Processing

| Mode | Datapath | Latency | Use Case |
|---|---|---|---|
| **Inline** | All packets pass through FPGA | Added ~100–500 ns | OVS offload, firewall, DDoS mitigation |
| **Look-aside** | Packets分流: fast-path in FPGA, slow-path to CPU | Only fast-path sees FPGA latency | Cryptographic offload, deep packet inspection |

Most modern SmartNICs use **inline** mode. Look-aside is reserved for workloads where the FPGA only accelerates specific packet types (e.g., IPsec ESP decryption).

---

## 3. Ethernet at Line Rate

### 3.1 Speed Grades and Encoding

| Ethernet Rate | Lanes × Line Rate | Encoding | FPGA Transceiver | Reference Clock |
|---|---|---|---|---|
| **10GBASE-R** | 1 × 10.3125 Gbps | 64B/66B | GTX/GTH (Xilinx), GX (Intel) | 156.25 MHz or 312.5 MHz |
| **25GBASE-R** | 1 × 25.78125 Gbps | 64B/66B + RS-FEC | GTH/GTY (Xilinx), GT (Intel) | 156.25 MHz |
| **40GBASE-R4** | 4 × 10.3125 Gbps | 64B/66B | Same as 10G × 4 | 156.25 MHz |
| **100GBASE-R4** | 4 × 25.78125 Gbps | 64B/66B + RS-FEC | GTY/GTM (Xilinx), E-Tile (Intel) | 156.25 MHz |
| **400GBASE-R8** | 8 × 53.125 Gbps (PAM4) | 64B/66B + RS-FEC(544,514) | GTM (Versal), E-Tile (Agilex) | 156.25 MHz |

> For transceiver configuration details, see [transceiver_basics.md](../06_ip_and_cores/transceivers/transceiver_basics.md) and [transceiver_ip_usage.md](../06_ip_and_cores/transceivers/transceiver_ip_usage.md).

### 3.2 RS-FEC (Reed-Solomon Forward Error Correction)

25G/100G Ethernet mandates **RS-FEC (528,514)** — a Reed-Solomon code that adds 14 parity symbols per 514 data symbols, correcting up to 7 symbol errors per codeword.

- **Latency cost:** ~100 ns (encode) + ~200 ns (decode) on a 322 MHz fabric clock
- **When to disable:** Point-to-point DAC cables under 3 m in controlled environments (HFT "FEC bypass"). Some switches support FEC-disabled mode for ultra-low-latency links.
- **Implementation:** Most FPGA hard MACs include RS-FEC. For soft implementations, expect ~2,000 LUTs + 4 BRAM blocks.

### 3.3 Multi-Lane Bonding

For 40G/100G, multiple 10G/25G lanes must be bonded into a single logical stream:

```
Lane 0 ──┐
Lane 1 ──┤  Alignment  ──►  Single 322-bit @ 322 MHz
Lane 2 ──┤  & Reorder      AXI-Stream to user logic
Lane 3 ──┘
```

**Key constraint:** All bonded lanes must be in the same transceiver quad. The alignment FIFO introduces 5–10 UI of deskew latency per lane.

---

## 4. TCP Offload Engine (TOE)

### 4.1 Why TOE Is Hard

TCP is the hardest protocol to implement in FPGA because it is **stateful, timing-dependent, and requires large memory**:

| Challenge | Software (CPU) | FPGA (Hardware) |
|---|---|---|
| **Connection state** | Hash table in DRAM, ~1M connections | BRAM-limited; typically 1K–64K connections |
| **Retransmission timer** | OS timer wheel, ms granularity | Hardware timer per connection, µs granularity |
| **Sliding window** | OS manages buffers in DRAM | Must track window in BRAM; limited buffer depth |
| **Out-of-order segments** | Reassembly queue in DRAM | Expensive in BRAM; often limited to small reorder window |
| **Congestion control** | Cubic/BBR algorithm, floating-point | Simplified Reno or DCTCP; approximated in fixed-point |

### 4.2 TOE Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       TCP Offload Engine                    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ RX Parser    │  │ Connection   │  │ TX Engine         │  │
│  │ (TCP header  │─►│ Table        │─►│ (seq num update,  │  │
│  │  extraction) │  │ (5-tuple →   │  │  checksum, FSM)   │  │
│  └──────────────┘  │  TCB ptr)    │  └───────────────────┘  │
│                    └──────┬───────┘                         │
│                           │                                 │
│                    ┌──────▼───────┐  ┌───────────────────┐  │
│                    │ TCB          │  │ Retransmission    │  │
│                    │ (Transmission│  │ Timer Engine      │  │
│                    │  Control     │  │ (per-connection   │  │
│                    │  Block)      │  │  RTO management)  │  │
│                    └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**TCB (Transmission Control Block):** Per-connection state — typically 128–256 bytes. At 10K connections, this is 1.25–2.5 MB → requires external DRAM or URAM.

### 4.3 TOE IP Vendors

| Vendor | Product | Max Connections | Speeds | Notes |
|---|---|---|---|---|
| **Intilop** | NAC-108 | 64K | 10G/40G | HFT-focused; ultra-low latency |
| **ESN (eSolute)** | TCP100G-TOE | 10K+ | 100G | Available through MACOM |
| **Reflex CES** | AES-TOE | 4K | 10G/25G/40G/100G | Xilinx/Intel FPGA variants |
| **Plasma** | TOE-10G | 2K | 10G | Lightweight, lower cost |
| **OpenTOE** | (Open-source) | ~1K | 10G | Research-grade; not production-hardened |

### 4.4 When You Need TOE vs When You Don't

| Scenario | Need TOE? | Alternative |
|---|---|---|
| Storage (NVMe-oF, iSCSI) | Yes — TCP is the transport | — |
| HFT market-data feed | Usually no — UDP multicast | Raw UDP + application-level reliability |
| RDMA/InfiniBand replacement | No — use RoCEv2 instead | See §6 (RDMA/RoCE) |
| API gateway / web server | Yes — millions of short-lived connections | Software TCP + FPGA checksum offload |

> **Rule of thumb:** If your connections fit in BRAM (< 10K) and you need sub-microsecond TCP termination, TOE makes sense. Otherwise, offload only the checksum and use software TCP.

---

## 5. DPDK Integration

### 5.1 Kernel Bypass Architecture

Standard Linux networking: `Packet → NIC → Kernel Driver → sk_buff → Socket → Application`. Every packet traverses the kernel, incurring multiple context switches and memory copies.

DPDK bypass: `Packet → NIC → DMA → Userspace Ring Buffer → Application`. The kernel is never involved.

```
┌──────────────────── Without DPDK ────────────────────┐
│  NIC → [kernel driver] → [sk_buff copy] → [socket]   │
│  Latency: 10–50 µs, copies: 2–3                      │
└──────────────────────────────────────────────────────┘

┌──────────────────── With DPDK ───────────────────────┐
│  NIC → [DMA] → [userspace rte_ring] → [application]  │
│  Latency: 1–5 µs, copies: 0 (zero-copy)              │
└──────────────────────────────────────────────────────┘
```

### 5.2 Key DPDK Concepts

| Concept | What It Is | FPGA Relevance |
|---|---|---|
| **PMD (Poll-Mode Driver)** | No interrupts; CPU spins on ring buffer status | FPGA DMA engine writes directly to the ring |
| **rte_ring** | Lock-free ring buffer in huge-page memory | FPGA DMA target; must be physically contiguous |
| **VFIO** | Linux framework for userspace PCI device access | Maps FPGA PCIe BARs and IOMMU into userspace |
| **mempool** | Pre-allocated packet buffer pool | DMA descriptors point into mempool buffers |
| **Huge pages** | 2 MB / 1 GB pages (reduces TLB misses) | Essential for DMA performance; 1 GB pages preferred |

### 5.3 FPGA-Specific DPDK Integration

There are three approaches to connect an FPGA SmartNIC to DPDK:

**Approach A: AF_XDP (XDP — eXpress Data Path)**
- Linux kernel provides an AF_XDP socket that redirects packets to userspace
- No custom kernel driver needed
- Lower performance than VFIO (kernel still involved in setup)
- Good for prototyping

**Approach B: VFIO + Custom FPGA DMA**
- FPGA implements its own DMA engine (XDMA / QDMA / custom)
- Userspace maps BARs via VFIO
- Highest performance; zero kernel involvement in data path
- Requires VFIO driver binding

**Approach C: Vendor PMD (e.g., Netronome, Pensando)**
- Vendor ships a DPDK PMD that knows how to talk to the FPGA
- Best integration but vendor lock-in

### 5.4 Practical Setup

```bash
# 1. Allocate huge pages
echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# 2. Bind FPGA PCIe device to VFIO
dpdk-devbind.py --bind=vfio-pci 0000:3b:00.0

# 3. Run DPDK application
./build/l2fwd -l 0-3 -n 4 -- -p 0x1
```

---

## 6. RDMA and RoCEv2

### 6.1 Why RDMA?

RDMA (Remote Direct Memory Access) eliminates CPU involvement on both sides of a network connection. The NIC reads/writes remote memory directly.

| Operation | TCP (kernel) | RDMA (hardware) |
|---|---|---|
| **Send 1 MB** | CPU sends → kernel → NIC → wire → NIC → kernel → CPU receives | App posts buffer → NIC DMA reads → wire → NIC DMA writes → completion |
| **CPU cycles** | ~5,000 per packet | ~0 (offloaded) |
| **Latency (1 byte)** | ~10 µs | ~0.5–1 µs |
| **Latency (1 MB)** | ~1 ms | ~50 µs |

### 6.2 RoCEv2 Protocol Stack

RoCEv2 (RDMA over Converged Ethernet v2) encapsulates InfiniBand transports over UDP/IP:

```
┌──────────────────────────────┐
│  InfiniBand Transport Header │  ← BTH (Base Transport Header): opcode, PSN, QP
├──────────────────────────────┤
│  RDMA Extended Transport     │  ← RETH (RDMA Extended): remote addr, rkey, length
├──────────────────────────────┤
│  UDP (port 4791)             │  ← Identifies RoCEv2 traffic
├──────────────────────────────┤
│  IPv4 / IPv6                 │  ← Routable (unlike RoCEv1 which is L2 only)
├──────────────────────────────┤
│  Ethernet                    │  ← Standard L2 framing
└──────────────────────────────┘
```

### 6.3 Queue Pairs (QP) in Hardware

Every RDMA connection uses a **Queue Pair** — a Send Queue + Receive Queue:

| QP Component | Where It Lives | FPGA Implementation |
|---|---|---|
| **Send Queue (SQ)** | Host memory | DMA reads work requests; processes them in FPGA |
| **Receive Queue (RQ)** | Host memory | DMA posts receive buffers; incoming data written directly |
| **Completion Queue (CQ)** | Host memory | FPGA writes completion entries; host polls |
| **Doorbell** | PCIe BAR / WC memory | Host rings doorbell to notify FPGA of new work requests |

**Resource budget:** Each QP requires ~256 bytes of context in FPGA BRAM. 10K QPs = ~2.5 MB → requires URAM or DRAM.

### 6.4 Congestion Control for RoCEv2

RoCEv2 runs on lossless Ethernet. The network must not drop packets:

| Mechanism | Layer | What It Does |
|---|---|---|
| **PFC (Priority Flow Control)** | L2 | Pause frames per 802.1p priority; prevents switch buffer overflow |
| **ECN (Explicit Congestion Notification)** | L3 | Switch marks IP header on congestion |
| **DCQCN** | Transport | Rate-based congestion control for RoCEv2 (similar to QCN) |
| **CNP (Congestion Notification Packets)** | L4 | Receiver sends CNP back to sender upon ECN marking |

**FPGA implementation:** The RoCEv2 engine must generate and respond to CNPs within ~1 µs. This requires tight integration between the MAC, parser, and QP state machine.

---

## 7. P4 Programmable Pipelines

### 7.1 P4 Language Overview

P4 (Programming Protocol-Independent Packet Processors) is a domain-specific language for defining how packets are processed in a programmable pipeline. It describes **three stages**:

1. **Parser** — Extracts header fields from raw packet bytes
2. **Match-Action Tables** — Classifies packets and applies actions (forward, drop, modify, replicate)
3. **Deparser** — Reassembles headers and emits the packet

### 7.2 P4 → FPGA Compilation

| Tool | Vendor | Target | Notes |
|---|---|---|---|
| **SDNet** | Xilinx | Versal / UltraScale+ | P4-16 → VHDL/Verilog; integrates with Vitis |
| **P4 Studio** | Intel (Barefoot) | Intel FPGAs (Stratix 10, Agilex) | SDE (Software Development Environment) |
| **P4→NetFPGA** | Open-source | Xilinx 7-series | Academic; compiles P4 to NetFPGA pipeline |
| **p4c-xilinx** | Xilinx (open) | Xilinx FPGAs | Open-source P4 compiler backend |

### 7.3 Match Types and FPGA Resources

| Match Type | Description | FPGA Resource | Latency |
|---|---|---|---|
| **Exact** | Full key match (e.g., /32 route) | Hash table in BRAM | 2–3 cycles |
| **Ternary (TCAM)** | Wildcard match (e.g., /24 route) | Emulated TCAM in BRAM/LUT or external TCAM | 1–2 cycles (if on-chip) |
| **Range** | Value within range (e.g., port 1024–65535) | Decomposed into ternary entries | 2–4 cycles |
| **LPM (Longest Prefix Match)** | Longest matching prefix | Modified trie in BRAM or TCAM | 4–10 cycles (trie depth) |

> **TCAM limitation:** FPGAs have no native TCAM. A 1K-entry × 128-bit TCAM costs ~4,000 LUTs. For large routing tables (>100K entries), use DDR4-backed hash tables with on-chip caching.

### 7.4 Example: L2/L3 Switch Pipeline

```p4
// Simplified P4-16 L2/L3 switch
parser MyParser(packet_in pkt, out headers hdr) {
    state start {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            0x0800: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        pkt.extract(hdr.ipv4);
        transition accept;
    }
}

control MyIngress(inout headers hdr, inout standard_metadata meta) {
    action forward(bit<48> dstAddr, bit<9> port) {
        hdr.ethernet.dstAddr = dstAddr;
        meta.egress_spec = port;
    }
    table mac_table {
        key = { hdr.ethernet.dstAddr: exact; }
        actions = { forward; }
        size = 4096;
    }
    apply { mac_table.apply(); }
}
```

---

## 8. SR-IOV and Network Virtualization

### 8.1 PF / VF Architecture

SR-IOV (Single Root I/O Virtualization) allows a single PCIe device to appear as multiple virtual devices:

```
┌──────────────────────────────────────────┐
│              FPGA SmartNIC               │
│                                          │
│  ┌──────────┐  ┌─────┐  ┌─────┐  ┌─────┐ │
│  │ PF       │  │ VF0 │  │ VF1 │  │ VF2 │ │
│  │ (mgmt)   │  │(VM0)│  │(VM1)│  │(VM2)│ │
│  └────┬─────┘  └──┬──┘  └──┬──┘  └──┬──┘ │
│       │           │        │        │    │
│  ┌────▼───────────▼────────▼────────▼──┐ │
│  │         Shared MAC + Datapath       │ │
│  └──────────────────┬──────────────────┘ │
│                     │                    │
│              ┌──────▼──────┐             │
│              │  QSFP28 MAC │             │
│              └─────────────┘             │
└──────────────────────────────────────────┘
```

| Function | Purpose | PCIe Resource |
|---|---|---|
| **PF (Physical Function)** | Management: config, statistics, flow rules | Full BAR space, MSI-X |
| **VF (Virtual Function)** | Data path: packet Rx/Tx only | Lightweight BAR (doorbell + completion) |
| **Typical VF count** | 16–128 per port | Limited by PCIe bus numbers and MSI-X vectors |

### 8.2 OVS (Open vSwitch) Offload

OVS normally runs in the kernel as a software switch. With an FPGA SmartNIC:

1. **Control plane** stays in software (ovs-vswitchd, OpenFlow controller)
2. **Data plane** (packet forwarding) is offloaded to FPGA match-action tables
3. The `tc (traffic control)` Flower classifier maps OVS flows to FPGA rules via `devlink`

```bash
# Offload an OVS flow to FPGA
ovs-ofctl add-flow br0 \
  "in_port=eth0,dl_dst=00:11:22:33:44:55,actions=output:eth1"
# Kernel translates to tc flower rule → FPGA driver → match-action table entry
```

---

## 9. Precision Time Protocol (PTP / IEEE 1588)

### 9.1 Why Timing Matters

| Application | Required Accuracy | Standard |
|---|---|---|
| **HFT (tick timestamping)** | < 100 ns | MiFID II RTS 25 |
| **5G fronthaul** | < 1.5 µs | ITU-T G.8271 |
| **Industrial automation** | < 1 µs | IEEE 1588v2 |
| **Power grid (synchrophasors)** | < 1 µs | IEEE C37.238 |

### 9.2 Hardware Timestamping

Software timestamping (kernel `SO_TIMESTAMPING`) adds microseconds of jitter. FPGA SmartNICs timestamp packets at the **MAC layer**, where the first bit of the SFD crosses the MII interface:

```
           ┌─────────────────────────────────────────┐
           │              FPGA Fabric                │
  SFP ────►│  MAC ──► Parser ──► Timestamp Unit ──►  │
           │   ▲                                     │
           │   │   ┌───────────────────────────┐     │
           │   └───│ RTC (Real-Time Clock)     │     │
           │       │ Locked to GM/BC via PTP   │     │
           │       │ Resolution: 8 ns (125MHz) │     │
           │       └───────────────────────────┘     │
           └─────────────────────────────────────────┘
```

**RTC resolution:** 1 / fabric_clock_frequency. At 322 MHz (100G Ethernet), this is ~3.1 ns. Sub-nanosecond accuracy requires digital interpolators or multi-phase sampling.

### 9.3 PTP Clock Types

| Type | Role | FPGA Implementation |
|---|---|---|
| **Grandmaster (GM)** | Source of time (GPS-disciplined) | External GPS module → FPGA RTC |
| **Boundary Clock (BC)** | Two-port switch; recovers time on one port, serves on the other | Dual MAC + dual RTC + servo in soft CPU |
| **Transparent Clock (TC)** | Forwards PTP frames, adding residence time correction | MAC intercepts PTP, adds `correctionField` |
| **Ordinary Clock (OC)** | Endpoint; synchronizes to GM | Single MAC + servo (PI controller in FPGA) |

---

## 10. Latency Budgets

### 10.1 HFT Tick-to-Trade Budget

```
┌─── Wire ───┐ ┌─ SFP ──┐ ┌─ SerDes ─┐ ┌─ MAC ─┐ ┌─ Parse ─┐ ┌─ FPGA ─┐ ┌─ DMA ─┐ ┌─ PCIe ─┐ ┌─ App ─┐
│  ~5 ns/m   │ │ ~10 ns │ │  ~40 ns  │ │~30 ns │ │ ~20 ns  │ │~50 ns  │ │~50 ns │ │~200 ns │ │~100 ns│
└────────────┘ └────────┘ └──────────┘ └───────┘ └─────────┘ └────────┘ └───────┘ └────────┘ └───────┘
                                                                               Total: ~500 ns (optimal)
```

| Stage | Latency (typical) | Optimization |
|---|---|---|
| **SFP module** | 5–20 ns | Use DAC cable; avoid optical transceivers |
| **Transceiver CDR lock** | 30–50 ns | Fixed by silicon; not optimizable |
| **MAC (RS-FEC disabled)** | 20–50 ns | Disable FEC; accept bit errors |
| **MAC (RS-FEC enabled)** | 150–300 ns | ~100 ns overhead for encode/decode |
| **Packet parser** | 10–30 ns | Single-cycle parse with parallel header extraction |
| **Match-action lookup** | 10–40 ns | BRAM hash table (2-cycle read) |
| **DMA descriptor write** | 30–80 ns | Write-combining PCIe transactions |
| **PCIe traversal** | 100–300 ns | Gen5 ×16, relaxed ordering enabled |
| **Application logic** | 50–500 ns | Depends on algorithm complexity |
| **Total (best case)** | **~500 ns** | With DAC, no FEC, minimal logic |

### 10.2 Where Latency Hides

1. **FEC** — 100+ ns penalty. HFT often disables FEC on controlled point-to-point links.
2. **PCIe transaction layer** — TLP packaging adds ~100 ns. Relaxed ordering (`set_relax_therm`) helps.
3. **DMA alignment** — Cache-line-aligned descriptors avoid partial writes.
4. **Interrupt moderation** — Never use interrupts for HFT. Poll-mode only.
5. **DDR4 flow table lookups** — 50–80 ns per access. Cache hot flows in BRAM.

---

## 11. Vendor & Open-Source SmartNIC Platforms

### 11.1 Commercial Platforms

| Platform | FPGA / ASIC | Speeds | Key Feature | Deployment |
|---|---|---|---|---|
| **AWS Nitro** | Annapurna Labs (custom ASIC, evolved from Xilinx) | 25G/100G | Full offload: network, storage, security | AWS EC2 instances |
| **Azure SmartNIC** | Xilinx UltraScale+ (Catapult v3) | 40G | SDN pipeline, OVS offload, IPSec | Azure VMs |
| **Pensando DSC** | Custom ASIC (not FPGA) | 25G/100G | P4 pipeline, distributed services | Dell/HPE servers |
| **Intel IPU (IPU-M200)** | Intel Agilex 7 FPGA + ARM | 200G | Infrastructure processing, OVS, NVMe-oF | Cloud providers |
| **AMD Pensando (Pollux)** | Versal Premium + hardened NPU | 200G/400G | P4 + AI co-processing | Next-gen servers |
| **Mellanox ConnectX-6/7** | Hardwired ASIC (not FPGA) | 100G/400G | Hardware RoCEv2, DPDK, SF (Sub-Function) | Baseline comparison |

### 11.2 Open-Source Platforms

| Platform | FPGA | Speeds | Key Feature | Repo |
|---|---|---|---|---|
| **[Corundum](https://github.com/corundum/corundum)** | Xilinx UltraScale+, Versal | 10G/25G/100G | Full open-source NIC with DMA, PTP, multiple queues | GitHub |
| **[NetFPGA](https://netfpga.org/)** | Xilinx Virtex-7 / Kintex-7 | 1G/10G | Academic reference; full pipeline + Linux driver | netfpga.org |
| **[Edge-core (Barefoot)](https://www.barefootnetworks.com/)** | Intel FPGA + Tofino ASIC | 100G | P4 programmable switch + FPGA overlay | Intel P4 Studio |

### 11.3 Selection Guide

| You Need... | Choose... |
|---|---|
| Full custom datapath at 100G+ | Xilinx Alveo / Intel Agilex + Corundum |
| Academic research with P4 | NetFPGA-SUME or Corundum |
| Production cloud infrastructure | AWS Nitro / Azure SmartNIC (managed) |
| Low-latency trading with custom parsing | Custom design on Alveo AU55N or AU50 |
| Cost-effective 10G prototyping | Xilinx AAC1 (Artix-7 based) |

---

## 12. Optical Modules & Physical Considerations

### 12.1 Module Types

| Module | Speeds per Port | Connector | Max Cable Length (DAC) | Power per Module |
|---|---|---|---|---|
| **SFP+** | 10G | LC | 7 m (passive DAC) | ~1 W |
| **SFP28** | 25G | LC | 5 m (passive DAC) | ~1.5 W |
| **QSFP+** | 40G (4 × 10G) | QSFP | 3 m (passive DAC) | ~3.5 W |
| **QSFP28** | 100G (4 × 25G) | QSFP28 | 3 m (passive DAC) | ~4 W |
| **QSFP56-DD** | 400G (8 × 50G PAM4) | QSFP-DD | 2 m (passive DAC) | ~12 W |

### 12.2 DAC vs AOC vs Optical

| Cable Type | Latency | Cost | Distance | Signal Integrity |
|---|---|---|---|---|
| **Passive DAC** | ~5 ns/m | $10–$50 | ≤ 5 m | Best (no signal conversion) |
| **Active Optical Cable (AOC)** | ~5 ns/m + 20 ns (retimer) | $100–$500 | 1–100 m | Good (retimed) |
| **Optical transceiver + fiber** | ~5 ns/m + 20–50 ns (module) | $200–$2,000 | 100 m–10 km | Depends on module quality |

> **HFT tip:** Use passive DAC cables under 3 m for the lowest latency. Every optical module adds ~20–50 ns of retimer/CDR latency.

### 12.3 Thermal Budget

A 100G SmartNIC with 2× QSFP28 modules at full line rate dissipates:
- FPGA: 20–40 W
- 2× QSFP28 modules: ~8 W
- DDR4 DIMM: ~3 W
- **Total: ~30–50 W** — requires active cooling (heatsink + fan or server airflow)

---

## 13. Practical Design Flow

### 13.1 From Specification to Working SmartNIC

```
1. Define datapath    →  What protocols? What speed? What latency budget?
2. Select FPGA        →  Transceiver count, BRAM, PCIe Gen, HBM vs DDR4
3. Instantiate MAC    →  Hard MAC (preferred) or soft MAC (verilog-ethernet)
4. Build parser       →  P4 compiler or hand-coded RTL
5. Implement DMA      →  XDMA / QDMA (Xilinx) or custom DMA engine
6. Write DPDK driver  →  VFIO + PMD or AF_XDP
7. Verify             →  Simulation → ILA → loopback → traffic generator
8. Deploy             →  PCIe insertion → firmware load → DPDK init → go live
```

### 13.2 Debug Strategy

| Stage | Tool | What to Check |
|---|---|---|
| **MAC bring-up** | IBERT + ILA on AXI-Stream | Link up, PCS block lock, FEC alignment |
| **Parser** | ILA on parsed headers | Correct field extraction, no truncation |
| **Match-action** | ILA on table lookup results | Hit/miss, action application |
| **DMA** | PCIe protocol analyzer or ILA on DMA engine | Descriptor writes, completion, no stalling |
| **DPDK** | `dpdk-testpmd` | Packet count, throughput, latency histogram |
| **End-to-end** | ExaNIC / Solarflare timestamping | Wire-to-wire latency measurement |

### 13.3 Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Insufficient transceiver count** | Can't instantiate all 100G ports | Select FPGA with enough quads; check channel sharing rules |
| **RS-FEC not matching link partner** | Link comes up but data is garbled | Ensure both sides use same FEC mode (enabled/disabled/RS-FEC) |
| **DMA descriptor alignment** | PCIe transaction failures, data corruption | Align descriptors to 64-byte cache lines; use `__attribute__((aligned(64)))` |
| **BRAM overflow in flow table** | Packet drops under load | Profile BRAM usage; use URAM for larger tables; implement aging |
| **Head-of-line blocking** | Single slow flow blocks all others | Use multiple DMA queues; implement per-queue flow control |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [PG302 — QDMA Subsystem for PCI Express](https://docs.amd.com/r/en-US/pg302-qdma) | AMD/Xilinx | PCIe DMA engine for UltraScale+ |
| [E-Tile Hard IP for Ethernet Intel FPGA IP User Guide](https://www.intel.com/programmable/technical-pdfs/683468.pdf) | Intel | Hard MAC configuration, RS-FEC, PTP for Stratix 10 & Agilex 7 |
| [IEEE 802.3-2022 (Clause 91)](https://ieeexplore.ieee.org/document/9844436) | IEEE | RS-FEC (528,514) for 25G/100G Ethernet |
| [IEEE 1588-2019](https://standards.ieee.org/standard/1588-2019.html) | IEEE | Precision Time Protocol v2.1 |
| [RFC 5040 — RDMA Protocol](https://datatracker.ietf.org/doc/html/rfc5040) | IETF | RDMAP specification (basis for iWARP/RoCE) |
| [InfiniBand Architecture Specification](https://www.infinibandta.org/ibta-specification/) | IBTA | Queue Pairs, Verbs, RoCEv2 encapsulation |
| [P4-16 Language Specification](https://p4.org/specifications/) | P4.org | P4 language reference |
| [DPDK Programmer's Guide](https://doc.dpdk.org/guides/prog_guide/) | DPDK.org | Poll-mode driver development |
| [Corundum Repository](https://github.com/corundum/corundum) | GitHub | Open-source 100G NIC reference design |
