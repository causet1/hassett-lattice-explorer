# A finite algorithm for intersections of Hassett divisors

This is a readable adaptation of the user-supplied five-page PDF, *A finite algorithm for intersections of Hassett divisors*. The unchanged [original PDF](references/hassett-intersection-algorithm.pdf) is the source of the formulas, procedure, correctness argument, and examples below. The note describes Yang–Yu's Algorithm 7.6; theorem numbering refers to [arXiv:2103.09132v1](https://arxiv.org/abs/2103.09132v1). This transcription does not claim a new mathematical result or an independent proof of the cited geometric theorems.

## Input and output

Work over $\mathbb C$. The inputs are distinct integers $d_1,d_2>6$, each congruent to $0$ or $2$ modulo $6$. The output is one distinguished integral rank-three lattice for each reduced irreducible component of $\mathcal C_{d_1}\cap\mathcal C_{d_2}$, with construction origins and inclusion matrices. In every Gram matrix, the first basis vector is $h^2$ and $(h^2,h^2)=3$.

There is no fixed mathematical bound on the labels. Implementations may impose explicit resource limits, but must not report an interrupted search as complete. Equal labels give the divisor itself as the reduced intersection, outside this rank-three procedure. Intersection multiplicities are not computed.

## 1. Starting lattices and the finite parameter interval

Define

$$
\varepsilon_i=\begin{cases}0&d_i\equiv0\pmod6,\\1&d_i\equiv2\pmod6,\end{cases}
\qquad s_i=\frac{d_i+\varepsilon_i}{3}.
$$

Each marking has Gram matrix $\left(\begin{smallmatrix}3&\varepsilon_i\\\varepsilon_i&s_i\end{smallmatrix}\right)$. Their sum, in the basis $(h^2,u,v)$, has matrix

$$
G_\tau=\begin{pmatrix}
3&\varepsilon_1&\varepsilon_2\\
\varepsilon_1&s_1&\tau\\
\varepsilon_2&\tau&s_2
\end{pmatrix},\qquad \tau\in\mathbb Z.
$$

Its determinant is

$$D_\tau=\frac{d_1d_2-(3\tau-\varepsilon_1\varepsilon_2)^2}{3}.$$

The first two leading principal minors are $3$ and $d_1>0$, so positive definiteness is equivalent to

$$(3\tau-\varepsilon_1\varepsilon_2)^2<d_1d_2.$$

Use exact integer arithmetic. For $R=\operatorname{isqrt}(d_1d_2-1)$, enumerate

$$
\left\lceil\frac{\varepsilon_1\varepsilon_2-R}{3}\right\rceil
\leq\tau\leq
\left\lfloor\frac{\varepsilon_1\varepsilon_2+R}{3}\right\rfloor.
$$

Here $\operatorname{isqrt}(m)=\lfloor\sqrt m\rfloor$. Discard any starting lattice containing an integral vector of square two; that vector persists in every extension. If one $\varepsilon_i=0$, changing the sign of its generator identifies $\tau$ and $-\tau$, so nonnegative parameters suffice as an optional optimization. If both $\varepsilon_i=1$, include negative parameters.

## 2. Every compatible finite-index extension

For a surviving matrix, write

$$M=\mathbb Zh^2+\mathbb Zu+\mathbb Zv,\quad K_1=\langle h^2,u\rangle,\quad K_2=\langle h^2,v\rangle.$$

Suppose $N\supset M$ has index $n$ and $K_1$ remains primitive in $N$. Since $N/K_1\simeq\mathbb Z$, a lift of a quotient generator yields the basis

$$N=\langle h^2,u,w\rangle,\qquad w=\frac{ah^2+bu+v}{n},\qquad 0\leq a,b<n.$$

Every permitted extension has this form; in particular, $N/M$ is cyclic. The second marking is primitive precisely when $\gcd(b,n)=1$, since

$$N/K_2\simeq\mathbb Z^2/\langle(-b,n)\rangle.$$

The identity $D_\tau=n^2\det N$ gives the complete finite enumeration:

$$1\leq n\leq\operatorname{isqrt}(D_\tau),\quad n^2\mid D_\tau,\quad 0\leq a,b<n,\quad\gcd(b,n)=1.$$

There is no further coprimality condition on $a$. Compute

$$p=\frac{3a+\varepsilon_1b+\varepsilon_2}{n},\qquad q=\frac{\varepsilon_1a+s_1b+\tau}{n},$$

$$r=\frac{3a^2+s_1b^2+s_2+2\varepsilon_1ab+2\varepsilon_2a+2\tau b}{n^2}.$$

The proposed Gram matrix is

$$H=\begin{pmatrix}3&\varepsilon_1&p\\\varepsilon_1&s_1&q\\p&q&r\end{pmatrix}.$$

Keep it exactly when $p,q,r$ are integers, $r\equiv p\pmod2$, and the whole lattice has no vector of square two. Positive definiteness follows by rational change of basis from $G_\tau$.

The parity condition means that $h^2$ is distinguished, that is, its orthogonal complement is even. In a basis beginning with $h^2$, this is equivalent to $H_{ii}\equiv H_{0i}\pmod2$; only the new vector needs a new check. Indeed, for $k=(h^2,x)$, the vector $3x-kh^2$ is orthogonal to $h^2$ and has square $9x^2-3k^2$, giving the stated parity equivalence.

Record the inclusion certificate

$$E=\begin{pmatrix}1&0&-a\\0&1&-b\\0&0&n\end{pmatrix},\qquad E^THE=G_\tau,\qquad\det E=n.$$

Include $n=1,a=b=0$, which recovers $M$ itself. Retain nonmaximal successful extensions as well: a proper equal-rank inclusion is not primitive and does not itself imply containment of the corresponding primitive lattice loci.

### Solving the linear conditions before the norm test

Both implementations now avoid scanning all $n^2$ residue pairs. Write
$p_0=\varepsilon_1$, $q_0=\varepsilon_2$, and $s_1=(d_1+p_0)/3$.
The linear conditions are

$$3a+p_0b+q_0\equiv0\pmod n,\qquad p_0a+s_1b+\tau\equiv0\pmod n.$$

Eliminating $a$ gives $d_1b\equiv p_0q_0-3\tau\pmod n$. For a congruence
$cx\equiv r\pmod n$, let $g=\gcd(c,n)$. There are no solutions unless
$g\mid r$; otherwise invert $c/g$ modulo $n/g$ and take all $g$ lifts.
First solve for $b$, retain $\gcd(b,n)=1$, then solve
$3a\equiv-p_0b-q_0\pmod n$. Recheck the second original equation, because
elimination is only a necessary condition when $3\mid n$.

Every original solution appears, and every retained lift satisfies both
equations. At most $\gcd(d_1,n)\gcd(3,n)$ lifts reach this recheck; quadratic
norm integrality and parity remain separate exact tests. Lexicographically
sorting $(a,b)$ preserves the historical origin order and representative IDs.
The diagnostic `overlattice_parameter_candidates` now counts linear solutions
reaching the norm test; historical files counted the entire residue square.
Work counters are implementation diagnostics, not mathematical invariants.

Representatives are also grouped by determinant before isometry testing.
The Julia package delegates short-vector enumeration, isometry and automorphism
groups to Hecke, and exact integer algebra to Nemo/FLINT. Its marked-vector
transport and row/column conventions are documented in
[the backend notes](julia/HassettLattices/docs/src/algorithm.md).

## 3. Exact finite root and isometry tests

### Vectors of prescribed norm

Both engines first apply an inexpensive exact root-exclusion certificate. Write
the binary Schur form as $H(y,z)=Ay^2+2Byz+Cz^2$. Then

$$H(y,z)\geq(\min(A,C)-|B|)(y^2+z^2).$$

A square-two vector would satisfy $H(y,z)=6-(h^2,r)^2\leq6$.
If $\min(A,C)-|B|>6$, no nonzero integral pair is possible; $y=z=0$
would give $3x^2=2$, also impossible. The inequality is strictly greater than
six: equality can contain roots. If this certificate does not apply, the full
exact search proceeds (Hecke in Julia, the finite coordinate search in Python).

For a positive-definite matrix $G$ and an integral vector satisfying $x^TGx=m$, Cauchy–Schwarz gives

$$|x_i|^2\leq m(G^{-1})_{ii},\qquad i=0,1,2.$$

Use $G^{-1}=\operatorname{adj}(G)/\det G$. An explicit exact bound is

$$B_i=\operatorname{isqrt}\!\left(\left\lfloor\frac{m\operatorname{adj}(G)_{ii}}{\det G}\right\rfloor\right).$$

Enumerate every integral vector in the box $-B_i\leq x_i\leq B_i$ and check the norm equation exactly. For root exclusion, set $m=2$ and search the entire lattice, not only $(h^2)^\perp$.

### Isometry fixing the distinguished class

Two surviving matrices $H,H'$ represent the same component precisely when there is an integral matrix $U$ such that

$$U^TH'U=H,\qquad Ue_0=e_0,\qquad\det U=\pm1,\qquad e_0=(1,0,0)^T.$$

Reject unequal determinants first. Write $U=(e_0,x,y)$ and enumerate vectors using the bounds above with the requirements

$$x^TH'x=H_{11},\quad e_0^TH'x=H_{01},\qquad y^TH'y=H_{22},\quad e_0^TH'y=H_{02}.$$

Then check $x^TH'y=H_{12}$ and $\det(e_0,x,y)=\pm1$. This examines every possible isometry. Equal determinants are insufficient. The isometry must fix $h^2$ but need not fix the two selected rank-two markings.

## 4. Complete procedure

The finite bound on `n` is made explicit below; all formulas refer to the preceding sections.

```text
COMPONENTS(d1, d2):
    validate distinct labels > 6, each congruent to 0 or 2 modulo 6
    compute eps1, eps2, s1, s2 and the finite tau interval
    components = []
    for tau in that interval:
        G = G_tau
        if G has an integral square-two vector: continue
        D = det(G)
        for n from 1 through isqrt(D):
            if D is not divisible by n*n: continue
            for 0 <= a,b < n with gcd(b,n) = 1:
                compute p,q,r and H
                if p,q,r are not integers: continue
                if r-p is odd: continue
                if H has an integral square-two vector: continue
                compute E and verify transpose(E) * H * E = G
                if H is h^2-isometric to an existing representative:
                    attach this origin, its inclusion, and its isometry
                else:
                    append H and its inclusion certificate
    return components
```

Keep every construction origin even when it is identified with an earlier representative. In a software implementation, express certificates in a consistently documented basis and retain the basis change to the chosen representative.

## 5. Correctness argument recorded in the PDF

The PDF invokes Yang–Yu, Lemma 4.11, Theorem 5.1, and Proposition 5.9. It states that a positive-definite integral rank-three lattice with distinguished square-three class and no square-two vector has a nonempty irreducible closed locus of codimension two and occurs as the full algebraic lattice of a cubic fourfold. The required numerical bound is automatic: $\operatorname{rk}(N)+\ell(N)\leq3+3\leq20$. Primitive-embedding uniqueness excludes additional splitting by ambient embedding class.

All parameter, extension, root, and isometry searches are finite. For a point of the intersection, the two distinct primitive markings have distinct rational spans, so their sum has rank three and one of the matrices $G_\tau$. Its saturation in the full algebraic lattice is among the extensions in Section 2, and both markings remain primitive. Conversely, every retained lattice contains the required primitive markings, so its locus lies in the intersection.

If two retained lattices described the same locus, use a point whose full algebraic lattice equals one of them. The other then embeds primitively with equal rank. A finite torsion-free quotient is zero, so this is an isometry fixing $h^2$, already removed by deduplication. Thus the resulting loci are precisely the distinct reduced irreducible components, each of dimension $18$, according to the cited geometric results.

## 6. Examples from the PDF

| Intersection | Surviving normalized parameters | Sorted component determinants | Count |
|---|---|---|---:|
| $\mathcal C_8\cap\mathcal C_{14}$ | $-2\leq\tau\leq2$ | 21, 29, 32, 36, 37 | 5 |
| $\mathcal C_8\cap\mathcal C_{26}$ | $-3\leq\tau\leq4$ | 29, 36, 48, 53, 61, 64, 68, 69 | 8 |

For these two cases, the matrix is $\left(\begin{smallmatrix}3&1&1\\1&3&\tau\\1&\tau&(d+1)/3\end{smallmatrix}\right)$ with $d=14,26$. No proper compatible extension adds a component. The PDF cites Auel–Bernardara–Bolognesi–Várilly-Alvarado, Theorem 4, and Awada, Proposition 3.2.

For $\mathcal C_{20}\cap\mathcal C_{12}$, sign reduction and the root test leave

$$G_\tau=\begin{pmatrix}3&1&0\\1&7&\tau\\0&\tau&4\end{pmatrix},\qquad0\leq\tau\leq4.$$

These starting matrices have determinants $80,77,68,53,32$. At $\tau=0$, the index-two choice $a=b=1$ yields

$$w=\frac{h^2+u+v}{2},\qquad H=\begin{pmatrix}3&1&2\\1&7&4\\2&4&4\end{pmatrix},\qquad\det H=20.$$

It contributes the sixth component, cited as Yang–Yu, Theorem 7.11. Omitting extensions would miss it.

K3 admissibility is a separate test on output lattices. It is never a condition for retaining an intersection component. The procedure provides neither a rationality verdict nor a birational parametrization.

## Implementation and references

The imported implementation is in [hassett_lattices/core.py](hassett_lattices/core.py), with its CLI in [hassett_lattices/__main__.py](hassett_lattices/__main__.py). Its presentation may normalize the input order and use equivalent bases. Consult [docs/implementation.md](docs/implementation.md) and [docs/mathematics.md](docs/mathematics.md) for those conventions.

The three references in the supplied PDF are:

1. Asher Auel, Marcello Bernardara, Michele Bolognesi, and Anthony Várilly-Alvarado, *Cubic fourfolds containing a plane and a quintic del Pezzo surface*, Algebraic Geometry **1** (2014), 181–193. [arXiv:1205.0237v4](https://arxiv.org/abs/1205.0237v4).
2. Hanine Awada, *Rational fibered cubic fourfolds*, 2024, [arXiv:1910.10182v2](https://arxiv.org/abs/1910.10182v2).
3. Song Yang and Xun Yu, *On lattice polarizable cubic fourfolds*, Research in the Mathematical Sciences **10** (2023), Article 2. [arXiv:2103.09132v1](https://arxiv.org/abs/2103.09132v1).
