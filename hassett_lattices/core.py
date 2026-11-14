"""Finite, exact implementation of Yang--Yu Algorithm 7.6.

No floating-point decision enters the algorithm. The only floating-point value
returned is elapsed wall-clock time. Rank-two markings are required primitive;
their sum is not assumed saturated. Isometry means isometry preserving h^2.

Completeness of the overlattice enumeration:
  Write M = Z h + Z u + Z v. If K1 = Z h + Z u is primitive in an
  overlattice N, then N/K1 is infinite cyclic. If [N:M]=n, N has a basis
  (h,u,w) with w=(a*h+b*u+v)/n, 0 <= a,b < n. The second marking
  K2 = Z h + Z v is primitive precisely when gcd(b,n)=1. Hence every
  admissible overlattice occurs in the finite search below; n^2 divides det M.

The test h characteristic, G[i][i] == G[0][i] modulo 2, is equivalent
to the evenness of h-perp when h^2=3 (Yang--Yu Lemma 4.4).
"""

from dataclasses import dataclass
from math import gcd, isqrt
from time import monotonic


class ResourceLimitError(RuntimeError):
    """A resource limit was reached; no partial list is a complete answer."""


@dataclass(frozen=True)
class Limits:
    """Explicit resource limits. Use None for either unlimited resource.

    max_work counts iterations in all potentially long finite searches, not CPU
    instructions. A result is returned only after the entire search finishes.
    """

    max_work: int | None = 5_000_000
    timeout_seconds: float | None = 60.0

    def __post_init__(self):
        if self.max_work is not None and (
            isinstance(self.max_work, bool)
            or not isinstance(self.max_work, int)
            or self.max_work < 1
        ):
            raise ValueError("max_work must be a positive integer or None")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive or None")


class _Budget:
    def __init__(self, limits):
        self.limits = limits
        self.started = monotonic()
        self.work = 0

    def tick(self, n=1):
        self.work += n
        if self.limits.max_work is not None and self.work > self.limits.max_work:
            raise ResourceLimitError(
                f"Work limit ({self.limits.max_work}) reached; no complete result was produced. "
                "Increase Limits.max_work or use None."
            )
        if (self.work & 255) == 0:
            self.check_time()

    def check_time(self):
        limit = self.limits.timeout_seconds
        if limit is not None and monotonic() - self.started > limit:
            raise ResourceLimitError(
                f"Time limit ({limit} seconds) reached; no complete result was produced. "
                "Increase Limits.timeout_seconds or use None."
            )


def valid_discriminant(d):
    """Whether C_d is a nonempty Hassett divisor."""
    return isinstance(d, int) and not isinstance(d, bool) and d > 6 and d % 6 in (0, 2)


def _factor(n, budget=None):
    """Trial division is exact and deliberately subject to the work budget."""
    factors = []
    p = 2
    while p * p <= n:
        if budget:
            budget.tick()
        if n % p == 0:
            e = 0
            while n % p == 0:
                n //= p
                e += 1
            factors.append((p, e))
        p = 3 if p == 2 else p + 2
    if n > 1:
        factors.append((n, 1))
    return factors


def _arithmetic_obstructions(d, budget=None):
    """Condition (**) alone, also applicable to the content lambda=2 or 6."""
    out = []
    if d % 4 == 0:
        out.append("divisible by 4")
    if d % 9 == 0:
        out.append("divisible by 9")
    for p, _ in _factor(d, budget):
        if p != 2 and p % 3 == 2:
            out.append(f"divisible by the odd prime {p}, congruent to 2 modulo 3")
    return out


def admissible_discriminant(d):
    """Hassett's untwisted-K3 condition, including the divisor condition (*)."""
    return valid_discriminant(d) and not _arithmetic_obstructions(d)


def determinant(g):
    """Exact determinant of a 3 by 3 matrix."""
    return (
        g[0][0] * (g[1][1] * g[2][2] - g[1][2] * g[2][1])
        - g[0][1] * (g[1][0] * g[2][2] - g[1][2] * g[2][0])
        + g[0][2] * (g[1][0] * g[2][1] - g[1][1] * g[2][0])
    )


def _validate_gram(g):
    if len(g) != 3 or any(len(row) != 3 for row in g):
        raise ValueError("Expected a 3 by 3 Gram matrix")
    if any(not isinstance(x, int) or isinstance(x, bool) for row in g for x in row):
        raise ValueError("Gram entries must be integers")
    if any(g[i][j] != g[j][i] for i in range(3) for j in range(3)):
        raise ValueError("Gram matrix must be symmetric")
    if g[0][0] != 3:
        raise ValueError("The first basis vector must be h^2, of square 3")
    if 3 * g[1][1] - g[0][1] ** 2 <= 0 or determinant(g) <= 0:
        raise ValueError("Gram matrix must be positive definite")


def _schur(g):
    p, q = g[0][1], g[0][2]
    return 3 * g[1][1] - p * p, 3 * g[1][2] - p * q, 3 * g[2][2] - q * q


def _vectors_with_norm_pairing(g, norm, pairing, budget):
    """Enumerate EVERY vector x with x^2=norm and h.x=pairing.

    Set H=3*B-p*p^t (the binary Schur form). For x=(x0,y,z),
      H(y,z)=3*norm-pairing^2, x0=(pairing-p1*y-p2*z)/3.
    Cauchy--Schwarz bounds one coordinate; an exact discriminant square test
    solves the quadratic in the other. Sort in the historical (y,z) order so
    root and isometry certificates remain byte-for-byte reproducible.
    """
    a, b, c = _schur(g)
    target = 3 * norm - pairing * pairing
    if target < 0:
        return
    delta = a * c - b * b
    # Tiny boxes are cheaper than discriminant tests plus sorting. Keep the
    # same exact search, with this measured constant-factor fast path.
    ymax = isqrt(target * c // delta)
    zmax = isqrt(target * a // delta)
    p, q = g[0][1], g[0][2]
    if (2 * ymax + 1) * (2 * zmax + 1) <= 25:
        for y in range(-ymax, ymax + 1):
            for z in range(-zmax, zmax + 1):
                budget.tick()
                if a * y * y + 2 * b * y * z + c * z * z == target:
                    xnum = pairing - p * y - q * z
                    if xnum % 3 == 0:
                        yield (xnum // 3, y, z)
        return
    swapped = a > c
    if swapped:
        a, c = c, a
        zmax = ymax
    found = []
    for z in range(-zmax, zmax + 1):
        budget.tick()
        square = a * target - delta * z * z
        root = isqrt(square)
        if root * root != square:
            continue
        for k in ((root,) if root == 0 else (-root, root)):
            numerator = k - b * z
            if numerator % a:
                continue
            y = numerator // a
            yy, zz = (z, y) if swapped else (y, z)
            xnum = pairing - p * yy - q * zz
            if xnum % 3 == 0:
                found.append((xnum // 3, yy, zz))
    yield from sorted(found, key=lambda v: (v[1], v[2]))


def _root(g, budget):
    budget.tick()
    a, b, c = _schur(g)
    # H(y,z) >= (min(a,c)-abs(b))*(y*y+z*z). A norm-two
    # vector requires H(y,z)=6-(h.r)^2 <= 6; y=z=0 cannot work.
    if min(a, c) - abs(b) > 6:
        return None
    # |h.r|^2 <= h^2*r^2 = 6, so the five pairings suffice.
    for pairing in range(-2, 3):
        for v in _vectors_with_norm_pairing(g, 2, pairing, budget):
            return list(v)
    return None


def norm_two_vector(g, limits=Limits()):
    """Return a norm-2 witness, or None after an exhaustive exact search."""
    _validate_gram(g)
    budget = _Budget(limits)
    result = _root(g, budget)
    budget.check_time()
    return result


def _bilinear(g, v, w):
    return sum(v[i] * g[i][j] * w[j] for i in range(3) for j in range(3))


def _matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


_IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def _isometry(source, target, budget):
    """U with U^t target U=source, U*e0=e0, det U=+-1, or None."""
    if determinant(source) != determinant(target):
        return None
    if source == target:
        return [row[:] for row in _IDENTITY]
    first = list(_vectors_with_norm_pairing(target, source[1][1], source[0][1], budget))
    second = list(_vectors_with_norm_pairing(target, source[2][2], source[0][2], budget))
    for u in first:
        for v in second:
            budget.tick()
            if abs(u[1] * v[2] - u[2] * v[1]) != 1:
                continue
            if _bilinear(target, u, v) != source[1][2]:
                continue
            return [[1, u[0], v[0]], [0, u[1], v[1]], [0, u[2], v[2]]]
    return None


def h_fixed_isometry(source, target, limits=Limits()):
    """Find a certified integral isometry preserving the first basis vector.

    Returns U satisfying U.T * target * U == source and det(U) in {1,-1},
    or None after exhaustive search. Discriminant equality alone is insufficient.
    """
    _validate_gram(source)
    _validate_gram(target)
    budget = _Budget(limits)
    result = _isometry(source, target, budget)
    budget.check_time()
    return result


def _k3_association(g, budget):
    a, b, c = _schur(g)
    content = gcd(gcd(a, 2 * b), c)
    primitive = [a // content, 2 * b // content, c // content]
    split = gcd(gcd(3, g[0][1]), g[0][2]) == 3
    obstructions = _arithmetic_obstructions(content, budget)
    mod3_witness = next(
        ([y, z] for y in range(3) for z in range(3)
         if (primitive[0] * y * y + primitive[1] * y * z + primitive[2] * z * z) % 3 == 1),
        None,
    )
    if split and mod3_witness is None:
        obstructions.append("primitive discriminant form does not represent 1 modulo 3")
    return {
        "admissible": not obstructions,
        "discriminant_form": [a, 2 * b, c],
        "content": content,
        "primitive_form": primitive,
        "h_splits_orthogonally": split,
        "mod3_witness": mod3_witness,
        "obstructions": obstructions,
        "criterion": "Yang–Yu Theorem 8.9" if split else "Yang–Yu Theorem 8.8",
        "interpretation": (
            "This lattice contains an admissible primitive rank-two sublattice through h. "
            "For a cubic containing this algebraic lattice primitively, it gives an untwisted K3 association. "
            "This is not a rationality decision."
            if not obstructions else
            "This lattice contains no admissible primitive rank-two sublattice through h. "
            "A cubic with exactly this algebraic lattice has no untwisted K3 association. "
            "Special points with additional algebraic classes may have one. "
            "This is not an irrationality decision."
        ),
    }


def lattice_k3_association(g, limits=Limits()):
    """Exact lattice admissibility by Yang--Yu Theorems 8.8 and 8.9.

    Applies to a positive-definite integral rank-three lattice with distinguished
    first vector. A positive answer is Hodge-theoretic, not a rationality proof.
    """
    _validate_gram(g)
    if any((g[i][i] - g[0][i]) % 2 for i in range(3)):
        raise ValueError("The first vector must be distinguished (h-perp even)")
    budget = _Budget(limits)
    result = _k3_association(g, budget)
    budget.check_time()
    return result


def _indices(det, budget):
    values = [1]
    for p, e in _factor(det, budget):
        values = [n * p ** j for n in values for j in range(e // 2 + 1)]
    return sorted(values)


def _normalize(d1, d2):
    if not valid_discriminant(d1) or not valid_discriminant(d2):
        raise ValueError("Both discriminants must be integers > 6, congruent to 0 or 2 modulo 6")
    if d1 == d2:
        raise ValueError("Use two distinct discriminants: a self-intersection is the divisor itself")
    if d1 % 6 == d2 % 6:
        return tuple(sorted((d1, d2)))
    return (d1, d2) if d1 % 6 == 2 else (d2, d1)


def _linear_residues(coefficient, rhs, modulus):
    """All solutions of coefficient*x = rhs modulo modulus, in [0,modulus)."""
    divisor = gcd(coefficient, modulus)
    if rhs % divisor:
        return ()
    step = modulus // divisor
    start = 0 if step == 1 else (pow(coefficient // divisor, -1, step) * (rhs // divisor)) % step
    return range(start, modulus, step)


def _saturation_residues(d1, p, q, aa, tau, n, budget):
    """Solve the two linear integrality conditions before testing the norm.

    Elimination gives d1*b = p*q - 3*tau (mod n). For each solution b,
    solve 3*a = -p*b-q (mod n) and recheck the second original equation
    (essential when 3 divides n). Sorting preserves historical origin order.
    """
    residues = []
    for b in _linear_residues(d1, p*q - 3*tau, n):
        budget.tick()
        if gcd(b, n) != 1:
            continue
        for a in _linear_residues(3, -p*b-q, n):
            budget.tick()
            if (p*a + aa*b + tau) % n == 0:
                residues.append((a, b))
    return sorted(residues)


def intersection_components(d1, d2, *, limits=Limits()):
    """Compute all reduced irreducible components of C_d1 intersect C_d2.

    Returns a JSON-serializable certificate dictionary with ``complete=True``.
    Invalid inputs and resource exhaustion raise exceptions; an incomplete list
    is never returned as an answer. Components have generic algebraic rank three
    and codimension two in cubic-fourfold moduli. Scheme multiplicities are not
    computed. The input is normalized to the three cases of Algorithm 7.6.
    """
    input_pair = [d1, d2]
    d1, d2 = _normalize(d1, d2)
    budget = _Budget(limits)
    p, q = int(d1 % 6 == 2), int(d2 % 6 == 2)
    aa, bb = (d1 + p) // 3, (d2 + q) // 3
    # det M = (d1*d2 - (3*tau-p*q)^2)/3; strict inequality is exact.
    radius = isqrt(d1 * d2 - 1)
    lower = -(-(p * q - radius) // 3)
    upper = (p * q + radius) // 3
    if p * q == 0:
        lower = max(0, lower)
    candidates, bases, components = [], [], []
    determinant_buckets = {}
    counts = {
        "overlattice_parameter_candidates": 0,
        "integral_overlattices": 0,
        "rejected_parity": 0,
        "rejected_roots": 0,
        "accepted_marked_lattices": 0,
        "duplicate_count": 0,
    }

    def accept(g, base, tau, n, a, b):
        counts["accepted_marked_lattices"] += 1
        det = determinant(g)
        bucket = determinant_buckets.setdefault(det, [])
        embed = [[1, 0, -a], [0, 1, -b], [0, 0, n]]
        origin = {
            "tau": tau, "index": n, "a": a, "b": b,
            "base_gram": base,
            "overlattice_gram": g,
            "embedding": embed,
            "basis_map_to_representative": [row[:] for row in _IDENTITY],
        }
        for component in bucket:
            budget.tick()
            change = _isometry(g, component["gram"], budget)
            if change is not None:
                origin["basis_map_to_representative"] = change
                origin["embedding"] = _matmul(change, embed)
                component["origins"].append(origin)
                counts["duplicate_count"] += 1
                return
        component = {
            "id": f"{d1}-{d2}-c{len(components) + 1:02d}",
            "gram": g,
            "determinant": det,
            "rank": 3,
            "h": [1, 0, 0],
            "tau": tau,
            "index": n,
            "origins": [origin],
            "k3_association": _k3_association(g, budget),
        }
        components.append(component)
        bucket.append(component)

    for tau in range(lower, upper + 1):
        budget.tick()
        g = [[3, p, q], [p, aa, tau], [q, tau, bb]]
        det = determinant(g)
        if det <= 0:
            raise AssertionError("Internal positivity interval failure")
        root = _root(g, budget)
        record = {
            "tau": tau, "gram": g, "determinant": det,
            "root_free": root is None, "root_witness": root,
            "accepted_overlattices": 0,
        }
        candidates.append(record)
        if root is None:
            bases.append(record)
            accept(g, g, tau, 1, 0, 0)

    for record in bases:
        base, tau, det = record["gram"], record["tau"], record["determinant"]
        for n in _indices(det, budget):
            if n == 1:
                continue
            for a, b in _saturation_residues(d1, p, q, aa, tau, n, budget):
                budget.tick()
                counts["overlattice_parameter_candidates"] += 1
                hn = 3 * a + p * b + q
                un = p * a + aa * b + tau
                wn = 3 * a * a + aa * b * b + bb + 2 * p * a * b + 2 * q * a + 2 * tau * b
                if wn % (n * n):
                    continue
                hp, up, wp = hn // n, un // n, wn // (n * n)
                g = [[3, p, hp], [p, aa, up], [hp, up, wp]]
                counts["integral_overlattices"] += 1
                if (wp - hp) % 2:
                    counts["rejected_parity"] += 1
                    continue
                if _root(g, budget) is not None:
                    counts["rejected_roots"] += 1
                    continue
                if determinant(g) * n * n != det:
                    raise AssertionError("Internal index/discriminant identity failure")
                record["accepted_overlattices"] += 1
                accept(g, base, tau, n, a, b)

    budget.check_time()
    counts.update({
        "positive_definite_taus": [r["tau"] for r in candidates],
        "root_free_taus": [r["tau"] for r in bases],
        "work_units": budget.work,
        "elapsed_seconds": round(monotonic() - budget.started, 6),
    })
    return {
        "schema_version": "1.0",
        "algorithm": "Yang–Yu Algorithm 7.6",
        "reference": "https://arxiv.org/abs/2103.09132",
        "input_pair": input_pair,
        "d1": d1, "d2": d2,
        "complete": True,
        "component_count": len(components),
        "components": components,
        "candidates": candidates,
        "diagnostics": counts,
        "scope": "Reduced irreducible components; scheme-theoretic multiplicities are not computed.",
    }
