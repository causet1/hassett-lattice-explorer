# HassettLattices for Macaulay2

A native implementation of Yang--Yu Algorithm 7.6, classifying all reduced
components of intersections of distinct Hassett divisors. It retains every
saturation origin and exact integral inclusion/isometry certificate, with
primitive markings, whole-lattice K3 criteria, bounded K3 witnesses, Smith
invariants, a CLI, and resumable catalogues.

Requires **Macaulay2 1.26.05 or later** on Linux or macOS, with the bundled
`LLLBases`, `JSON`, `Parsing`, and `ForeignFunctions` packages and libffi/GMP
support. Tested with **1.26.06**. Gzip I/O uses `gzip`; catalogue hashing uses
`sha256sum` or `shasum`. No Python, Julia, or network service is used at runtime.
Python is used only by the separate development validation tools.

From a checkout of this repository, in Macaulay2:

```m2
path = prepend(currentDirectory() | "macaulay2/", path);
needsPackage "HassettLattices";
r = hassettIntersection(12,20)
sort apply(hassettComponents r,c->c#"determinant")
-- {20,32,53,68,77,80}
verifyHassettResult(r,Classification=>true)
writeHassettResult("12-20.json.gz",r);
r = readHassettResult "12-20.json.gz"
```

To install into your usual Macaulay2 package directory, after setting `path`:

```m2
installPackage "HassettLattices";
check "HassettLattices";
viewHelp HassettLattices
```

The package is distributed from this repository. It has not been submitted to
the Macaulay2 distribution or published to a public registry. Repository access
is required; pin a commit for reproducible research. The
[MIT license](LICENSE) covers this implementation. Dependencies retain their
own licenses; none of their source is vendored here.

## Working with lattices

```m2
c = first hassettComponents r;
g = hassettGram c;
hassettDiscriminant c
hassettInvariants c
latticeK3Association c
primitiveHassettMarkings(c,500)
k3Witness(c,500)
u = matrix {{1,2,-1},{0,1,4},{0,0,1}};
l = changeHassettBasis(c,u);
s = hFixedIsometry(c,l);
assert(transpose s*hassettGram l*s == g)
```

`hassettLattice` validates a symmetric, positive definite 3-by-3 `ZZ` Gram
matrix with first vector `h` of square three and distinguished parity.
`normTwoVector` and `hFixedIsometry` also accept positive Gram matrices without
the parity condition, for general lattice experiments. They return a witness
or `null` after an exhaustive search. All basis and inclusion matrices use
**column coordinates**. Component records and results are immutable hash
tables, with native matrices; `hassettResultData` converts them to JSON arrays.

`positiveHassettParameters`, `hassettBaseGram`, `saturationIndices`, and
`saturationResidues` expose the individual steps. See `help` for each exported
function and the [implementation/reuse guide](CONTRIBUTING.md).

The algorithm classifies **reduced components**. It does not compute scheme
multiplicities, explicit equations, rationality, or birational maps. The K3
decision applies to the entire marked lattice; failure to find a bounded
`k3Witness` does not negate that decision.

## Commands and catalogues

Use `--script` as the first M2 argument:

```sh
M2 --script macaulay2/HassettLattices/cli.m2 intersect 8 14 -o result.json
M2 --script macaulay2/HassettLattices/cli.m2 verify result.json --classification
M2 --script macaulay2/HassettLattices/cli.m2 markings result.json 8-14-c01 500
M2 --script macaulay2/HassettLattices/cli.m2 catalogue 42 build/m2-catalogue
M2 --script macaulay2/HassettLattices/cli.m2 help
```

Plain schema-1.0 JSON can be imported directly into the explorer. Gzip pair
files and schema-1.1 catalogue indexes use the same contract as Python and
Julia, including stored/uncompressed SHA-256 hashes and publication fixtures.

```m2
i = buildHassettCatalogue("build/m2-catalogue",42,StopAfter=>10);
assert(not i#"complete")
i = buildHassettCatalogue("build/m2-catalogue",42);
assert i#"complete"
```

Existing shards are verified before reuse, corrupt shards are repaired, and
resource failures remain in the failure ledger for a later retry. Use
`Classification=>true` to re-enumerate reused classifications as well.
`Compressed=>false` selects plain JSON. Atomic file replacement protects each
checkpoint; after interruption, rerun to reconcile newer shards with the
index. Use one writer per directory. A changed bound/compression mode that
leaves unlisted shards is refused. Aggregate totals count records per pair,
not globally distinct geometric loci.

Limits default to `MaxWork=>5000000` and `TimeLimit=>60`; set either to `null`
to disable it. Backend calls are checked before and after, so timeouts are
cooperative. No interrupted calculation returns a partial `HassettResult`.
CLI equivalents are `--max-work N|none` and `--timeout SECONDS|none`. Exit codes
are 0 for success, 1 for an incomplete catalogue, and 2 for input/search errors.

## Existing geometric packages

`SpecialFanoFourfolds` constructs explicit fourfolds and surfaces, and exposes
geometric discriminants and surface intersection numbers. It is complementary
to this moduli-lattice classification. Its internal
`latticeIntersectionMatrix3x3` can include an undetermined polynomial entry;
there is no stable public general marked-Gram accessor in the version studied
(2.8). We therefore do not depend on that private geometry interface or trigger
expensive geometric computations during package loading.

Pass a **known integral Gram matrix**, in the basis `(h,S,T)`, to
`hassettLattice(G)` to use this package's invariant, root, marking, and isometry
tools. This validates the lattice; it does not prove that the span of the
chosen geometric classes is saturated or equals the full algebraic lattice of
the fourfold. Establish those geometric facts separately. The inexpensive
factor-based admissibility checks also avoid importing that large geometry
package solely for its existing `isAdmissible` label predicate.

## Verification and benchmarks

```sh
M2 --script macaulay2/test.m2
M2 --script macaulay2/build-docs.m2
python3 scripts/validate_macaulay2.py
python3 scripts/test_macaulay2_cli.py
M2 --script macaulay2/benchmark-hassett.m2 build/macaulay2-benchmark.json
```

`build-docs.m2` installs into an ignored local prefix and executes all native
documentation examples with documentation checks enabled. It does not modify
your usual package installation. CI runs these checks and retains the HTML
documentation and validation report.

The independent validation covers all 66 pairs through 42 (628 components,
640 origins), all five published fixtures, and stress cases `(8,96)`,
`(446,494)`, `(456,488)`, `(498,500)`, reaching saturation index 68. Native tests
also cover huge shears, signed residue conditions, the strict root-bound
boundary, corrupt certificates, exact integers beyond 64 bits, quoted paths,
budget failures, interrupted catalogues, and corrupt-shard repair.
See [performance and validation](../docs/performance.md) for measured results
and the distinction between certificate checks and classification audits.
