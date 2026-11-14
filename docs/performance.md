# Algorithm improvements and performance

The November 2026 implementation replaces the quadratic saturation residue
scan with two solved linear congruences, followed by the original exact norm
and parity tests. It also groups component representatives by determinant and
computes each accepted determinant once. The proof of equivalence, including
the noninvertible case when 3 divides the index, is in
[ALGORITHM.md](../ALGORITHM.md#solving-the-linear-conditions-before-the-norm-test).
Both Python and Julia use these improvements.

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
separate shard ownership and measured memory use before adoption. Macaulay2
remains the next independent frontend, using this certificate contract and the
published regression suite.
