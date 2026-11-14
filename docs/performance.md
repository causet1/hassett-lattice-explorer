# Algorithm improvements and performance

The November 2026 implementation replaces the quadratic saturation residue
scan with two solved linear congruences, followed by the original exact norm
and parity tests. It also groups component representatives by determinant and
computes each accepted determinant once. The proof of equivalence, including
the noninvertible case when 3 divides the index, is in
[ALGORITHM.md](../ALGORITHM.md#solving-the-linear-conditions-before-the-norm-test).
Python, Julia, and Macaulay2 use these improvements.

Warm Julia benchmarks also motivated an exact Schur-form root bound. When
`min(A,C)-abs(B)>6`, the binary form cannot take a value at most six on a
nonzero integer pair, so no norm-two vector exists. Otherwise the original
root search runs. This prefilter avoids many general Hecke calls and speeds
the Python reference too; the strict equality boundary is regression tested.

## Measured Python improvement

Seven warm runs per case on the recorded macOS/x86-64 machine, Python 3.12,
compared against commit `d3a365b38d9c083c52db8181821d34c54993877e`:

| Pair | Components | Previous median | New median | Speedup |
| --- | ---: | ---: | ---: | ---: |
| 8, 26 | 8 | 0.394 ms | 0.316 ms | 1.25x |
| 8, 96 | 11 | 0.758 ms | 0.488 ms | 1.55x |
| 446, 494 | 525 | 640.624 ms | 27.911 ms | 22.95x |
| 456, 488 | 231 | 277.129 ms | 23.979 ms | 11.56x |
| 498, 500 | 171 | 112.591 ms | 7.846 ms | 14.35x |

For `(446,494)`, residues reaching the quadratic test fell from a scan of
568,713 pairs to 617 linear solutions. Application work units fell from 736,738
to 26,132. Work units are implementation counters, not an estimate of floating
point operations. Existing JSON schemas are unchanged; the meaning of
`overlattice_parameter_candidates` is now the filtered linear-solution count.
Historical stored files retain the earlier diagnostic counts.

These are machine-specific microbenchmarks, excluding startup, serialization
and Julia compilation. Small sub-millisecond cases are noisy. Raw samples,
environment, baseline commit and source hash are retained in
[algorithm-benchmark-2026-11-14.json](algorithm-benchmark-2026-11-14.json).
Reproduce with:

```sh
python scripts/benchmark_engine.py --baseline d3a365b --repeat 7 --output build/benchmark.json
```

## Full-range regression comparison

The optimized Python engine was rerun for **all 13,530 pairs through 500**.
Every one of the **1,636,925 component records and 1,698,033 origins**, including
Gram matrices, K3 reports, inclusion/isometry certificates and starting
candidates, exactly matched the previously verified dataset. Diagnostics were
excluded because the optimization intentionally changes work counters.
Every stored shard's SHA-256 hash was checked before comparison. See
[optimized-engine-comparison-500.json](optimized-engine-comparison-500.json).

```sh
python scripts/compare_engine_catalogue.py ../hassett-expanded-500/catalogue-index.json \
  --report build/optimized-engine-comparison-500.json
```

The small-box tests independently compare every residue with the original
exhaustive conditions. The classification audit independently re-enumerates
saturations with rational matrices. Equality with an old dataset is a regression
check; its geometric correctness also depends on the documented completeness
proof and cited theorems.

## Julia and further optimization

The native Julia implementation calls Hecke's published lattice algorithms and
Nemo/FLINT's exact integer algebra. It additionally caches root decisions and
Hecke lattice objects within each intersection. Its primary benefit is access
to the broader algebra ecosystem; language translation alone is not a speed
claim. The small dependency-free Python algorithm remains efficient at rank
three. Julia package load, installation precompilation and first-call compilation
can dominate small computations and must be separated from warm timings.

Use the package's `benchmark/benchmarks.jl` with BenchmarkTools for native warm
measurements. The recorded Julia 1.10.12 run gives the following **warm minima**
(a different statistic from the Python medians above):

| Pair | Julia / Hecke warm minimum |
| --- | ---: |
| 8, 26 | 1.205 ms |
| 8, 96 | 2.146 ms |
| 446, 494 | 57.363 ms |
| 456, 488 | 32.174 ms |
| 498, 500 | 11.421 ms |

The optimized Python implementation remains faster on these rank-three inputs.
Julia provides the established algebra backend and broader lattice operations;
the choice should include those capabilities and compilation costs. See
[julia-benchmark-2026-11-14.json](julia-benchmark-2026-11-14.json) for the measured
environment and source hashes.

CI runs correctness and cross-language audits, without unstable
wall-clock thresholds. Larger-range work should profile root enumeration,
isometry and certificate serialization separately. Further filters must preserve
marked isometry classes and every origin; process-level parallelism needs
separate shard ownership and measured memory use before adoption.

## Quadratic equation search added with the Macaulay2 package

The native Macaulay2 work yielded a further Python improvement. Instead of
scanning a rectangle for `A*y^2 + 2*B*y*z + C*z^2 = T`, enumerate the coordinate
with the smaller bound and test whether `A*T - (A*C-B^2)*z^2` is a square.
Divisibility then gives every other coordinate. Python keeps its original
loop for boxes of at most 25 points and sorts solutions in historical order,
so every existing root and isometry certificate remains identical. See
[the proof](../ALGORITHM.md#solving-the-binary-equation-without-scanning-a-rectangle).

Fifteen warm Python medians against the already optimized `ed13fe4`:

| Pair | Previous median | New median | Further speedup |
| --- | ---: | ---: | ---: |
| 8, 26 | 0.414 ms | 0.333 ms | 1.24x |
| 8, 96 | 0.505 ms | 0.509 ms | 0.99x |
| 446, 494 | 29.143 ms | 22.750 ms | 1.28x |
| 456, 488 | 25.783 ms | 12.023 ms | 2.14x |
| 498, 500 | 7.874 ms | 7.525 ms | 1.05x |

The sub-millisecond cases are noisy; no improvement is claimed for `(8,96)`.
At `(456,488)`, work fell from 37,131 to 9,922 units. The
[raw benchmark](quadratic-search-benchmark-2026-11-14.json) includes samples,
environment, and source hash. A fresh
[full-range comparison](quadratic-search-comparison-500.json) again reproduced
all 13,530 pairs, 1,636,925 component records, and 1,698,033 origins exactly,
including all witnesses. This is regression agreement, not an independent
classification proof for that entire range.

## Native Macaulay2 implementation

The [Macaulay2 package](../macaulay2/README.md) reuses GMP square roots through
ForeignFunctions, LLLBases/NTL for unimodular preconditioning, Core for exact
matrix arithmetic and Smith forms, and JSON's published parser and encoder.
Its rank-three marked enumeration uses the quadratic identity above. A
triangular integer surrogate lets Euclidean LLL handle large shears; its norm
is provably within a factor four of the scaled Schur norm. All changes are
certified and transported back, and final enumeration is exact. Native tests
include shears of size `10^30` in both isometry directions.

The [validation record](macaulay2-validation-2026-11-14.json) checks agreement
with Python and independently audits all 66 pairs through 42: 628 components
and 640 origins. Four larger/equal-determinant cases also pass certificates and
agree, including index 68. Native package tests, CLI recovery tests, package
installation, help-tree checks, and executable documentation run in CI.
This Macaulay2 validation does not claim a full native sweep through 500.

Use `M2 --script macaulay2/benchmark-hassett.m2` for seven warm medians. The
[native benchmark](macaulay2-benchmark-2026-11-14.json) excludes startup,
container launch, and JSON/gzip serialization. It records the Linux M2 runtime
inside Docker on the local macOS host; its times are not directly comparable
to bare-host Python or Julia timings. The package's primary value is native
Macaulay2 algebra interoperability and independently checked implementation,
not a claim that translation makes rank-three enumeration faster.
