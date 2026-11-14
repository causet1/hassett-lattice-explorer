# Implementation conventions and backend reuse

The package follows the official Macaulay2
[package layout](https://macaulay2.com/doc/Macaulay2/share/doc/Macaulay2/Macaulay2Doc/html/_creating_spa_sppackage.html)
and [documentation conventions](https://macaulay2.com/doc/Macaulay2/share/doc/Macaulay2/Macaulay2Doc/html/_writing_spdocumentation.html):
`newPackage`, explicit exports, camelCase operations, capitalized types and
options, `method` dispatch for option-bearing operations, auxiliary source
files, `beginDocumentation`, SimpleDoc nodes, executable examples, and `TEST`
blocks run by `check`. Four-space indentation and explicit dependency imports
follow the maintained `JSON` and `ForeignFunctions` packages. Keep arithmetic
over `ZZ`/`QQ`; use reals only for elapsed time.

| Task | Reused implementation | Our application-specific code |
| --- | --- | --- |
| Exact integers, matrices, determinant, gcd, factorization, Smith form | Macaulay2 Core and its GMP/FLINT/NTL backends | Fixed-rank formulas and validation |
| Exact integer square root | GMP `mpz_sqrt` via the published [ForeignFunctions](https://msp.org/jsag/2025/15-1/p01.xhtml) package | Nonnegative input guard |
| Unimodular preconditioning | [LLLBases](https://macaulay2.com/doc/Macaulay2/share/doc/Macaulay2/LLLBases/html/___L__L__L.html), `Strategy=>NTL` | Certify and transport the change matrix |
| JSON strings, objects, arrays, arbitrary integers | [JSON](https://macaulay2.com/doc/Macaulay2/share/doc/Macaulay2/JSON/html/index.html), including its existing Parsing fallback | Matrix conversion and narrow compatibility wrappers |
| Compression and hashing | System gzip, SHA-256 tools | Literal filename quoting, manifests, atomic checkpoints |
| Algebraic geometry of explicit fourfolds | [SpecialFanoFourfolds](https://macaulay2.com/doc/Macaulay2/share/doc/Macaulay2/SpecialFanoFourfolds/html/index.html) | Documented integral Gram handoff; no private geometry dependency |

No applicable published Macaulay2 complete rank-three **marked** short-vector
and isometry interface was found in the installed packages or official
documentation. The Schur-form enumeration is consequently implemented here.
It solves the application's quadratic equation exactly, fixes `h`, and
transports witnesses through certified unimodular changes. It does not attempt
to replace a general lattice library. Julia continues to reuse Hecke's general
short-vector, isometry, and automorphism algorithms.

`LLLBases` reduces Euclidean columns, not an input Gram matrix. For
`H=[[A,B],[B,C]]`, put `delta=det H` and `t=floor(sqrt(delta))`. We pass the
integral surrogate `M=[[A,B],[0,t]]` to LLL. Its Euclidean form satisfies
`(A/4)*v' H v <= ||M v||^2 <= A*v' H v`, so it avoids squaring the conditioning
of `H`. We certify `reduced=M*U` and `abs(det U)=1`, and retain the map only if
it reduces the product of the
diagonal coefficients, hence the area of the dual coordinate bounds.
Completeness follows from exact enumeration of `U^t H U`, regardless of
whether that form is reduced. Do not label this a Gram-LLL implementation.

Two JSON 0.7 compatibility details are covered by tests:

- Jansson's decoder rejects integers outside signed 64-bit range. The existing
  `jsonTextP`, `utf8Analyzer`, and `processJSON` symbols are imported from JSON
  only for its exact parser fallback. This is the sole private dependency
  interface in the library; check it when upgrading Macaulay2.
- JSON's real encoder can emit `.5`, which is invalid JSON. A private wrapper
  extends `toJSON` for our own type to supply the leading zero. No upstream
  method is replaced, and no parser or encoder is copied.

Macaulay2's `//` and `%` truncate toward zero. Signed bounds use exact rational
`floor`/`ceiling`, and congruence starts are normalized explicitly. Ranges passed
to `apply` can produce sequences rather than lists; convert deliberately when
building JSON arrays. Matrices inherit `HashTable`, so matrix cases precede
generic table handling. M2 `for ... from ... to ...` endpoints are machine
integers; unbounded mathematical coordinates use `while` loops over `ZZ`, so
large inputs still reach the cooperative resource checks. These are correctness
concerns, not cosmetic choices.

Core file I/O treats a leading `!` as a shell pipe. All public file paths are
resolved to absolute literal paths before reaching Core, and shell-tool paths
are single-quoted separately. Tests cover both mechanisms.

`ForeignFunctions` before version 0.7 had a garbage-collection issue for GMP
objects; the minimum Macaulay2 version is 1.26.05. The package checks its version.
Monotonic timing and atomic rename use documented POSIX APIs via the same FFI.
Support is limited to Linux and macOS; native Windows is not claimed.

Before changing mathematical code, run native tests, independent cross-language
validation, and documentation examples. Preserve all origins and stable
component IDs. Witnesses may differ between backends but must satisfy the
exact matrix identities. Certificate verification and optional classification
re-enumeration have distinct promises; keep both explicit in documentation.
Measure warm engine timing separately from startup, Docker, and serialization.

Original source in this directory is MIT-licensed. External package code has
not been copied; its original authors and licenses remain applicable. See the
repository's mathematical citations and AI-assistance disclosure in
`CITATION.cff`.
