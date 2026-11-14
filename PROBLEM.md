# Problem description and expected outcome

This brief records the problem supplied in [the original screenshot](references/problem-statement.png). The repository is private, as requested. The screenshot's aspiration to an open-source implementation is retained as a project objective; it does not authorize making this repository public. The imported implementation already carries its original MIT license.

## Area and background

Algebraic geometry: Hodge theory and lattice theory, cubic fourfolds, and K3 surfaces.

A smooth complex cubic fourfold is special when it contains an algebraic surface whose class is not homologous to a complete intersection. Such fourfolds lie on a countable collection of Hassett divisors $\mathcal C_d$ in the moduli space of smooth cubic fourfolds. The nonempty divisors have labels

$$d>6,\qquad d\equiv0\text{ or }2\pmod6.$$

For a valid label, Hassett's arithmetic condition for an associated polarized K3 surface is that $d$ is not divisible by $4$, by $9$, or by any odd prime congruent to $2$ modulo $3$. This is a condition on the labeled Hodge-theoretic association. It is separate from deciding the irreducible components of an intersection and from deciding rationality.

Intersections of Hassett divisors are governed by embeddings and saturations of integral lattices containing the distinguished class $h^2$, whose square is $3$. The problem is to make this lattice description explicit and computationally reproducible, and explain its relationship with K3 associations and rationality questions.

## Computational problem

For two distinct valid labels $d_1,d_2$, determine the reduced irreducible components of

$$\mathcal C_{d_1}\cap\mathcal C_{d_2}.$$

Return a rank-three integral Gram matrix for each component, with $h^2$ as its first basis vector, together with its determinant, construction parameters, finite-index inclusion certificates, and any isometries used to merge duplicate presentations.

The computation must include all compatible finite-index extensions of the sum of the two markings. It must preserve primitivity of both rank-two markings, test for square-two vectors in the whole lattice, and identify lattices by integral isometries fixing $h^2$. Equal determinants alone do not establish isometry.

The supplied procedure is documented in [ALGORITHM.md](ALGORITHM.md), with the unchanged [source PDF](references/hassett-intersection-algorithm.pdf) retained for comparison.

## Expected outcome

1. **Reproducible implementation.** An exact implementation of the intersection algorithm, with explicit finite search bounds, useful certificates, and a clear distinction between completed computations and interrupted searches.
2. **Published regression cases.** Recover five components for $\mathcal C_8\cap\mathcal C_{14}$ and eight for $\mathcal C_8\cap\mathcal C_{26}$. Check the component determinants and lattice certificates as well as the counts. The six-component case $\mathcal C_{20}\cap\mathcal C_{12}$ must include the index-two extension that is missed by an unsaturated search.
3. **Interactive visualization.** Let users explore divisor labels, intersections, Gram matrices, and saturation data. Distinguish a schematic incidence graph from actual coordinates in moduli, and uncomputed inputs from empty intersections.
4. **Written explanation.** Connect the lattice computation to K3 associations and rationality questions while making clear what is a theorem, a computed result, or an interpretation. K3 admissibility must not be used to discard intersection components or presented as an automatic rationality verdict.

The existing [Hassett Lattice Explorer website](https://hassett-lattice-explorer.causetpatrick.chatgpt.site) and its source are included in this repository; see [WEBSITE.md](WEBSITE.md) for the source snapshot and data scope. These are existing project materials, not a claim of a new theorem or a fresh independent proof of every mathematical assertion.

## Scope boundaries

The algorithm computes reduced components, not intersection multiplicities, defining equations, rational parametrizations, or a general rationality decision. For equal labels, the reduced self-intersection is the divisor itself; the rank-three implementation rejects that input explicitly.

## Reference material

- Brendan Hassett, *Special cubic fourfolds*, Compositio Mathematica **120** (2000), 1–23. See Theorem 1.0.1 and Section 5. [DOI](https://doi.org/10.1023/A:1001706324425).
- Song Yang and Xun Yu, *On lattice polarizable cubic fourfolds*, Research in the Mathematical Sciences **10** (2023), Article 2. The problem and supplied note use the numbering of [arXiv:2103.09132v1](https://arxiv.org/abs/2103.09132v1): Algorithm 7.6, Theorem 7.9, and Theorem 7.11.
- Steven Zucker, *The Hodge conjecture for cubic fourfolds*, Compositio Mathematica **34** (1977), 199–209, Theorem 3.2, as cited in the supplied problem screenshot.
- Auel, Bernardara, Bolognesi, and Várilly-Alvarado, *Cubic fourfolds containing a plane and a quintic del Pezzo surface*, Algebraic Geometry **1** (2014), 181–193, Theorem 4. [arXiv:1205.0237v4](https://arxiv.org/abs/1205.0237v4).
- Hanine Awada, *Rational fibered cubic fourfolds*, [arXiv:1910.10182v2](https://arxiv.org/abs/1910.10182v2), Proposition 3.2.
