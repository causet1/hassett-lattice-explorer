# Exact implementation and certificate format

This document describes the executable algorithm in `hassett_lattices/core.py` and the independent verifier in `scripts/verify_certificates.py`. Both use the Python standard library only. The algorithm computes the **reduced irreducible components** of the intersection of two **distinct** Hassett divisors. It does not compute scheme-theoretic multiplicities, equations of cubic fourfolds, or rational parametrizations.

The geometric foundation is Song Yang and Xun Yu, [*On lattice polarizable cubic fourfolds*](https://arxiv.org/abs/2103.09132), Algorithm 7.6, together with their nonemptiness and irreducibility theorem and Corollary 7.5. The K3 test uses their Theorems 8.8 and 8.9. The mathematical completeness statement depends on those results; software certificate verification alone does not establish the completeness of an enumeration.

Throughout this document, `h` denotes the square of the hyperplane class. In every returned component basis, its coordinate vector is `(1, 0, 0)` and its square is 3.

## 1. Input normalization and starting lattices

Both inputs must be integers satisfying

$$d_i>6,\qquad d_i\equiv0,2\pmod6.$$

They must be distinct. In a mixed pair, the discriminant congruent to 2 modulo 6 is put first. Otherwise the pair is sorted increasingly. The JSON preserves both the caller's `input_pair` and the normalized `d1`, `d2`.

Put $p_i=1$ when $d_i\equiv2\pmod6$, and $p_i=0$ otherwise. Set $a_i=(d_i+p_i)/3$. The starting lattice, with ordered basis $(h,u,v)$, has Gram matrix

$$G_\tau=\begin{pmatrix}3&p_1&p_2\\p_1&a_1&\tau\\p_2&\tau&a_2\end{pmatrix}.$$

The two prescribed primitive rank-two sublattices are $\langle h,u\rangle$ and $\langle h,v\rangle$, with discriminants $d_1$ and $d_2$. The determinant identity is

$$\det G_\tau=\frac{d_1d_2-(3\tau-p_1p_2)^2}{3}.$$

Because the leading rank-two principal minor is $d_1>0$, positivity of this determinant is equivalent to positive definiteness. Let

$$r=\left\lfloor\sqrt{d_1d_2-1}\right\rfloor.$$

All possible parameters satisfy

$$\left\lceil\frac{p_1p_2-r}{3}\right\rceil\le\tau\le\left\lfloor\frac{p_1p_2+r}{3}\right\rfloor.$$

The subtraction of 1 implements the strict determinant inequality using integer arithmetic. If $p_1p_2=0$, the implementation retains only $\tau\ge0$, as allowed by the sign symmetry in Yang–Yu's algorithm. If $p_1=p_2=1$, negative parameters must be retained.

## 2. Exact exclusion of roots

A root is an integral vector of square 2. For a positive definite Gram matrix

$$G=\begin{pmatrix}3&p^{\mathsf T}\\p&B\end{pmatrix},\qquad H=3B-pp^{\mathsf T},$$

consider a vector $x=(x_0,y,z)$ of square $m$ and with $(h,x)=k$. Completing the square gives

$$H(y,z)=3m-k^2,\qquad x_0=\frac{k-p_1y-p_2z}{3}.$$

If $H=\begin{pmatrix}A&D\\D&C\end{pmatrix}$ and $q=3m-k^2\ge0$, Cauchy–Schwarz gives the complete coordinate bounds

$$|y|\le\left\lfloor\sqrt{\frac{qC}{AC-D^2}}\right\rfloor,\qquad |z|\le\left\lfloor\sqrt{\frac{qA}{AC-D^2}}\right\rfloor.$$

The implementation enumerates that finite rectangle, checks the quadratic equation exactly, and requires $k-p_1y-p_2z$ divisible by 3. For a root, $m=2$ and $|k|^2\le6$, so only $k=-2,-1,0,1,2$ occur. Every root is therefore examined. No bounded heuristic search or floating-point eigenvalue test is used.

A starting lattice with a root is discarded: every overlattice contains that same root. Returned rejected starting candidates include an explicit integral `root_witness`.

## 3. Complete saturation enumeration

The sum of the two primitive rank-two markings need not itself be primitive in the algebraic lattice. Omitting its proper overlattices gives an incomplete answer; the additional determinant-20 component of $\mathcal C_{20}\cap\mathcal C_{12}$ is a regression example.

For this rank-three problem, the primitiveness constraints permit a particularly direct enumeration. Write

$$M=\mathbf Zh+\mathbf Zu+\mathbf Zv,\qquad K_1=\langle h,u\rangle,\qquad K_2=\langle h,v\rangle.$$

Suppose $N\supset M$ is a finite-index integral overlattice and $K_1$ is primitive in $N$. Then $N/K_1$ is free of rank one. If $[N:M]=n$, the image of $v$ in that quotient generates a subgroup of index $n$. Consequently a generator of $N/K_1$ can be lifted to a vector $w$ such that

$$w=\frac{ah+bu+v}{n},\qquad N=\langle h,u,w\rangle.$$

Changing the lift by integral multiples of $h,u$ puts $0\le a,b<n$. Conversely, every such vector produces a rank-three overmodule with $K_1$ primitive. In its basis $(h,u,w)$ one has

$$v=nw-ah-bu.$$

Therefore $K_2$ is primitive in $N$ exactly when

$$\gcd(b,n)=1.$$

Also $n^2\det N=\det M$. The implementation enumerates every positive $n$ with $n^2\mid\det M$, and every residue pair $a,b$ meeting the gcd condition. This proves that no noncyclic gluing cases are missed: the primitiveness of $K_1$ forces $N/M$ cyclic.

With $p=p_1$, $q=p_2$, the three new Gram entries are

$$ (h,w)=\frac{3a+pb+q}{n},\qquad (u,w)=\frac{pa+a_1b+\tau}{n}, $$

$$ w^2=\frac{3a^2+a_1b^2+a_2+2pab+2qa+2\tau b}{n^2}. $$

All three must be integers. The first vector must remain distinguished: by Yang–Yu Lemma 4.4, when $h^2=3$, the condition $h^\perp$ even is equivalent to

$$G_{ii}\equiv G_{0i}\pmod2\quad\text{for every basis vector }i.$$

The first two parity conditions already hold in the starting lattice, so only $w^2\equiv(h,w)\pmod2$ is new. Every resulting integral distinguished overlattice is subjected to the exact root test.

## 4. Removing duplicate components

Two lattice presentations describe the same component when they are integrally isometric with the distinguished vector identified. Equality of determinants is only a preliminary filter.

For source and target Gram matrices $G_s,G_t$, the engine seeks an integer matrix $U$ satisfying

$$U^{\mathsf T}G_tU=G_s,\qquad Ue_0=e_0,\qquad\det U=\pm1.$$

The first column is fixed. The other two columns are enumerated by their required norms and pairings with $h$, using the exact finite search in Section 2. The mutual pairing and determinant are then checked. Thus a negative isometry result is exhaustive.

The distinction matters in computations. For $\mathcal C_8\cap\mathcal C_{96}$, two components have determinant 64 but are not isometric preserving $h$. Conversely, in $\mathcal C_8\cap\mathcal C_{24}$, the index-two saturation from $\tau=0$ is isometric to the index-one lattice at $\tau=4$, so both origins are stored on one component.

## 5. K3 lattice admissibility

For the same binary Schur form, write its polynomial as

$$f(y,z)=Ay^2+2Dyz+Cz^2=\lambda g(y,z),\qquad\lambda=\gcd(A,2D,C).$$

The content is the gcd of the **polynomial coefficients**, so the middle coefficient is $2D$. This distinction prevents a factor-of-two error.

The condition that $h$ splits off orthogonally is equivalent to $\gcd(3,G_{01},G_{02})=3$. If it does not split, Yang–Yu Theorem 8.8 says that the lattice is admissible exactly when $\lambda$ is divisible by neither 4, nor 9, nor any odd prime congruent to 2 modulo 3. If it splits, Theorem 8.9 adds the requirement that the primitive polynomial $g$ represent 1 modulo 3. The latter test examines all nine pairs in $(\mathbf Z/3)^2$.

The content $\lambda$ may be 2 or 6. The nonemptiness requirement $d>6$ for a Hassett **divisor label** must not be applied to $\lambda$.

`admissible_discriminant(d)` checks both the divisor condition and Hassett's arithmetic condition. `lattice_k3_association(G)` applies the more general rank-three criterion. A positive lattice test is not a rationality algorithm. A negative test concerns this algebraic lattice; higher-rank specializations may acquire an admissible rank-two sublattice.

## 6. Python API and resource semantics

```python
from hassett_lattices import Limits, intersection_components

result = intersection_components(20, 12)
assert result["complete"]
assert result["component_count"] == 6

custom = intersection_components(
    8, 96,
    limits=Limits(max_work=10_000_000, timeout_seconds=120.0),
)
unlimited = Limits(max_work=None, timeout_seconds=None)
```

The default is `Limits(max_work=5_000_000, timeout_seconds=60.0)`. A work unit is an iteration of a potentially long finite search, not a CPU instruction; it is useful as a deterministic budget for this implementation. Time is measured with Python's monotonic clock. Time checks occur periodically in the search and once before returning. This is a cooperative limit, not a process-level hard timeout.

`None` disables the corresponding limit. Invalid parameters raise `ValueError`. Exhaustion raises `ResourceLimitError`; there is no partial-success return value. The command-line interface exits with status 2 and does not write an output JSON file when a computation fails. It writes a requested output only after a complete result exists. Existing output files are not removed on failure.

Large input values remain computationally expensive even though the search is finite. Integer factorization uses exact trial division, which also consumes the work budget. Arbitrary-precision integer arithmetic prevents machine-integer overflow. No timing value participates in a mathematical decision.

## 7. JSON schema, version 1.0

The top-level result has the following fields.

| Field | Meaning |
|---|---|
| `schema_version` | Currently `"1.0"`. |
| `algorithm`, `reference` | Algorithm name and source URL. |
| `input_pair` | Original discriminants in caller order. |
| `d1`, `d2` | Normalized discriminants, as in Section 1. |
| `complete` | `true` only after the whole computation finishes. |
| `component_count` | Length of `components`. |
| `components` | Representatives of the isometry classes. |
| `candidates` | All positive definite starting $G_\tau$, including rejected roots. |
| `diagnostics` | Parameter sets, search counts, work units, and elapsed seconds. |
| `scope` | Statement that scheme-theoretic multiplicities are not computed. |

A `components` entry contains `id`, `gram`, `determinant`, `rank: 3`, `h: [1,0,0]`, `tau`, `index`, `origins`, and `k3_association`. The displayed `tau` and `index` describe the **first retained origin**; they are not intrinsic invariants of the component. All construction routes are in `origins`.

Each origin has:

| Field | Coordinate meaning |
|---|---|
| `tau`, `index`, `a`, `b` | Parameters $\tau,n,a,b$ of its construction. |
| `base_gram` | $G_M$ in the starting basis $(h,u,v)$. |
| `overlattice_gram` | $G_N$ in the construction basis $(h,u,w)$. |
| `basis_map_to_representative` | Matrix $S$ whose columns express that construction basis in the final representative basis. |
| `embedding` | Matrix $E$ whose columns express the **starting basis** $(h,u,v)$ in the final representative basis. |

Explicitly, put

$$E_0=\begin{pmatrix}1&0&-a\\0&1&-b\\0&0&n\end{pmatrix}.$$

Then the certificate identities are

$$S^{\mathsf T}G_{\mathrm{rep}}S=G_N,\qquad E=SE_0,\qquad E^{\mathsf T}G_{\mathrm{rep}}E=G_M.$$

Also $Se_0=Ee_0=e_0$, $|\det S|=1$, and $|\det E|=n$. The images of the two rank-two markings are respectively columns $(0,1)$ and $(0,2)$ of $E$. Each is primitive precisely when the gcd of its three maximal minors is 1.

The K3 object records the discriminant polynomial as `[A, 2D, C]`, its `content`, its `primitive_form`, `h_splits_orthogonally`, a possible `mod3_witness`, the Boolean `admissible`, and textual `obstructions`, `criterion`, and `interpretation`. The verifier checks the mathematical values, not the wording of the explanatory strings.

Each starting candidate stores `tau`, `gram`, `determinant`, `root_free`, `root_witness`, and `accepted_overlattices`. The last field counts accepted **marked construction routes**, before global isometry deduplication. Diagnostic `accepted_marked_lattices` equals the total number of origins; `duplicate_count` is that total minus `component_count`.

## 8. Independent certificate verification

```bash
python -m hassett_lattices intersect 20 12 --output result.json
python scripts/verify_certificates.py result.json
```

The verifier accepts one result, a JSON list of results, or a catalogue object with a `pairs` or `results` list. Several filenames may be supplied. It uses no package imports and no third-party dependencies: determinant calculations, matrix identities, primitivity checks, and the K3 arithmetic are implemented locally.

Its root check is deliberately different from the engine's Schur-form search. For every coordinate of a root $x$, it uses

$$|x_i|^2\le2(G^{-1})_{ii}.$$

The diagonal inverse entries are exact cofactor/determinant quotients. The resulting finite three-dimensional integer box is exhaustively searched. By default the verifier permits two million box-vector evaluations across all supplied files; `--max-vectors` changes that budget, and `--no-limits` removes it. Reaching the budget fails explicitly rather than passing an unverified file.

The verifier checks positive definiteness, integrality, distinguishedness, rootlessness, both rank-two discriminants and primitivity, every basis/inclusion identity above, recorded root witnesses, and the numerical K3 decisions. It also checks basic count/provenance consistency.

**What it does not certify:** it does not rerun all overlattice parameter searches, establish that no component is missing, prove pairwise nonisometry of every listed representative, or prove the geometric theorems underlying the algorithm. A successful run means that the supplied lattice constructions and their stated invariants are valid. Completeness additionally uses the algorithm, its mathematical proof, and the regression tests.
