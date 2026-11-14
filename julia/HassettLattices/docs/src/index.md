# HassettLattices.jl

This package computes every reduced irreducible component of the intersection
of two distinct nonempty Hassett divisors using exact lattice arithmetic.
For installation and local development, see the package README.

```jldoctest
julia> using HassettLattices

julia> r = intersection_components(12, 20);

julia> length(r)
6

julia> sort([Int(discriminant(c)) for c in r])
6-element Vector{Int64}:
 20
 32
 53
 68
 77
 80

julia> verify_result(r)
true
```

Each component carries its Gram matrix, determinant, whole-lattice K3 decision,
and every construction origin. `input_pair` retains input order; `pair` uses the
normalization of Algorithm 7.6. Iteration and indexing refer to components.
`gram_matrix(c)` returns a copy; `hecke_lattice(c)` returns an independent Hecke
lattice for further experiments.

## Markings and K3 associations

```julia
r = intersection_components(8, 12)
[c.k3_association.admissible for c in r]  # [false, true, false]
primitive_markings(r[2], 100)
k3_witness(r[2], 100)
lattice_invariants(r[2])
```

The discriminant of a rank-three component is distinct from the discriminants
of its rank-two markings. `primitive_markings` enumerates the latter through
a bound, modulo sign and addition of the distinguished vector. The unbounded
whole-lattice criterion uses Yang--Yu Theorems 8.8--8.9. A bounded witness search
returning `nothing` only means that no witness was found within its bound.
K3 admissibility is not a rationality decision.

## Exact certificates and interchange

```julia
write_result("intersection.json.gz", r)
loaded = read_result("intersection.json.gz"; classification=true)
data = result_dict(loaded; timing=false)
```

`read_result` verifies certificates and starting-parameter coverage by default.
With `classification=true`, it also recomputes the full origin partition and
representative isometry classes. This is a check using the same backend. For
an independent implementation use the repository's `scripts/verify_certificates.py`
or `scripts/audit_classification.py`. JSON integers remain exact, including
values larger than the machine integer range. The web explorer has its own
safe-integer import restrictions; arbitrary-size Julia data need not be suitable
for JavaScript arithmetic.

## Batch runs and limits

```julia
limits = Limits(max_work=20_000_000, timeout_seconds=180.0)
index = build_catalogue("catalogue", 42; limits, stop_after=10)
index["complete"]  # false: an intentional checkpoint
index = build_catalogue("catalogue", 42; limits)
index["complete"]  # true, unless a pair exhausted its limits
```

The builder writes schema-1.1 indices and schema-1.0 pair certificates, with
gzip, SHA-256 hashes, deterministic mathematical JSON and atomic replacement.
Resumption verifies existing certificates and recomputes corrupt shards.
Set `recheck_classification=true` to recompute completeness before reuse.
Resource failures are recorded and retried on the next run. Interrupted runs
retain complete shards. Use one writer per output directory, and a new directory
when reducing the bound or changing compression. Pair files retain all origins;
index component totals count records across pairs, not globally distinct loci.

Limits are cooperative and count application loops and backend calls. A long
Hecke/FLINT operation cannot be preempted, and time is checked on return. Julia
compilation is included in the elapsed time of a first call. Use a larger timeout
for cold batch starts; `nothing` disables an individual limit. A process-level
timeout is needed for a hard deadline. A single intersection returns a complete
result or throws, never an incomplete component list.

## Command line

Run `julia --project=julia/HassettLattices julia/HassettLattices/bin/hassett.jl`
followed by one of:

```text
intersect 12 20 --output result.json.gz
admissible 14
verify result.json.gz --classification
labels result.json.gz --component 1 --bound 500
catalogue data 42 --timeout 180
```

Use `--help` for all flags. Exit codes are 0 (success), 1 (incomplete catalogue)
and 2 (invalid input, verification failure or exhausted single-result limits).
