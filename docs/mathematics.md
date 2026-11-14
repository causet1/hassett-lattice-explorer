---
title: "Hassett divisors: from lattices to components"
subtitle: "An exact algorithm, reproducible computations, and the K3 connection"
author: "Hassett Lattice Explorer"
date: "12 November 2026"
lang: en-US
---

# What this project computes

Given two distinct nonempty Hassett divisors, this project computes the irreducible components of their reduced set-theoretic intersection in the moduli space of smooth complex cubic fourfolds. A component is represented by a positive definite integral lattice of rank three with a distinguished element of square three. The program returns Gram matrices, discriminants, saturation certificates, and the exact K3 admissibility status of the generic algebraic lattice. It does not compute scheme-theoretic intersection multiplicities, equations for cubic fourfolds, or a birational parametrization.

The implementation is an arithmetic realization of Yang--Yu's Algorithm 7.6 [YY]. Its two essential features are exhaustive enumeration of allowable overlattices and identification up to integral isometry preserving the distinguished class. Counting positive definite Gram matrices alone does not solve the problem.

Everything in the arithmetic engine uses integers. There is no floating-point positivity test, numerical lattice reduction, random search, external algebra system, or database of component answers. The published answers are used only in the regression tests. A computation that exceeds its configured resource budget raises an error rather than reporting a partial list as complete.

## The geometric input

Let $X\subset\mathbb P^5_{\mathbb C}$ be a smooth cubic fourfold. Write

$$A(X)=H^4(X,\mathbb Z)\cap H^{2,2}(X),\qquad o=h^2.$$

The intersection form on $A(X)$ is positive definite, and $o^2=3$. The element $o$ is distinguished: its orthogonal complement in $A(X)$ is even. In the bases used here, this condition is equivalent to

$$v^2\equiv(o,v)\pmod2\quad\text{for every }v\in A(X).$$

Indeed, if $o^\perp$ is even, then $3v-(o,v)o\in o^\perp$ has square congruent to $v^2-(o,v)$ modulo two. The converse is immediate by taking $(o,v)=0$. Consequently, the condition can be tested on a basis using the diagonal of a Gram matrix.

A discriminant-$d$ label is a primitive rank-two sublattice $K_d\subset A(X)$ containing $o$, with determinant $d$. Here primitive means that the quotient by $K_d$ has no torsion. This is a condition on the integral lattice, not just on its rational span.

Hassett's nonemptiness theorem gives precisely the labels

$$d>6,\qquad d\equiv0,2\pmod6.$$

For such a label, the corresponding divisor $\mathcal C_d$ is irreducible [H, Theorem 1.0.1]. Its dimension is 19 inside the 20-dimensional moduli space. At a very general point of a component of the intersection of two distinct divisors, $A(X)$ has rank three. Higher-rank algebraic lattices occur on further special subloci.

## Why two labels give a rank-three problem

The two labels share $o$. Their rational spans cannot coincide: if two primitive rank-two sublattices of the same ambient lattice have the same rational span, both equal the intersection of that span with the ambient lattice, hence are equal and have the same discriminant. Distinct discriminants therefore give a rank-three sum.

One must then saturate that sum in $A(X)$. The saturation can be strictly larger, without changing rank. This is why component discriminants need not be the determinants of the first matrices one writes down.

The geometric theorem needed to turn this finite lattice search into a component computation is Yang--Yu's nonemptiness and irreducibility theorem [YY, Theorem 1.1 / 5.1]. A positive definite lattice with a distinguished square-three element, no vector of square two, and rank plus discriminant-group length at most 20 defines a nonempty irreducible locus. For rank three, the last inequality is automatic, since the discriminant group needs at most three generators. The locus has codimension two. Their Proposition 7.3 and Corollary 7.5 identify the intersection components in this way.

# Normalized Gram matrices

For each label $d_i$, put

$$\epsilon_i=\begin{cases}0&d_i\equiv0\pmod6,\\1&d_i\equiv2\pmod6,\end{cases}
\qquad a_i=\frac{d_i+\epsilon_i^2}{3}.$$

The two rank-two lattices can be written in bases $(o,u_i)$ with Gram matrices

$$\begin{pmatrix}3&\epsilon_i\\\epsilon_i&a_i\end{pmatrix}.$$

Thus their sum has a basis $(o,u_1,u_2)$ with matrix

$$G_t=\begin{pmatrix}
3&\epsilon_1&\epsilon_2\\
\epsilon_1&a_1&t\\
\epsilon_2&t&a_2
\end{pmatrix},\qquad t\in\mathbb Z.$$

The unknown pairing $t=(u_1,u_2)$ records how the two labels sit together. Expanding the determinant gives a useful exact search bound:

$$\Delta_t=\det G_t
=\frac{d_1d_2-(3t-\epsilon_1\epsilon_2)^2}{3}.$$

The leading minors are $3$ and $d_1$, both positive. Sylvester's criterion therefore reduces positivity to $\Delta_t>0$, or

$$|3t-\epsilon_1\epsilon_2|<\sqrt{d_1d_2}.$$

The implementation derives the integer bounds with integer square roots and strict integer inequalities. If one of the $\epsilon_i$ vanishes, changing the sign of its generator changes $t$ to $-t$, so only one sign is necessary. This is a basis symmetry, not a heuristic truncation.

The code orders equal-residue discriminants increasingly. For a mixed pair, it puts the discriminant congruent to two modulo six first, so that $(\epsilon_1,\epsilon_2)=(1,0)$. Its reported $t$ and matrices use this normalized order; the original request is retained separately as `input_pair` in the JSON. In either case with a vanishing $\epsilon_i$, the search takes $t\ge0$.

## Excluding forbidden vectors exactly

For each positive definite matrix, the program searches for a vector of square two. This search is finite. If $G$ is positive definite and $v^TGv=m$, the Cauchy--Schwarz inequality in the $G$-metric gives

$$v_i^2\le m(G^{-1})_{ii}.$$

Since $G^{-1}=\operatorname{adj}(G)/\det G$, every coordinate bound can be evaluated using integer arithmetic. The engine uses a sharper two-variable version of this argument. Write $G=\left(\begin{smallmatrix}3&\mathbf p^T\\\mathbf p&B\end{smallmatrix}\right)$ and $H=3B-\mathbf p\mathbf p^T$. For $v=(x,y,z)^T$ with $v^TGv=m$ and $(o,v)=k$, one has

$$
\begin{pmatrix}y&z\end{pmatrix}H\begin{pmatrix}y\\z\end{pmatrix}=3m-k^2,
\qquad x=\frac{k-p_1y-p_2z}{3}.
$$

For square-two vectors, $k^2\le6$, so only $k=-2,-1,0,1,2$ occur. The inverse-diagonal bounds for the positive definite matrix $H$ bound $y,z$ exactly, and the displayed formula recovers $x$ subject to its integrality. This is an exhaustive search. A rejected base matrix includes an explicit square-two vector in its diagnostics.

Testing the full lattice matters. Checking only $o^\perp$ for square-two vectors can miss forbidden configurations. Also, one need not add a separate square-one test: if $v^2=1$, distinguishedness and Cauchy--Schwarz imply $(o,v)=\pm1$, and then $(o\mp v)^2=2$.

A square-two vector remains present in every overlattice. It is therefore safe to reject a base lattice before considering its saturations.

# Enumerating every saturation

Here is the finite parametrization used in the code. It is particularly simple because both rank-two labels must remain primitive.

Let $M=\langle o,u_1,u_2\rangle$ be a retained base lattice, and let $N$ be an integral overlattice of finite index $n$ in which both labels remain primitive. Since $\langle o,u_1\rangle$ is primitive in $N$, the quotient

$$N/\langle o,u_1\rangle\simeq\mathbb Z.$$

The image of $M/\langle o,u_1\rangle$ has index $n$ in this infinite cyclic group. Choosing its positive generator gives a basis $(o,u_1,w)$ of $N$ satisfying

$$w=\frac{a o+b u_1+u_2}{n}.$$

Adding integral multiples of $o$ and $u_1$ to $w$ reduces $a,b$ uniquely modulo $n$. We may therefore assume

$$0\le a,b<n.$$

In this basis, $u_2=nw-a o-bu_1$. The quotient by the second label has presentation

$$N/\langle o,u_2\rangle\simeq\mathbb Z^2/\langle(-b,n)\rangle.$$

It is torsion-free precisely when

$$\gcd(b,n)=1.$$

Finally, the determinant-index formula gives

$$\det M=n^2\det N,$$

so $n^2$ must divide $\det M$. These statements prove completeness of a finite enumeration over $n,a,b$. In particular, the quotient $N/M$ is cyclic because primitivity forces it to be cyclic; the program is not discarding possible noncyclic quotients without justification.

For each candidate, compute

$$
(o,w)=\frac{3a+\epsilon_1b+\epsilon_2}{n},\qquad
(u_1,w)=\frac{\epsilon_1a+a_1b+t}{n},
$$

$$
w^2=\frac{3a^2+a_1b^2+a_2+2\epsilon_1ab+2\epsilon_2a+2tb}{n^2}.
$$

All three quantities must be integers, and distinguishedness additionally requires

$$w^2\equiv(o,w)\pmod2.$$

The resulting matrix is again checked for square-two vectors. Positivity is inherited from the rational quadratic space of $M$.

## Checkable inclusion certificates

The inclusion $M\hookrightarrow N$ is represented by

$$E=\begin{pmatrix}1&0&-a\\0&1&-b\\0&0&n\end{pmatrix}.$$

If $G_N$ is the returned matrix of $N$, the certificate satisfies

$$E^TG_NE=G_t,\qquad |\det E|=n.$$

Both label determinants remain $d_1,d_2$. Primitivity of the first is visible from the first two basis columns; primitivity of the second is equivalent to the gcd of its two-by-two minors being one. The tests verify these identities independently for the emitted certificates.

## Why isometry deduplication is necessary

A component parametrizes cubic fourfolds, not a chosen ordered pair of labels or a chosen basis. The same rank-three lattice may arise from different values of $t$, from different saturation descriptions, or from distinct pairs of rank-two sublattices inside it.

The program consequently identifies matrices only after an exact integral isometry test preserving $o$. It seeks a unimodular matrix $P$ with

$$P^TG_2P=G_1,\qquad P(1,0,0)^T=(1,0,0)^T.$$

The remaining two columns have prescribed norms and prescribed pairings with $o$, so finite coordinate bounds again make this search exhaustive. Equality of determinants is used only as a quick necessary check; it is not treated as an isometry criterion. When several origins produce the same component, their certificates are retained in a common representative basis.

Different root-free rank-three lattices cannot give one component properly containing another via a primitive inclusion: a primitive finite-index inclusion between lattices of the same rank is an isomorphism. Thus the deduplicated list gives the maximal irreducible loci needed here.

# Worked examples and published checks

The exact regression fixtures include the two requested intersections, a nontrivial saturation example, and two additional published cases. Tables of their determinants are collected in the appendix.

## Five components of $\mathcal C_8\cap\mathcal C_{14}$

The normalized matrix is

$$G_t=\begin{pmatrix}3&1&1\\1&3&t\\1&t&5\end{pmatrix},
\qquad\det G_t=37+2t-3t^2.$$

Positivity allows $-3\le t\le3$. The end values have square-two vectors and are excluded. The five retained values are $t=-2,-1,0,1,2$, with determinants $21,32,37,36,29$, respectively. No additional admissible overlattice contributes a component.

The geometric basis in Auel--Bernardara--Bolognesi--Várilly-Alvarado [ABBVA] uses $T=o+u_2$, so their intersection parameter is $(P,T)=t+1$. Their parameter range $-1,0,1,2,3$ therefore agrees with the normalized range above. A regression test checks the Gram matrices after this basis conversion, rather than assuming that parameters used by different authors have identical meanings.

## Eight components of $\mathcal C_8\cap\mathcal C_{26}$

Now

$$G_t=\begin{pmatrix}3&1&1\\1&3&t\\1&t&9\end{pmatrix},
\qquad\det G_t=69+2t-3t^2.$$

The root-free values are $t=-3,-2,-1,0,1,2,3,4$. Awada [A, Proposition 3.2] uses the surface class $S_{26}=2o+u_2$, giving parameter $t+2$ and matrix

$$\begin{pmatrix}3&1&7\\1&3&t+2\\7&t+2&25\end{pmatrix}.$$

Its determinant is unchanged. This explains why a correct implementation using normalized bases prints different parameter values from the geometric presentation in the paper.

## The sixth component of $\mathcal C_{20}\cap\mathcal C_{12}$

Use the basis order in Yang--Yu [YY, Theorem 7.11]:

$$M_t=\begin{pmatrix}3&1&0\\1&7&t\\0&t&4\end{pmatrix}.$$

The root-free base lattices have $0\le t\le4$ and determinants $80,77,68,53,32$. At $t=0$, take

$$w=\frac{o+u_1+u_2}{2}.$$

The basis $(o,u_1,w)$ gives

$$G_N=\begin{pmatrix}3&1&2\\1&7&4\\2&4&4\end{pmatrix},\qquad\det G_N=20.$$

The inclusion has index two. Both original labels remain primitive, distinguishedness holds, and the new lattice has no square-two vector. It yields a sixth component. The alternative basis $(o,o-w,u_1)$ gives

$$\begin{pmatrix}3&1&1\\1&3&-3\\1&-3&7\end{pmatrix},$$

exactly the matrix displayed in the published theorem. This example is the regression that detects omission of saturation.

# K3 associations: what is actually being tested

For a primitive label $K_d$, Hassett's untwisted polarized K3 association asks for a polarized K3 surface $(S,L)$, $L^2=d$, and an integral Hodge isometry

$$K_d^\perp\simeq L^\perp(-1).$$

The arithmetic condition is

$$4\nmid d,\qquad9\nmid d,\qquad
p\nmid d\text{ for every odd prime }p\equiv2\pmod3.$$

Together with nonemptiness, this is the admissibility criterion for a label [H, Theorem 1.0.2 / 5.1.3]. The Tate twist in this expression changes the sign of the quadratic form.

There are three distinctions that the interface preserves. First, the component discriminant $\det A(X)$ is not a label discriminant: one must look for primitive rank-two sublattices containing $o$. Second, a nonadmissible label does not exclude other admissible labels on the same cubic. For example, a point in $\mathcal C_8\cap\mathcal C_{14}$ has the admissible label 14 even though 8 is nonadmissible. Third, a K3 surface equipped with a nonzero Brauer class, often called a twisted K3 surface, is different from the untwisted association above.

## An exact test for the entire rank-three lattice

Write the matrix of a component as

$$G=\begin{pmatrix}3&p&q\\p&r&s\\q&s&t\end{pmatrix}.$$

For a vector $v=x o+y u+z w$, the determinant of $\langle o,v\rangle$ is independent of $x$ and equals

$$f(y,z)=(3r-p^2)y^2+2(3s-pq)yz+(3t-q^2)z^2.$$

The pair spans a primitive rank-two sublattice if and only if $\gcd(y,z)=1$. Let $\lambda$ be the gcd of the three *polynomial coefficients* of $f$, including the doubled mixed coefficient, and write $f=\lambda g$.

Yang--Yu's Theorems 8.8--8.9 give an exact criterion [YY]. In the nonsplit case $\gcd(3,p,q)=1$, an admissible label exists precisely when $\lambda$ passes the prime-divisibility condition above. In the split case $\gcd(3,p,q)=3$, one additionally requires that $g$ represent $1$ modulo three. This last condition is checked on the nine pairs in $(\mathbb Z/3\mathbb Z)^2$.

The content $\lambda$ is not itself asserted to be a Hassett label. In particular, $\lambda=2$ or $6$ is allowed; imposing $\lambda>6$ would be a bug. Nor can the split congruence check be omitted. For example, $G=\operatorname{diag}(3,4,6)$ gives $f=12y^2+18z^2$, content six, and primitive form $2y^2+3z^2$, which never represents one modulo three. It is nonadmissible. In contrast, $\operatorname{diag}(3,4,10)$ gives primitive form $2y^2+5z^2$, which represents one modulo three at $(1,1)$, and is admissible.

An intersection can reveal an admissible label that neither input provides. In $\mathcal C_8\cap\mathcal C_{12}$, the normalized lattice with $t=1$ has determinant 29. The primitive vector $v=u_1+u_2$ satisfies $v^2=9$ and $(o,v)=1$, and $\langle o,v\rangle$ is primitive because $\gcd(1,1)=1$. Its discriminant is $3\cdot9-1=26$. This component therefore has an untwisted K3 association although both input labels 8 and 12 are nonadmissible. The components with $t=0,2$ instead have content four and are generically nonadmissible.

A positive result persists throughout the component: a primitive admissible label in $M$ remains primitive after a primitive inclusion $M\hookrightarrow A(X)$. A negative result concerns cubic fourfolds with $A(X)=M$, hence the very general point of that component. It must not be extended to every point: higher-rank specializations can acquire an admissible label.

# Rationality: geometric constructions and the limits of the output

The lattice calculation identifies algebraic Hodge conditions. It does not produce a birational map to projective space. The historical Hassett/Kuznetsov picture links untwisted K3 associations, geometric K3 categories, and rationality; this project does not turn that picture into an unconditional numerical equivalence.

There are concrete positive results. Pfaffian cubic fourfolds are classical rational examples in $\mathcal C_{14}$. Russo--Staglianò's constructions using congruences of five-secant conics establish rationality in the families with labels 14, 26, and 38 [RS]. These are geometric constructions in addition to lattice admissibility. Their existence explains why the requested intersections are informative test cases.

For a cubic containing a plane $P$, projection from the plane gives a quadric surface fibration over $\mathbb P^2$. The residual quadric class is $Q=o-P$. An algebraic class with odd intersection with $Q$ supplies the classical rational-section criterion, hence rationality; with smooth discriminant, the same condition is expressed by vanishing of the Clifford Brauer class on the degree-two K3 discriminant cover [A, Section 3.1].

In the normalized $\mathcal C_8\cap\mathcal C_{14}$ matrix,

$$Q\cdot o=2,\qquad Q\cdot P=-2,\qquad Q\cdot u_2=1-t.$$

Thus an odd pairing occurs exactly when $t$ is even, assuming this rank-three lattice is the full algebraic lattice. For $t=-1$, the determinant is 32 and this section criterion fails. Nevertheless, [ABBVA, Theorem A] proves that the general member of that component is pfaffian and rational, with nontrivial Clifford invariant. Failure of one rationality construction is therefore not an irrationality proof. This is a particularly concrete reason to keep Brauer, K3, and rationality indicators separate.

## The categorical bridge

The derived category has a semiorthogonal decomposition

$$D^b(X)=\langle\operatorname{Ku}(X),\mathcal O_X,\mathcal O_X(1),\mathcal O_X(2)\rangle.$$

The residual category $\operatorname{Ku}(X)$ is the Kuznetsov component. Its Serre functor is the shift by two, so it is a two-Calabi--Yau category, with the categorical structure characteristic of a K3 surface. Kuznetsov's 2010 Conjecture 1.1 proposes that $X$ is rational precisely when $\operatorname{Ku}(X)$ is equivalent to $D^b(S)$ for an untwisted K3 surface $S$ [K]. An equivalence with a twisted category $D^b(S,\alpha)$, where $\alpha\ne0$, is a different condition and does not by itself meet that conjectural criterion.

Addington--Thomas established generic agreement between Hassett's Hodge-theoretic K3 condition and the existence of an untwisted geometric K3 category [AT]. This historical result explains why the arithmetic admissibility test belongs in a discussion of rationality. The explorer computes the lattice condition; it does not construct a derived equivalence, compute the Kuznetsov component, or establish the conjectured equivalence with rationality.

## Current context, checked 12 November 2026

The older statement that no irrational smooth complex cubic fourfold is known is no longer appropriate. Katzarkov--Kontsevich--Pantev--Yu prove that a very general cubic fourfold is irrational using Hodge atoms [KKPY, current arXiv version dated 6 March 2026]. Guéré's September 2026 version proves that rationality implies an isomorphism

$$H^4(X,\mathbb Q)_{\mathrm{prim}}\simeq H^2(S,\mathbb Q)(-1)$$

for a projective K3 surface $S$ [G, Theorem 63]. This statement is explicitly about rational Hodge structures. It should not silently be substituted for an integral polarized Hassett association: the integral lattice and its pairing contain extra information. The program invokes neither result in its correctness argument, and its K3 flag is never labeled a rationality decision.

# Using and interpreting the explorer

The offline explorer displays a finite catalogue generated by the same Python engine. Selecting two divisors exposes the rank-three components, and selecting a component shows its matrix, determinant, origins, and K3 test. The candidate scan explains which pairings survive the root test and where saturation adds a component. JSON exported by the command-line tool can be loaded into the explorer for additional discriminants.

The network is an incidence schematic. Distances, angles, edge crossings, and vertex positions have no meaning in the 20-dimensional moduli space. An edge records the computed component count for a bundled pair. An unbundled pair is not asserted to have empty intersection. The display is not a projection of the period domain, and it does not display intersection multiplicities.

For computational reproducibility, retain the JSON alongside the version of the code. The matrices and inclusion certificates permit elementary independent checks; the completeness argument is the finite enumeration proved above plus the cited geometric theorem. Passing the published fixtures is a regression check, not a substitute for that argument.

# Appendix: validation targets

The table records the published component counts and the sorted discriminants of their generic rank-three algebraic lattices. The reproducible validation report in the distribution records the actual run of the implementation.

| Intersection | Components | Sorted component discriminants | Primary reference |
|:--|--:|:--|:--|
| $\mathcal C_8\cap\mathcal C_{14}$ | 5 | 21, 29, 32, 36, 37 | [ABBVA], Theorem A / 4 |
| $\mathcal C_8\cap\mathcal C_{26}$ | 8 | 29, 36, 48, 53, 61, 64, 68, 69 | [A], Proposition 3.2 |
| $\mathcal C_8\cap\mathcal C_{38}$ | 10 | 36, 45, 61, 68, 80, 85, 93, 96, 100, 101 | [A], Theorem 1.1(2) |
| $\mathcal C_{20}\cap\mathcal C_{12}$ | 6 | 20, 32, 53, 68, 77, 80 | [YY], Theorem 7.11 |
| $\mathcal C_{20}\cap\mathcal C_{38}$ | 17 | 45, 77, 92, 120, 133, 157, 168, 188, 197, 213, 220, 232, 237, 245, 248, 252, 253 | [YY], Theorem 7.9 |

The automated checks also cover input rejection, swapping the two discriminants, exact isometry, explicit root witnesses, primitive inclusion certificates, the index-two example above, and the split/nonsplit K3 criterion. A JavaScript interaction harness exercises the explorer's event logic and data handling with 55 assertions. Live-browser rendering, downloads, and clipboard behavior remain unverified.

# References

**[H]** Brendan Hassett, *Special cubic fourfolds*, Compositio Mathematica **120** (2000), 1--23. Theorems 1.0.1, 1.0.2 and 5.1.3. [doi:10.1023/A:1001706324425](https://doi.org/10.1023/A:1001706324425).

**[YY]** Song Yang and Xun Yu, *On lattice polarizable cubic fourfolds*, Research in the Mathematical Sciences **10** (2023), article 2. Algorithm 7.6; Theorems 1.1, 7.9, 7.11, 8.8 and 8.9. [arXiv:2103.09132](https://arxiv.org/abs/2103.09132), [doi:10.1007/s40687-022-00368-6](https://doi.org/10.1007/s40687-022-00368-6). Numbering follows the available arXiv version.

**[ABBVA]** Asher Auel, Marcello Bernardara, Michele Bolognesi and Anthony Várilly-Alvarado, *Cubic fourfolds containing a plane and a quintic del Pezzo surface*, Algebraic Geometry **1** (2014), 181--193. [arXiv:1205.0237v4](https://arxiv.org/abs/1205.0237v4).

**[A]** Hanine Awada, *Rational fibered cubic fourfolds*, arXiv version 2, 9 July 2024. Theorem 1.1 and Proposition 3.2. [arXiv:1910.10182v2](https://arxiv.org/abs/1910.10182v2). Earlier versions used the title *Rational fibered cubic fourfolds with nontrivial Brauer classes*.

**[RS]** Francesco Russo and Giovanni Staglianò, *Congruences of 5-secant conics and the rationality of some admissible cubic fourfolds*, Duke Mathematical Journal **168** (2019), 849--865. [arXiv:1707.00999](https://arxiv.org/abs/1707.00999), [doi:10.1215/00127094-2018-0053](https://doi.org/10.1215/00127094-2018-0053).

**[K]** Alexander Kuznetsov, *Derived categories of cubic fourfolds*, in *Cohomological and Geometric Approaches to Rationality Problems*, Progress in Mathematics **282** (2010), 219--243. Conjecture 1.1. [arXiv:0808.3351](https://arxiv.org/abs/0808.3351).

**[AT]** Nicolas Addington and Richard Thomas, *Hodge theory and derived categories of cubic fourfolds*, Duke Mathematical Journal **163** (2014), 1885--1927. [arXiv:1211.3758](https://arxiv.org/abs/1211.3758).

**[KKPY]** Ludmil Katzarkov, Maxim Kontsevich, Tony Pantev and Tony Yue Yu, *Birational invariants from Hodge structures and quantum multiplication*, version 2, 6 March 2026. [arXiv:2508.05105v2](https://arxiv.org/abs/2508.05105v2).

**[G]** Jérémy Guéré, *On the irrationality of cubic fourfolds*, version 2, 4 September 2026. Theorem 63. [arXiv:2603.04518v2](https://arxiv.org/abs/2603.04518v2).

**Authorship and provenance.** This software and explanatory text were developed with AI assistance. The mathematical algorithm and geometric theorems are credited to the authors above. The implementation, saturation parametrization proof, certificates, and tests should be reviewed as research software; the project is not a formal proof assistant verification.
