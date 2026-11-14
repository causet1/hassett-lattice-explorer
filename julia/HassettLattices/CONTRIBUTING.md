# Development and published-code reuse

The implementation follows [Hecke's contributor conventions](https://github.com/thofma/Hecke.jl/blob/master/CONTRIBUTING.md):
two-space indentation, ASCII Julia source, descriptive lowercase names with
underscores, UpperCamelCase types, and approximately 80-column lines. Public
methods have Julia docstrings and Documenter references. Mutating helpers end
in `!`; public matrix getters return defensive copies. Result fields are
inspectable Julia objects, not immutable storage: mutating their vectors or
Nemo matrices invalidates certificates until rechecked.

We also follow the [Julia style guide](https://docs.julialang.org/en/v1/manual/style-guide/)
and [Pkg package layout](https://pkgdocs.julialang.org/v1/creating-packages/).
Functions accept ordinary exact integers and Nemo integers. Bool, floating
point labels and nonintegral Gram entries are rejected. Public result types
avoid `Any` except schema diagnostics. Package dependencies have compatibility
bounds; `Manifest.toml` is intentionally untracked for this library.

| Operation | Published implementation reused |
| --- | --- |
| Arbitrary-size integers, exact matrices, factorization, modular inverses, determinants, Smith normal forms | Nemo / FLINT |
| Exact norm-two search and bounded binary marking enumeration | Hecke `short_vectors_iterator`, `short_vectors` |
| Lattice isometry and automorphism generators | Hecke `is_isometric_with_isometry`, `automorphism_group_generators` |
| JSON with arbitrary-size integers and stable key ordering | JSON.jl 1.13+ |
| Gzip, argument parsing, hashes and timestamps | CodecZlib, ArgParse, Julia SHA and Dates |

Hecke's isometry implementation uses Plesken--Souvignier,
*Computing isometries of lattices*, J. Symbolic Computation 24 (1997), 327--334,
[DOI 10.1006/jsco.1996.0130](https://doi.org/10.1006/jsco.1996.0130).
Our code adds only the Hassett-specific parameterization, marked-vector orbit
transport, K3 criteria, provenance and interchange. General lattice algebra
must remain in the backend. The Python implementation remains useful as a
small dependency-free reference and independent comparison.

## Checks

```sh
julia --project=julia/HassettLattices -e 'using Pkg; Pkg.test()'
python scripts/validate_julia.py
python scripts/benchmark_engine.py --baseline d3a365b --repeat 7
```

Tests cover the five published examples, all three normalization cases,
exhaustive small congruence boxes, equal-determinant nonisometry, saturation
duplicates, 60 random basis changes, marked-vector certificates, primitive
markings, corruption, resource failures, CLI and catalogue resume. Aqua checks
package quality. Cross-language integration independently checks the 66 pairs
through 42 (628 components and 640 origins); the independent audit re-enumerates
saturations using rational matrices and tests nonisometry with full coordinate
boxes. Neither certificate checking alone nor comparing two implementations
replaces the cited geometric completeness theorem.

Additional cross-language stress cases cover equal-determinant classes,
525-component intersections and saturation index 68. Their certificates are
checked independently; the full rational-matrix classification audit remains
limited to the small catalogue.

Install developer tools and format:

```sh
julia --project=julia/HassettLattices/dev -e 'using Pkg; Pkg.instantiate()'
julia --project=julia/HassettLattices/dev julia/HassettLattices/dev/format.jl
julia --project=julia/HassettLattices/dev julia/HassettLattices/benchmark/benchmarks.jl
```

Build documentation (including doctests, no deployment):

```sh
julia --project=julia/HassettLattices/docs -e 'using Pkg; Pkg.develop(path="julia/HassettLattices"); Pkg.instantiate()'
julia --project=julia/HassettLattices/docs julia/HassettLattices/docs/make.jl
```

Keep benchmarks separate from correctness tests. Warm Julia before measuring;
report startup/compilation separately. Never claim faster execution solely
from a language choice. Preserve origin order and representative identities
when optimizing; check the noninvertible congruence cases and resource behavior.
