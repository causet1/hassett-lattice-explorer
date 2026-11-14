# Algorithm and backends

The geometric input is [Yang--Yu, *On lattice polarized cubic fourfolds*](https://arxiv.org/abs/2103.09132),
Algorithm 7.6 and Theorems 8.8--8.9. The repository's `ALGORITHM.md` gives the
finite saturation proof and exact formulas. The package computes rank-three,
positive-definite, distinguished, root-free lattices with two primitive
rank-two markings. The sum of the markings need not be saturated.

## Reused lattice algorithms

Nemo/FLINT supplies arbitrary-size integers, matrix arithmetic, factorization,
modular inverses, determinants and Smith normal forms. Hecke supplies exact
short vectors, lattice isometry and automorphism generators. See
[Hecke integer lattices](https://docs.hecke.thofma.com/stable/manual/quad_forms/integer_lattices/)
and [Nemo](https://nemocas.github.io/Nemo.jl/stable/).

Hecke's isometry witness uses **row coordinates**:
`T * G_target * transpose(T) == G_source`. This package's certificates use
**column coordinates**: `transpose(U) * G_target * U == G_source`.
An ordinary isometry may move the distinguished vector. We traverse its finite
orbit under the target's Hecke automorphism generators, retaining a transport
matrix. If the orbit reaches plus or minus the target distinguished vector,
composition, transposition and (if necessary) negation give the marked witness.
Exhausting the orbit proves there is no marked isometry. Equal determinant alone
never identifies components.

## Congruence search optimization

For normalized labels, let `p,q` be 0 or 1 and `aa=(d1+p)/3`. An index `n`
construction uses `(a*h+b*u+v)/n`. The two linear integrality conditions are

```text
3a + p*b + q = 0 (mod n)
p*a + aa*b + tau = 0 (mod n).
```

Eliminating `a` gives `d1*b = p*q - 3*tau (mod n)`. Solve this linear congruence
by gcd and modular inverse, retain `gcd(b,n)=1`, then solve the first equation
for `a`. Recheck the second equation: elimination alone is insufficient when
3 is not invertible modulo `n`. This enumerates exactly the original linear
solutions with at most `gcd(d1,n)*gcd(3,n)` candidate lifts, rather than scanning
all `n^2` residues. The quadratic norm integrality and distinguished parity
checks still follow. Sorting `(a,b)` preserves historical construction order.

The implementation also groups representatives by determinant before isometry
testing and caches root searches and Hecke lattices within an intersection.
Caches are local to each call; a batch does not retain every lattice in memory.
No heuristic equivalence or floating-point cutoff is used.

Before invoking Hecke for roots, an exact Schur-form bound can certify their
absence. For `H(y,z)=A*y^2+2B*y*z+C*z^2`, we have
`H(y,z) >= (min(A,C)-abs(B))*(y^2+z^2)`. A norm-two vector requires
`H(y,z) <= 6`. Thus a coefficient strictly greater than six rules out all
nonzero integer pairs, while `y=z=0` would require `3*x^2=2`. The equality
case still goes to Hecke. This cheap certificate avoids a general short-vector
call when an elementary bound already settles the question.

## Scope of verification

Certificate verification checks positive definite Grams, distinguished parity,
root witnesses/root exclusion, exact inclusion and basis-change identities,
primitive markings, the index/determinant identity, K3 arithmetic, unique
origins, starting-parameter coverage and counts. Classification verification
additionally reruns the finite enumeration. Independent Python integration
uses three-dimensional coordinate boxes and rational saturation matrices.

Performance depends on the problem and compilation state. The lightweight
Python reference is still competitive for small rank-three inputs. This Julia
package's primary advantages are exact algebra interoperability, established
lattice algorithms, and a maintainable basis for larger extensions. Measure
warm computation separately from package load and compilation.
