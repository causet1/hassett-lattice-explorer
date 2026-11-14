# Mathematical completion audit

This audit addresses the four mathematical deliverables in the problem brief:
classification correctness, the published benchmark components, constructive K3
decisions, and precise rationality implications. It checks the implementation
against primary sources and adds a second saturation construction. It is an
AI-assisted source-level review with executable arithmetic checks, not external
peer review or a proof-assistant formalization of the geometric theorems.

## The lattice-to-component correspondence

Write o=h². All lattices below are integral and positive definite; o²=3 and
o-perp is even. The implementation fixes o, but does not fix the two rank-two
labels during isometry deduplication. We classify loci of cubic fourfolds,
rather than cubic fourfolds equipped with an ordered pair of markings.

The geometric inputs were checked in
[Yang–Yu, arXiv:2103.09132v1](https://arxiv.org/html/2103.09132v1):

| Step | Primary result | Hypothesis used here |
|---|---|---|
| Remove forbidden lattices | Lemma 4.11, Corollary 5.5 | Distinguished element, positivity, no square-two vector |
| Realize the full algebraic lattice | Corollary 5.5 | Rank 3 and discriminant-group length at most 3 |
| Nonempty irreducible locus of dimension 18 | Theorem 5.1 | Rank plus length at most 20; here at most 6 |
| No splitting by ambient embeddings | Proposition 5.9 | Embeddings preserve o and are primitive; equivalence is under Γ⁺ |
| Recover the intersection components | Proposition 7.3, Corollary 7.5 | Two distinct valid Hassett labels |

Here is the complete argument connecting those inputs to the actual search.

1. Distinct primitive rank-two labels through o cannot have the same rational
   span: each would be the intersection of that span with the ambient lattice.
   Their sum therefore has rank three. Normalize its two generators to obtain
   G_t. Sylvester's criterion gives the strict bound
   (3t−ε₁ε₂)² < d₁d₂. Changing the sign of a generator with ε=0 accounts for
   the optional t≥0 symmetry. No such sign truncation is used when both ε=1.
2. Let N be the saturation of the sum M inside A(X). Because K₁ is primitive
   in A(X), it is primitive in N. The quotient N/K₁ is free of rank one.
   The image of M/K₁ has index n in it. Lifting a positive quotient generator
   yields N=⟨o,u,w⟩, with nw=ao+bu+v. Integral changes of w reduce a,b modulo n.
   The presentation of N/K₂ has relation (−b,n); its torsion vanishes precisely
   when gcd(b,n)=1. This proves that every compatible quotient N/M is cyclic.
   Cyclicity is a consequence of primitivity, not a restriction imposed without
   justification. The determinant identity n² det(N)=det(M) makes n finite.
3. Integral pairings of w with o,u,w test integrality of N. The congruence
   w²≡(o,w) mod 2 tests distinguishedness. Indeed, 3x−(o,x)o is orthogonal to o,
   and its square has parity x²−(o,x). This proves the equivalence with even
   o-perp. Positive definiteness is unchanged by an invertible rational basis
   map. The root test covers the whole lattice. A root in M persists in N,
   justifying early rejection. A vector of square one also produces a root:
   its pairing with o is ±1, and o∓v has square two.
4. Every accepted N gives a nonempty irreducible locus of dimension 18 and
   contains the two primitive labels. Conversely every point of the divisor
   intersection supplies one of these N, including points of higher algebraic
   rank. Thus the intersection is exactly a finite union of the returned loci.
   Each N occurs as the full A(X) of some cubic. If two loci coincided, the
   other lattice would embed primitively in this A(X) with equal rank. Its
   quotient is finite and torsion-free, hence zero. The embedding is therefore
   an o-preserving isometry. Distinct equal-dimensional irreducible loci cannot
   properly contain one another. These facts prove the claimed bijection.

The ambient embedding statement is essential: matching an abstract Gram alone
would not justify irreducibility without it. Also, an integral finite-index
inclusion of equal-rank lattices is generally not primitive. One must retain
successful nonmaximal overlattices; they need not define contained loci.

### An independent saturation construction

`scripts/audit_hnf.py` enumerates general integer inclusion matrices in row
Hermite form, before imposing either primitive-label condition. For index n,
these have rows (a,x,y), (0,b,z), (0,0,c), with abc=n, 0≤x<b and 0≤y,z<c.
Left unimodular row operations change only the chosen basis of N, so every
inclusion occurs in this list. The candidate Gram is E⁻ᵀ G_t E⁻¹, calculated
by rational Gaussian elimination.

Primitivity is checked using gcds of the two-by-two minors of the relevant
columns of E. In particular K₁ primitivity forces ab=1, hence a=b=1 and x=0.
K₂ primitivity then forces gcd(z,c)=1. Only after these checks are surviving
matrices translated to the engine's residue convention for comparison.
This independently recovers the cyclic-extension restriction and tests the
coverage of the specialized enumeration, including possible noncyclic inputs.

The audit checks every saturation origin, independently checks roots, and
tests equal-determinant representatives for marked isometry using finite
three-dimensional vector boxes. The complete 66-pair embedded catalogue passes:
628 components and 640 origins. This is a finite computational audit; the
unbounded mathematical justification is the argument above. It is not a new
audit of all 13,530 pairs through 500.

## Constructive K3 certificates

For G with rows (3,p,q), (p,r,s), (q,s,t), put

f(y,z)=(3r−p²)y²+2(3s−pq)yz+(3t−q²)z².

This is det⟨o,yo₂+zo₃⟩. Such a marking is primitive exactly when gcd(y,z)=1,
as can be seen from the minors of its two columns. Adding a multiple of o to
the second vector leaves its label unchanged. A simultaneous sign change also
leaves the marking unchanged. These are the only identifications used in the
marking enumerator; it does not quotient by all automorphisms of G.

Let λ be the gcd of the polynomial coefficients of f, including the doubled
mixed coefficient, and g=f/λ. Yang–Yu Theorems 8.8–8.9 give the decision:
λ must avoid divisibility by 4, 9, and odd primes 2 modulo 3. In the split case
gcd(3,p,q)=3, g must additionally represent 1 modulo 3. The nine residues suffice
to decide that condition. Neither λ>6 nor admissibility of det(G) is required.

All three packages now provide `k3_certificate` (Macaulay2: `k3Certificate`).
A negative certificate contains the explicit content or congruence obstruction.
A positive certificate includes a primitive vector, its rank-two Gram and
admissible discriminant. The search uses successively doubled discriminant
bounds starting at 16, with one shared work/time budget. Python and Macaulay2
enumerate the exact Schur ellipse; Julia reuses Hecke's short-vector algorithm.

Each bounded search is exhaustive: writing f=Ay²+2Byz+Cz² and Δ=AC−B² gives
(Ay+Bz)²+Δz²=A f(y,z). This bounds z and then gives exact integer endpoints
for y. The theorem guarantees existence in the affirmative case, so increasing
the bound eventually finds a witness if resources are unlimited. Resource
exhaustion raises an exception, rather than returning a negative certificate.
The existing bounded `k3_witness`/`k3Witness` APIs retain their separate meaning.

`scripts/verify_k3_certificates.py` imports no classification engine. It
recomputes the decision and checks the vector, primitive minors, rank-two Gram,
label and admissibility. Tampering and bounded-search/obstruction distinctions
are covered by regression tests. CI checks native certificates for all 628
embedded components in both Julia and Macaulay2; Python checks the same corpus.

If K is primitive in M and M is primitive in A(X), then A(X)/K is an extension
of two torsion-free groups, hence torsion-free. A positive marking therefore
persists throughout the component. A negative result concerns A(X)=M, which
holds at a very general point. It does not rule out admissible labels at
higher-rank specializations.

## Benchmark geometry and rationality

[The nineteen component dossiers](benchmark-components.md) and their
[machine-readable certificates](benchmark-components.json) complete the three
benchmark cases. Their basis changes are checked by UᵀGU=G_published and
|det(U)|=1; their saturation inclusions satisfy EᵀGE=G_base. The original
counts are 5, 8 and 6, respectively.

The rationality annotations invoke geometric theorems, with explicit scope:

- Every smooth cubic in C14 is rational; use
  [Bolognesi–Russo–Staglianò, 2.9 and 3.4](https://arxiv.org/html/1504.05863v6)
  or [Russo–Staglianò, Theorem 2](https://arxiv.org/html/1707.00999v4).
- Every smooth cubic in C26 is rational by Russo–Staglianò, Theorem 4.
  Consequently every member of both plane benchmark intersections is rational.
- In C12 ∩ C20, the normalized vector u₁−u₂ has discriminant 26 at t=1 and
  14 at t=3. Its coordinates are coprime, so these two entire components lie
  in rational Hassett divisors. The remaining four lattices fail the untwisted
  K3 criterion by content divisible by four. No irrationality claim is inferred.

For the plane P and Q=o−P, the pairings with the normalized basis are
(2,−2,1−t). Their gcd is one exactly when t is even, and then
(t/2)o+u₂ pairs to one with Q. This is an algebraic section-class certificate.
If A(X) is exactly this lattice and t is odd, every such pairing is even.
Interpreting this as the Clifford Brauer class of a smooth degree-two K3 cover
requires a **good plane**, equivalently a smooth discriminant sextic.
These hypotheses are retained in each dossier. The precise sources are
[ABBVA, Theorem A and Section 1](https://arxiv.org/html/1205.0237v4) and
[Awada, Theorems 3.1 and 3.3](https://arxiv.org/html/1910.10182v2).

For determinant 32 in C8 ∩ C14, the nontrivial Clifford invariant coexists
with rationality. We use the later BRS rationality proof: its Section 3
explicitly addresses the earlier argument's use of openness of the pfaffian
locus, and Theorem 3.7 shows that locus is not open in C14. No openness
assumption is needed by our certificates or rationality annotations.

### Integral, twisted, and rational Hodge statements

Keep four assertions separate: an integral polarized Hassett K3 association;
a twisted K3 surface with a Brauer class; a derived equivalence; and rationality
of the cubic. The code certifies the first. The plane calculation gives the
specified Brauer conclusion under its hypotheses, and the cited geometric
theorems give rationality for the particular labels above.

The current-context paragraph in the guide refers to
[KKPY v2](https://arxiv.org/abs/2508.05105v2) and
[Guéré v2, Theorem 63](https://arxiv.org/html/2603.04518v2).
The latter asserts a necessary isomorphism of **rational Hodge structures**
H⁴(X,Q)_prim ≅ H²(S,Q)(−1) for rational X. It does not assert the integral
polarized marking tested here, nor supply a converse. The parenthetical twist
there is a Tate twist, not a Brauer twist. These preprints are contextual
references; no additional rationality or irrationality test is inferred from
them, and classification correctness does not depend on them.

## Reproduce the completion checks

```sh
python scripts/audit_hnf.py web/catalogue.json --report build/validation/hnf-audit.json
python scripts/mathematical_report.py --check
python -m unittest discover -s tests -p test_mathematics.py -v
julia --project=julia/HassettLattices julia/HassettLattices/test/export_k3_certificates.jl web/catalogue.json build/julia-validation/k3-certificates.json
python scripts/verify_k3_certificates.py build/julia-validation/k3-certificates.json
mkdir -p build/macaulay2-validation
M2 --script macaulay2/export-k3-certificates.m2 "$PWD/web/catalogue.json" "$PWD/build/macaulay2-validation/k3-certificates.json"
python scripts/verify_k3_certificates.py build/macaulay2-validation/k3-certificates.json
```

These checks accompany the existing package, independent classification,
published fixture and release suites. The task does not require new claims
about scheme multiplicities, a general rationality algorithm, or all higher-rank
intersections. The four unresolved rationality entries above are mathematical
scope boundaries, not missing outputs or evidence of irrationality.
