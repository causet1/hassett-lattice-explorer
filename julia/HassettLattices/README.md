# HassettLattices.jl

`k3_certificate(l)` returns an exact whole-lattice decision with an explicit
primitive admissible marking or arithmetic obstruction. Positive searches
increase their bound under one shared resource budget; the older `k3_witness`
remains a bounded search. See the repository's [mathematical audit](../../docs/math-audit.md)
and [benchmark dossiers](../../docs/benchmark-components.md).

Exact classification of the reduced components of intersections of two
distinct Hassett divisors, implementing Yang--Yu Algorithm 7.6. The package
uses **Hecke and Nemo/FLINT**, with arbitrary-size integers throughout all
mathematical decisions. No Python executable or external service is needed.

Requires Julia 1.10 or later, Hecke 0.41 and Nemo 0.57. The package is currently
distributed from this repository, not the Julia General registry. Access to
the repository is required to install it:

```julia
using Pkg
Pkg.add(url="https://github.com/causet1/hassett-lattice-explorer",
        subdir="julia/HassettLattices", rev="main")
using HassettLattices

r = intersection_components(12, 20)
length(r)                              # 6 reduced components
sort(discriminant.(components(r)))      # [20, 32, 53, 68, 77, 80]
verify_result(r; classification=true)  # true
write_result("12-20.json.gz", r)
r = read_result("12-20.json.gz")
```

Pin `rev` to a commit for reproducible research. For a local checkout:

```sh
julia --project=julia/HassettLattices -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
julia --project=julia/HassettLattices julia/HassettLattices/bin/hassett.jl intersect 12 20 -o result.json
```

Useful operations include:

- `gram_matrix(c)`, `origins(c)`, `discriminant(c)`, and `lattice_invariants(c)`.
- `hecke_lattice(c)` for Hecke's general lattice API; `change_basis(c, U)` for
  a unimodular column basis change fixing the first vector.
- `norm_two_vector(G)` and `h_fixed_isometry(source, target)` with exact witnesses.
- `lattice_k3_association(c)` for the whole-lattice untwisted K3 criterion.
- `primitive_markings(c, bound)` for every primitive rank-two marking through
  the distinguished class within a discriminant bound, modulo sign and
  addition of that class. `k3_witness(c, bound)` searches for an admissible one.
- `positive_parameters`, `base_gram`, `saturation_indices`, and
  `saturation_residues` for examining each step of the finite algorithm.
- `build_catalogue("data", 42)` for resumable, hashed, compressed catalogue
  shards compatible with the existing web explorer and Python verifier.

See the [tutorial](docs/src/index.md), [algorithm and backend notes](docs/src/algorithm.md),
[API reference](docs/src/api.md), and [contributor guide](CONTRIBUTING.md).
The [examples](examples/) are executable Julia scripts.

The result classifies reduced geometric components. It does not compute scheme
multiplicities or decide rationality. A failed bounded `k3_witness` search does
not prove nonexistence; the whole-lattice criterion does decide admissibility.
Resource limits are cooperative: a running Hecke/FLINT call cannot be interrupted
by this package, and is checked for elapsed time when it returns. Compilation
also contributes to elapsed time on the first call.

The MIT license covers this implementation and its original documentation.
Dependencies retain their own licenses. Backend algorithms are called through
published APIs, not copied into this repository; see [reuse and conventions](CONTRIBUTING.md).
