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

## Jenkins Pipeline Example

For teams requiring on-premises CI:

```groovy
// Jenkinsfile
pipeline {
    agent { label 'fpga-builder' }  // Self-hosted with Vivado/Quartus Docker
    
    stages {
        stage('Lint') {
            steps {
                sh 'verilator --lint-only -Wall src/*.v'
            }
        }
        stage('Simulate') {
            steps {
                sh 'make sim'  // Verilator or Icarus
            }
        }
        stage('Synthesize') {
            steps {
                sh 'vivado -mode batch -source build.tcl -notrace'
            }
        }
        stage('Check Timing') {
            steps {
                script {
                    def wns = sh(returnStdout: true, 
                        script: 'grep -oP "WNS\s+=\s+[-\\d.]+" timing.rpt | grep -oP "[-\\d.]+$"').trim()
                    if (wns.startsWith('-')) {
                        error "Timing FAILED: WNS = ${wns}"
                    }
                    echo "Timing OK: WNS = ${wns}"
                }
            }
        }
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: '*.bit, *.rpt', fingerprint: true
            }
        }
    }
    post {
        failure {
            mail to: 'fpga-team@company.com',
                subject: "FPGA Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Check ${env.BUILD_URL}"
        }
    }
}
```

---

## FuseSoC + Edalize: Open-Source CI/CD

FuseSoC is an IP package manager that integrates with Edalize for vendor-agnostic CI builds:

```yaml
# core_file.core
CAPI=2:
name: ::my_design:1.0
dependencies:
  uart: "~1.0"
  spi:  "~1.0"
filesets:
  rtl:
    files: [src/top.v, src/uart_rx.v, src/spi_master.v]
    file_type: verilogSource
targets:
  default:
    filesets: [rtl]
  synth_icesugar:
    default_tool: nextpnr
    filesets: [rtl]
    tools:
      nextpnr:
        part: iCE40UP5K
        package: sg48
  synth_arty:
    default_tool: vivado
    filesets: [rtl]
    tools:
      vivado:
        part: xc7a35tcsg324-1
```

```bash
# CI commands
fusesoc library add my_lib .
fusesoc run --target=synth_icesugar my_design    # iCE40 build
fusesoc run --target=synth_arty my_design       # Artix-7 build
```

---

## Timing Regression Detection

Track timing across builds to catch regressions early:

```python
# timing_regress.py — compare WNS across builds
import re, sys

def parse_wns(rpt_file):
    with open(rpt_file) as f:
        for line in f:
            m = re.search(r'WNS\s+=\s+([-\d.]+)', line)
            if m: return float(m.group(1))
    return None

current = parse_wns(sys.argv[1])
baseline = parse_wns(sys.argv[2]) if len(sys.argv) > 2 else 0.0

if current is None:
    print(f"ERROR: Could not parse WNS from {sys.argv[1]}")
    sys.exit(1)

if current < 0:
    print(f"FAIL: WNS = {current} ns (negative slack)")
    sys.exit(1)

if baseline > 0 and current < baseline * 0.8:  # 20% degradation threshold
    print(f"WARNING: WNS regressed from {baseline} to {current} ns (>20% degradation)")
    sys.exit(1)

print(f"OK: WNS = {current} ns (baseline: {baseline} ns)")
```

---

## Artifact Management Strategy

| Artifact Type | Storage | Retention | Size (typical) |
|---|---|---|---|
| **Bitstream (.bit/.sof)** | S3 / Artifactory / GitHub Releases | 90 days (dev), permanent (release) | 1–50 MB |
| **Timing report (.rpt)** | Same as bitstream | Permanent | 100 KB – 5 MB |
| **Utilization report** | Same as bitstream | Permanent | <1 MB |
| **Simulation waveforms (VCD/FST)** | Not stored (too large) | On-demand only | 100 MB – 10 GB |
| **Synthesis checkpoint (.dcp)** | Not stored (vendor-locked) | Current + previous only | 50–500 MB |
| **Firmware (.bin/.hex)** | Same as bitstream | Permanent | <1 MB |

---

## Best Practices

1. **Don't check bitstreams into Git** — store in artifact repository (S3, Artifactory, GitHub Releases).
2. **Pin tool versions in Docker** — "latest Vivado" breaks builds. Tag images with tool version.
3. **Self-hosted runners for vendor tools** — GitHub-hosted runners don't have Vivado/Quartus. Use self-hosted or a CI service with FPGA tooling.
4. **Run lint + sim on every push, full P&R nightly** — lint takes seconds; P&R takes hours.
5. **Parse timing reports programmatically** — grep for WNS/TNS and fail the build on negative slack.
6. **Use FuseSoC for vendor-agnostic CI** — one `core` file can target Vivado, Quartus, or nextpnr.
7. **Track WNS across builds** — a 20% WNS degradation is a timing regression even if it's still positive.

## References

| Source |
|---|
| Vivado Docker Resources (Xilinx Community) |
| Intel FPGA CI/CD Documentation |
| Verilator Manual |
| FuseSoC (IP package manager + CI) |
| Edalize Backend Documentation |
| Jenkins Pipeline Syntax Reference |
