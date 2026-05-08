[← Case Studies Home](README.md) · [← Project Home](../README.md)

# FPGA Design Review Checklists

Design reviews catch bugs that simulation misses — architectural mistakes, CDC hazards, missing constraints, and verification gaps. This article provides actionable checklists for four review gates: **pre-synthesis** (RTL quality), **pre-implementation** (synthesis output), **pre-commit** (code quality), and **pre-release** (production readiness). Each checklist item includes the rationale and how to verify it.

For the board bring-up procedure after release, see [Bring-Up Checklist](bring_up_checklist.md). For common failure modes, see [Common Failures](common_failures.md). For safety-critical requirements, see [Safety-Critical Design](../16_advanced_topics/safety_critical_design.md).

---

## Checklist 1: Pre-Synthesis Review (RTL Quality)

**Gate:** Before running synthesis for the first time, or after major RTL changes.

### Architecture

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 1.1 | Clock domain crossing plan documented | Every CDC is a potential metastability bug | Review CDC matrix: source domain, dest domain, crossing type |
| 1.2 | Reset strategy defined (sync vs async, per-domain) | Inconsistent reset causes simulation/silicon mismatch | Document in design spec; check RTL matches |
| 1.3 | Resource budget estimated and within 70% of target device | Over-utilization causes routing congestion | Check vendor estimator spreadsheet |
| 1.4 | Power budget estimated | Exceeding thermal limits causes field failures | Run XPE/EPE with realistic toggle rates |
| 1.5 | IO pin assignment verified against schematic | Wrong bank voltage damages the FPGA | Cross-reference XDC/QSF with schematic IO table |
| 1.6 | All interfaces have a specification document | Ambiguous interfaces cause integration failures | AXI: ARM spec; custom: register map doc |
| 1.7 | Memory map defined and non-overlapping | Overlapping addresses cause bus conflicts | Verify address ranges in spreadsheet or script |

### RTL Quality

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 1.8 | No inferred latches | Latches are timing hazards | Run synthesis lint; search for `WARNING: inferred latch` |
| 1.9 | All `case` statements have `default` | Missing default → latch or X propagation | Grep for `case` / `endcase` pairs; verify default exists |
| 1.10 | All `if-else` chains are complete in sequential blocks | Incomplete conditions create latches in comb blocks | Review all `always @*` blocks |
| 1.11 | No `casex` used | `casex` treats X and Z as don't-care → sim/synth mismatch | Grep for `casex` → replace with `casez` or explicit |
| 1.12 | No multiply-driven signals | Multiple drivers on a net → undefined behavior | Synthesis warning: "net driven by multiple sources" |
| 1.13 | No width mismatches in assignments | Silent truncation causes data corruption | Synthesis warnings: "width mismatch" |
| 1.14 | All modules have parameterized widths (no magic numbers) | Hard-coded values prevent reuse and portability | Grep for literal constants > 1 in RTL |
| 1.15 | Async reset properly synchronized (if used) | Async release causes recovery violations | Check for reset synchronizer at every domain boundary |
| 1.16 | All clock domain crossings use proper synchronizers | Metastability | Verilator lint, Spyglass CDC, or Meridian CDC |
| 1.17 | No combinatorial loops | Oscillation or latch inference | Synthesis error/warning |
| 1.18 | No `initial` blocks for functional logic | `initial` ignored by some synthesis tools | Grep for `initial` outside of testbenches |

### Verification

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 1.19 | Testbench exists for every module | Untested code is broken code | Check testbench directory |
| 1.20 | Self-checking assertions in testbench | Visual inspection of waves is insufficient | Verify `$assert` / `assert` in testbench |
| 1.21 | CDC paths verified with protocol-aware checker | Simple synchronizers can fail on buses | Run CDC verification tool |
| 1.22 | Coverage targets defined (statement, branch, FSM) | Untested paths hide bugs | Define ≥95% statement, ≥90% branch |

---

## Checklist 2: Pre-Implementation Review (Post-Synthesis)

**Gate:** After synthesis succeeds with zero warnings, before running place-and-route.

### Synthesis Output

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 2.1 | Zero synthesis warnings (or all reviewed and waived) | Warnings indicate real bugs or mismatches | `grep -i warning synthesis.log` |
| 2.2 | No inferred latches | Confirms lint caught them | Check utilization report for "Latch" count = 0 |
| 2.3 | No black boxes | Missing source → undefined hardware | Check for "black box" warnings |
| 2.4 | Resource utilization within budget (≤70% LUT, ≤80% BRAM) | Margin for routing and ECO | Check utilization report |
| 2.5 | Clock resources within limits (PLL/MMCM count) | Running out of clocking resources forces redesign | Check against device limits |
| 2.6 | No timing violations in synthesis estimate | Synthesis timing is optimistic; violations here are critical | Check synthesis timing report |

### Constraint Completeness

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 2.7 | All clocks constrained | Unconstrained paths have no timing guarantee | `report_clocks` — verify all domains present |
| 2.8 | All input delays constrained | Missing input delay → capture failure | `report_ports -direction input` vs constraints |
| 2.9 | All output delays constrained | Missing output delay → launch failure | `report_ports -direction output` vs constraints |
| 2.10 | False paths identified | Over-constraining prevents P&R convergence | Review `set_false_path` and `set_clock_groups` |
| 2.11 | Multicycle paths identified | Default single-cycle analysis may be wrong | Review `set_multicycle_path` |
| 2.12 | Asynchronous reset paths have `set_false_path` | Reset recovery is not a standard timing path | Check reset network in constraints |

### Resource Mapping

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 2.13 | RAMs mapped to BRAM (not distributed) unless intended | Large RAMs in distributed RAM waste LUTs | Check `ram_style` attributes and utilization |
| 2.14 | Multipliers mapped to DSP (not LUT) unless intended | Wide multiplies in LUTs are slow and large | Check `use_dsp` attributes |
| 2.15 | Clock-gating inferred correctly | Incorrect gating creates glitches | Check for BUFGCE/ICG in synthesis report |

---

## Checklist 3: Pre-Commit Review (Code Quality)

**Gate:** Before merging any RTL change to the main branch.

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 3.1 | All existing tests pass | Regression catch | `make test` or CI pipeline green |
| 3.2 | No new synthesis warnings | Warnings are latent bugs | CI build log check |
| 3.3 | Code follows project style guide | Consistency aids readability | Linter pass (Verilator `--lint-only`, SpyGlass) |
| 3.4 | Module header comment present | Traceability and reviewability | Visual check |
| 3.5 | New parameters documented in module header | Parameters without docs are magic numbers | Check header matches parameter list |
| 3.6 | No debug signals left in production code | Debug signals waste resources and can leak data | Grep for `debug`, `ila`, `probe` in committed RTL |
| 3.7 | CDC changes reviewed by second engineer | CDC bugs are the hardest to find in the lab | Require CDC review sign-off |
| 3.8 | Constraint changes reviewed by timing engineer | Bad constraints create false confidence or real failures | Require constraint review sign-off |
| 3.9 | Git commit message references requirement or bug | Traceability | Check commit message format |
| 3.10 | No vendor-specific primitives in portable modules | Vendor lock-in prevents migration | Grep for `BUFGCE`, `MMCM`, `XPM`, `alt_` in portable modules |

---

## Checklist 4: Pre-Release Review (Production Readiness)

**Gate:** Before releasing bitstream to manufacturing or production.

### Timing & Resources

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 4.1 | Timing clean (zero negative slack, all corners) | Timing violation = potential field failure | `report_timing_summary` — WNS = 0.000 ns |
| 4.2 | Multi-corner timing met (if required) | Worst-case corner determines field reliability | Check slow/fast corner reports |
| 4.3 | Resource utilization ≤70% (with margin for ECO) | No room for fixes means new spin required | Check post-impl utilization report |
| 4.4 | BRAM/DSP utilization verified | These don't scale linearly like LUTs | Check specific BRAM and DSP counts |

### Configuration & Security

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 4.5 | Bitstream configuration mode correct (SPI/BPI/JTAG) | Wrong mode = board doesn't boot | Verify config pin strapping vs bitstream format |
| 4.6 | Configuration clock rate within flash spec | Too fast → read errors → boot failure | Check CCLK/CLKCFG rate vs flash datasheet |
| 4.7 | Bitstream encryption enabled (if required) | Unencrypted = clonable | Verify AES key programmed, bitstream encrypted |
| 4.8 | Readback protection enabled | Prevents reverse engineering | Check security reg settings |
| 4.9 | JTAG access locked or password-protected (if required) | Open JTAG = attack surface | Check JTAG lock configuration |
| 4.10 | Fallback / multi-boot configured | Primary image corruption = dead board | Verify GOLDEN_IMAGE and multiboot register settings |

### Verification Closure

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 4.11 | All requirements tested and passed | Untested requirements = unverified features | Requirements traceability matrix — 100% coverage |
| 4.12 | Coverage targets met (statement, branch, FSM) | Low coverage = untested corner cases | Coverage report ≥ defined threshold |
| 4.13 | CDC verification clean | CDC bugs only appear in the field | CDC tool report — zero violations |
| 4.14 | ILA/SignalTap probes removed or disabled | Debug probes consume BRAM and change timing | Check utilization for ILA resources = 0 |
| 4.15 | Power consumption measured on bench (not just estimated) | Estimates can be 50%+ off | Measure on evaluation board with real workload |
| 4.16 | Bitstream regression tested (same source → same bitstream) | Build reproducibility | Bit-identical bitstream from clean build |

### Documentation

| # | Item | Rationale | Verification |
|---|------|-----------|-------------|
| 4.17 | Register map document matches RTL | Software teams rely on register docs | Script: extract register addresses from RTL, compare with doc |
| 4.18 | Version register implemented in RTL | Field diagnostics require firmware version readback | Verify version register at known address |
| 4.19 | Release notes document all changes | Field failure diagnosis requires change history | Review release notes completeness |
| 4.20 | Known issues documented | Undocumented issues create support burden | Review known issues list |

---

## Automated Review with CI/CD

### Verilator Lint Gate

```yaml
# GitHub Actions snippet
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Verilator Lint
      run: |
        verilator --lint-only -Wall -Wno-UNUSEDSIGNAL \
          +define+FPGA_PROT \
          rtl/top.v rtl/spi.v rtl/uart.v
```

### Synthesis Gate

```yaml
synth:
  runs-on: [self-hosted, vivado]
  steps:
    - uses: actions/checkout@v4
    - name: Vivado Synthesis
      run: |
        vivado -mode batch -source synth.tcl
    - name: Check for warnings
      run: |
        python check_synth_warnings.py synth.log
```

### CDC Verification Gate

```yaml
cdc:
  runs-on: [self-hosted, spyglass]
  steps:
    - uses: actions/checkout@v4
    - name: SpyGlass CDC
      run: |
        spyglass -project cdc_spyglass.prj
    - name: Check CDC violations
      run: |
        python check_cdc_violations.py spyglass_report.rpt
```

---

## Review Meeting Template

### Attendees

| Role | Responsibility |
|------|---------------|
| **Design engineer** | Presents the design, answers technical questions |
| **Review lead** | Ensures checklist is followed, manages time |
| **Timing engineer** | Reviews constraints, timing results |
| **Verification engineer** | Reviews test coverage, testbench quality |
| **Independent reviewer** | Fresh eyes — not involved in the design |

### Agenda

1. **Overview** (5 min) — What does this design do? What changed?
2. **Architecture walk** (10 min) — Block diagram, clock domains, reset strategy
3. **CDC review** (10 min) — Crossing points, synchronizer types
4. **Constraint review** (5 min) — Clock definitions, exceptions
5. **Verification status** (10 min) — Coverage numbers, test results
6. **Open issues** (5 min) — Known bugs, waivers, action items

### Outcome

- [ ] All checklist items pass → **Approve**
- [ ] Minor issues found → **Approve with actions** (assign owners, due dates)
- [ ] Major issues found → **Reject** (require another review after fixes)

---

## Cross-References

| Topic | Article |
|-------|---------|
| Board bring-up procedure | [Bring-Up Checklist](bring_up_checklist.md) |
| Common failure modes | [Common Failures](common_failures.md) |
| Safety-critical requirements | [Safety-Critical Design](../16_advanced_topics/safety_critical_design.md) |
| CDC coding patterns | [CDC Coding](../04_hdl_and_synthesis/cdc_coding.md) |
| Timing closure methodology | [Timing Closure](../05_timing_and_constraints/timing_closure.md) |
| CI/CD for FPGA | [CI/CD for Hardware](../13_toolchains/cicd_hardware.md) |
