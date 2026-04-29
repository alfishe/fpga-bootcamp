[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# CI/CD for FPGA — Automated Builds for Hardware

"Hardware CI" is a decade behind software CI, but it's catching up. Docker containers for vendor tools, GitHub Actions runners, and artifact storage for bitstreams enable automated FPGA builds, timing regression checks, and simulation-based testing — if you're willing to work around the quirks of EDA licensing.

---

## The FPGA CI Stack

```
Git Push → CI Runner → Docker Container → Vendor Tools → Build → Test → Artifacts
                │            │                 │           │        │         │
          GitHub Actions  Vivado/Quartus   synth, P&R   timing   .bit/.sof  S3/Artifactory
          Jenkins          in container      bitstream   sim      reports
```

---

## Dockerizing Vendor Tools

### Vivado Docker Example

```dockerfile
FROM ubuntu:22.04

# Install Vivado dependencies
RUN apt-get update && apt-get install -y \
    libncurses5 libtinfo5 libglib2.0-0 libgtk2.0-0 \
    libx11-6 libxext6 libxrender1 libxtst6 \
    python3 python3-pip

# Copy Vivado installer
export VIVADO_VERSION=2023.2
COPY Xilinx_Unified_${VIVADO_VERSION}_*.tar.gz /tmp/
RUN /tmp/install.sh --batch --agree XilinxEULA,3rdPartyEULA \
    -e "Vivado" -l /opt/Xilinx

ENV PATH="/opt/Xilinx/Vivado/${VIVADO_VERSION}/bin:${PATH}"
```

### Quartus Docker Example

```dockerfile
FROM ubuntu:20.04  # Quartus requires older libs

RUN apt-get update && apt-get install -y \
    libc6-i386 libx11-6:i386 libxext6:i386 \
    libfreetype6:i386 libfontconfig1:i386

COPY Quartus-lite-21.1.0.842-linux.tar /tmp/
RUN /tmp/setup.sh --mode unattended --installdir /opt/intelFPGA_lite

ENV PATH="/opt/intelFPGA_lite/quartus/bin:${PATH}"
```

---

## License Management in CI

| License Type | CI Approach |
|---|---|
| **Free (WebPack/Lite)** | No license needed — works out of the box |
| **Floating (FlexNet)** | Point `LM_LICENSE_FILE` to license server; ensure runner has network access |
| **Node-locked** | Bind license to CI runner's MAC address; persistent VM |
| **Cloud (AWS FPGA, Azure)** | Built into AMI — no separate license |

> **For most hobbyist projects:** Vivado ML Standard or Quartus Lite (free) in Docker is sufficient — no license server needed.

---

## GitHub Actions Example

```yaml
name: FPGA Build

on: [push, pull_request]

jobs:
  build:
    runs-on: self-hosted  # Needs Vivado/Quartus Docker
    container:
      image: my-vivado:2023.2
    steps:
      - uses: actions/checkout@v4

      - name: Synthesize
        run: |
          vivado -mode batch -source build.tcl -notrace

      - name: Check Timing
        run: |
          grep "Worst Negative Slack" timing.rpt | tee slack.txt
          if grep -q "WNS.*-" slack.txt; then
            echo "TIMING FAIL" && exit 1
          fi

      - name: Archive Bitstream
        uses: actions/upload-artifact@v4
        with:
          name: bitstream
          path: top.bit
```

---

## What to Test in CI

| Test | How | Time |
|---|---|---|
| **Lint (Verilator)** | `verilator --lint-only top.v` | Seconds |
| **Synthesis** | Vendor synthesis or Yosys | 2–20 min |
| **Timing check** | Parse timing report for negative slack | 1 min |
| **Simulation (Verilator/Icarus)** | Open-source testbenches | 1–10 min |
| **Full P&R** | Vendor implementation | 20 min – 2 hours |
| **Power estimation** | Post-route power report | 1 min |

**Recommendation:** Run lint + synthesis + basic sim on every push. Run full P&R + timing nightly.

---

## Best Practices

1. **Don't check bitstreams into Git** — store in artifact repository (S3, Artifactory, GitHub Releases).
2. **Pin tool versions in Docker** — "latest Vivado" breaks builds. Tag images with tool version.
3. **Self-hosted runners for vendor tools** — GitHub-hosted runners don't have Vivado/Quartus. Use self-hosted or a CI service with FPGA tooling.

## References

| Source |
|---|
| Vivado Docker Resources (Xilinx Community) |
| Intel FPGA CI/CD Documentation |
| Verilator Manual |
| FuseSoC (IP package manager + CI) |
