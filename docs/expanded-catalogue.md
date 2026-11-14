# Expanded Hassett intersection catalogue: version 1.1.0

The expanded catalogue computes every intersection of two distinct nonempty Hassett divisors whose labels are at most **500**. It contains **165 labels, 13,530 unordered label pairs, and 1,636,925 component records**, with no failed or pending pairs. This adds **13,464 pairs** to the original catalogue through 42. All files and all emitted lattice certificates passed the independent catalogue verifier. The exact results and verification scope are recorded in [catalogue-verification-500.json](catalogue-verification-500.json); the downloadable dataset also includes `catalogue-summary-500.json` and a CSV with one row per pair.

This is a computational implementation of the established classification in [Yang–Yu, Algorithm 7.6](https://arxiv.org/abs/2103.09132). It provides a larger reproducible collection of examples and exact certificates. It does not claim a new classification theorem or a solution of the rationality problem.

## What “complete” means

The label set for this release is

\[
D_{500}=\{d\in\mathbf Z:6<d\leq500,\ d\equiv0\text{ or }2\pmod6\}.
\]

There are 165 such labels. The catalogue contains each unordered pair of distinct labels exactly once, hence \(\binom{165}{2}=13{,}530\) pairs. Self-intersections are excluded because their underlying set is the divisor itself, whereas this algorithm classifies the rank-three loci arising from two distinct divisors. The search includes all admissible saturation indices for each pair; 500 bounds the input labels, not the saturation index, component determinant, or number of components.

There are infinitely many valid Hassett labels. Thus a complete catalogue through 500 leaves infinitely many further finite computations available. The same engine accepts arbitrary valid distinct labels, subject to the selected resource limits. Completeness of an individual result comes from its exhaustive finite search and the geometric theorems connecting the surviving lattices to irreducible components. Passing certificate checks alone does not prove that an enumeration omitted nothing.

The following nested ranges are all fully covered. Component totals count records separately for each pair.

| Maximum label | Labels | Unordered distinct pairs | Component records |
|---|---:|---:|---:|
| 42 | 12 | 66 | 628 |
| 100 | 31 | 465 | 10,787 |
| 200 | 65 | 2,080 | 98,925 |
| 300 | 98 | 4,753 | 338,395 |
| 500 | 165 | 13,530 | 1,636,925 |

## Reading the mathematical records

For a fixed pair, each component record represents a reduced irreducible component of its intersection in the moduli space of smooth complex cubic fourfolds. It gives the generic rank-three algebraic lattice, a distinguished class representing \(h^2\), and all retained construction origins leading to that lattice. The engine identifies origins by integral isometries fixing the distinguished class. The guide [mathematics.md](mathematics.md) explains why the relevant lattice loci exist and are irreducible; [implementation.md](implementation.md) gives the exact search formulas.

**The aggregate total is not a count of globally distinct geometric loci.** A rank-three lattice can contain several primitive rank-two Hassett labels. Its locus can consequently occur in several different pairwise intersections, and it contributes a record in each corresponding pair. This release deduplicates representatives within each pair; it does not identify all repeated loci across the entire catalogue.

A component determinant is the determinant of its **rank-three** Gram matrix. A Hassett label is the discriminant of a primitive **rank-two** lattice containing \(h^2\). These are different invariants. Neither a component's determinant nor either input label alone decides whether its whole rank-three lattice contains an admissible K3 label.

| Quantity over the complete d ≤ 500 catalogue | Value |
|---|---:|
| Component records | 1,636,925 |
| Retained construction origins | 1,698,033 |
| Additional construction routes merged within pairs | 61,108 |
| Records whose lattice contains an admissible K3 label | 1,371,455 |
| Records whose lattice contains no admissible K3 label | 265,470 |
| Records with at least one proper saturation origin | 363,657 |
| Proper saturation origins, of index greater than one | 409,887 |
| Largest retained saturation index | 68 |
| Smallest / largest component determinant | 16 / 83,000 |

Here an origin records the initial pairing parameter, saturation index, residue parameters, and integral inclusion and basis maps. A record can have both an index-one origin and a proper saturation origin. Accordingly, the 363,657 records with proper saturation origins must not be interpreted as the number of components that would disappear if saturation were omitted.

The largest retained saturation index, 68, occurs in \(\mathcal C_{456}\cap\mathcal C_{488}\). The largest component count for a single pair in this range is 525, for \(\mathcal C_{446}\cap\mathcal C_{494}\). In 3,859 pairs, different representatives classified by the engine have the same determinant; for example, \(\mathcal C_8\cap\mathcal C_{96}\) has 11 components but only 10 distinct determinants. These observations illustrate why saturation and exact isometry classification are both necessary. They are finite-range computational results, not statements about extrema over all labels. The independent certificate checker does not separately repeat all pairwise isometry decisions.

### K3 associations and rationality

The K3 flag uses the whole lattice criterion of [Yang–Yu, Theorems 8.8–8.9](https://arxiv.org/abs/2103.09132). An affirmative flag means that the displayed rank-three lattice contains a primitive rank-two sublattice through \(h^2\) satisfying Hassett's arithmetic condition for an untwisted K3 association. Both input labels can fail that arithmetic test while a third label inside the same lattice succeeds.

A negative flag means that the displayed lattice contains no such admissible rank-two sublattice. This describes the generic rank-three situation on the component. At a more special point, the algebraic lattice can have higher rank and acquire an admissible label. The negative flag does not exclude K3 associations at every point of the component.

**No rationality or irrationality decisions are made.** A K3 association is a Hodge-theoretic statement, and rationality requires additional geometric or categorical arguments. This release computes neither explicit equations nor birational maps, and its component counts do not include scheme-theoretic intersection multiplicities. The mathematical guide discusses these distinctions and the connection to rationality questions.

## Published benchmarks and verification

The five published regression cases remain unchanged. Verification compares the complete component determinant lists, not only their lengths.

| Intersection | Components | Published reference |
|---|---:|---|
| \(\mathcal C_8\cap\mathcal C_{14}\) | 5 | [Auel–Bernardara–Bolognesi–Várilly-Alvarado, Theorem 4](https://arxiv.org/abs/1205.0237v4) |
| \(\mathcal C_8\cap\mathcal C_{26}\) | 8 | [Awada, Proposition 3.2](https://arxiv.org/abs/1910.10182v2) |
| \(\mathcal C_8\cap\mathcal C_{38}\) | 10 | [Awada, Theorem 1.1(2)](https://arxiv.org/abs/1910.10182v2) |
| \(\mathcal C_{20}\cap\mathcal C_{12}\) | 6 | [Yang–Yu, Theorem 7.11](https://arxiv.org/abs/2103.09132) |
| \(\mathcal C_{20}\cap\mathcal C_{38}\) | 17 | [Yang–Yu, Theorem 7.9](https://arxiv.org/abs/2103.09132) |

The independent streaming verifier checked every one of the 13,530 pair files. It checked the exact finite label-pair coverage; stored and uncompressed SHA-256 hashes and byte counts; every positive definite starting-parameter interval; and all emitted integral lattice, inclusion, primitive-label, distinguished-class, and basis-map certificates. Separate root enumeration and K3 arithmetic checked the mathematical conditions. The run covered 1,293,470 starting lattices and 3,077,975 independent root-box vectors, and recomputed all pair and aggregate statistics. The [verification report](catalogue-verification-500.json) records the passing result and its limitations.

The verifier does **not** independently re-enumerate every admissible overlattice or prove pairwise nonisometry of every distinct representative. Those completeness and classification steps rely on the engine's exact algorithm and its documented proof. Hashes establish consistency with the catalogue index; they are not external authentication of that index. This is regression-tested research software, not proof-assistant-verified code.

The application also passed 19 Python test methods and a JavaScript interaction harness with **192 base assertions**, increasing to **208 assertions when supplied with the actual expanded dataset**. The latter exercised actual certificates for pairs 8–44, 152–318, and 498–500. The harness executes the embedded application code in a Node VM with a simulated DOM and mocked same-origin HTTP responses; native Web Streams, gzip decompression, and WebCrypto execute in the tests. It verifies application behavior and certificate-loading logic, but does not verify live browser layout, native clipboard behavior, or actual network downloads. See [validation.json](validation.json) and [web_validation.json](web_validation.json).

## Explorer and data format

The [hosted explorer](https://hassett-lattice-explorer.causetpatrick.chatgpt.site) loads a summary index and then the selected pair's full certificate over HTTPS. It checks the file's recorded size and SHA-256 digest, decompresses gzip data, and displays the component matrices, construction origins, and K3 flags. The full dataset is not embedded in the page. Its 13,530 compressed pair files occupy **97,024,470 bytes**, compared with **1,527,319,588 bytes** of uncompressed JSON; these figures exclude the index and other release files.

The standalone `web/explorer.html` retains **66 embedded pairs through 42**. It works offline and imports plain JSON results from the Python engine. File-based offline use does not fetch the expanded dataset automatically. The incidence network is schematic; its drawing is not a coordinate chart or a model of distances in moduli.

The expanded data directory contains:

| Path | Contents |
|---|---|
| `catalogue-index.json` | Schema 1.1 index, exact range, completion state, per-pair summaries, hashes and aggregate statistics |
| `pairs/8-14.json.gz`, and similarly for every pair | Schema 1.0 full result with matrices, candidate scans, all origins, K3 data and diagnostics |
| `run-state.json` | Runner progress and timing; not part of the mathematical certificate |

Filenames use labels in increasing order. Inside a result, `d1` and `d2` follow the algorithm's normalization and therefore need not be increasing. The index records both. Stored-file hashes refer to the compressed bytes; `uncompressed_sha256` refers to the exact decompressed JSON bytes. Deterministic gzip files omit timestamps and original filenames. The packaged dataset includes the verified index, all pair files, a verification report, the summary JSON, the pair-summary CSV, and the MIT license.

## Reproduce, resume, verify, and package

To retrieve the published dataset instead of recomputing it, run
`python scripts/download_catalogue.py --output ../hassett-expanded-500`, then
run the verifier below. Downloads are pinned to the original release index hash.
See [development.md](development.md) for CI and the complete current release workflow.

Run the following commands from the source project's root with Python 3.10 or later. The engine, runner, catalogue verifier, and packaging scripts use the standard library. Node is needed only for the JavaScript interaction harness. The commands below use a sibling data directory so that the source package and expanded data remain separate.

### Compute the finite range

```bash
python scripts/expand_catalogue.py --max-discriminant 500 --gzip \
  --output ../hassett-expanded-500 --seed-catalogue web/catalogue.json
```

Repeat the same command to resume. Existing completed files and seed records undergo certificate checks before reuse. The runner writes each completed file atomically, updates the index periodically, and retries failed or pending pairs on a later invocation. `complete` becomes true only when every required pair succeeds. `run-state.json` retains progress information separately from the reproducible mathematical files. To recompute from scratch, choose a new empty output directory and omit `--seed-catalogue`.

The default per-pair limits are 5,000,000 work units and 60 seconds. Adjust them with `--max-work` and `--timeout`, or explicitly disable them with `--no-limits`. A failed or interrupted batch has an incomplete manifest and a nonzero exit status; completed pair certificates remain available for resumption. To explore further, select a larger finite `--max-discriminant` and verify the resulting index in the same way.

### Independently verify every file

```bash
python scripts/verify_catalogue.py ../hassett-expanded-500/catalogue-index.json \
  --no-limits --progress-every 1000 \
  --report build/validation/catalogue-verification-500.json
```

The verifier processes one pair at a time and writes the aggregate success report only after all checks pass. Here `--no-limits` removes its independent root-vector verification budget; it is separate from the runner's per-pair limits. To verify an extracted data archive, point this command at its `catalogue-index.json`.

Run the source and interaction regressions against the expanded files:

```bash
python scripts/validate_release.py --hosted-data ../hassett-expanded-500
```

Omit `--hosted-data` to run the base release checks with the embedded 66-pair catalogue. The expanded catalogue verification above remains a separate full-data check.

### Package source and data

```bash
python scripts/package_catalogue.py ../hassett-expanded-500/catalogue-index.json \
  --verification build/validation/catalogue-verification-500.json --output ../deliverables
python scripts/package_release.py --output ../deliverables --validation-dir build/validation
```

The first command requires a passing verification report for the exact index being packaged. It rechecks stored shard hashes and creates `hassett-catalogue-500.zip`, `hassett-component-counts-500.csv`, and `catalogue-summary-500.json`. The second creates the source archive `hassett-lattice-explorer.zip` plus standalone HTML/PDF deliverables and their checksum file; the expanded data archive is separate. The PDF is included in the source release. To regenerate it from the mathematical guide, run `python scripts/build_guide.py` with Pandoc and XeLaTeX installed before packaging.

### Build static website assets

```bash
python scripts/build_hosted_site.py ../hassett-expanded-500 \
  --verification build/validation/catalogue-verification-500.json --output dist \
  --summary-csv ../deliverables/hassett-component-counts-500.csv \
  --source-archive ../deliverables/hassett-lattice-explorer.zip
```

This produces `dist/index.html` and the corresponding `dist/data/` catalogue assets. Serve that directory over HTTPS for automatic index and pair loading; this command only prepares files and does not publish a website. Opening the HTML directly continues to use the embedded offline catalogue.

### Plot the complete count matrix

The optional scientific plotting script requires NumPy and Matplotlib. These packages are not dependencies of the lattice engine.

```bash
python scripts/plot_catalogue.py ../hassett-expanded-500/catalogue-index.json \
  --output ../deliverables/hassett-component-counts-500.png
```

Each axis lists the valid labels in increasing order; the colour is the number of components. The matrix is symmetric, and the diagonal is excluded.
