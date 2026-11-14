#!/usr/bin/env python3
"""Independently check exported lattice certificates, not enumeration completeness.

Uses only Python's standard library and does not import hassett_lattices.
The root test uses inverse-diagonal three-dimensional boxes, independently of
the engine's binary Schur-form implementation.
"""

import argparse
import json
from math import gcd, isqrt
from pathlib import Path
import sys


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def integer(x):
    return isinstance(x, int) and not isinstance(x, bool)


def matrix(value, name):
    require(isinstance(value, list) and len(value) == 3, f"{name}: expected three rows")
    require(all(isinstance(row, list) and len(row) == 3 for row in value), f"{name}: expected a 3 by 3 matrix")
    require(all(integer(x) for row in value for x in row), f"{name}: entries must be integers")
    return value


def det(a):
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def transpose(a):
    return [list(row) for row in zip(*a)]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def congruence(g, e):
    return mul(mul(transpose(e), g), e)


def pairing(g, v, w):
    return sum(v[i] * g[i][j] * w[j] for i in range(3) for j in range(3))


def first_column(a):
    return [a[i][0] for i in range(3)]


def gram(value, name):
    g = matrix(value, name)
    require(all(g[i][j] == g[j][i] for i in range(3) for j in range(3)), f"{name}: matrix is not symmetric")
    require(g[0][0] == 3, f"{name}: h must have square 3")
    require(3 * g[1][1] - g[0][1] ** 2 > 0 and det(g) > 0, f"{name}: matrix is not positive definite")
    require(all((g[i][i] - g[0][i]) % 2 == 0 for i in range(3)), f"{name}: h is not distinguished")
    return g


def primitive_pair(e, j):
    minors = [e[r][0] * e[s][j] - e[s][0] * e[r][j] for r, s in ((0, 1), (0, 2), (1, 2))]
    return gcd(gcd(*minors[:2]), minors[2]) == 1


def label_discriminant(g, e, j):
    h, v = [row[0] for row in e], [row[j] for row in e]
    return pairing(g, h, h) * pairing(g, v, v) - pairing(g, h, v) ** 2


class RootVerifier:
    def __init__(self, max_vectors):
        self.max_vectors = max_vectors
        self.vectors = 0
        self.cache = {}

    def find_root(self, g):
        key = tuple(tuple(row) for row in g)
        if key in self.cache:
            return self.cache[key]
        determinant = det(g)
        cofactors = [
            g[1][1] * g[2][2] - g[1][2] ** 2,
            g[0][0] * g[2][2] - g[0][2] ** 2,
            g[0][0] * g[1][1] - g[0][1] ** 2,
        ]
        bounds = [isqrt(2 * c // determinant) for c in cofactors]
        for x in range(-bounds[0], bounds[0] + 1):
            for y in range(-bounds[1], bounds[1] + 1):
                for z in range(-bounds[2], bounds[2] + 1):
                    self.vectors += 1
                    if self.max_vectors is not None and self.vectors > self.max_vectors:
                        raise VerificationError(
                            f"Root-verification budget ({self.max_vectors} vectors) exhausted; "
                            "verification is incomplete. Increase --max-vectors or use --no-limits."
                        )
                    v = [x, y, z]
                    if pairing(g, v, v) == 2:
                        self.cache[key] = v
                        return v
        self.cache[key] = None
        return None

    def check_root_free(self, g, context):
        root = self.find_root(g)
        require(root is None, f"{context}: alleged root-free lattice contains root {root}")


def has_arithmetic_obstruction(n):
    if n % 4 == 0 or n % 9 == 0:
        return True
    p = 2
    while p * p <= n:
        if n % p == 0:
            if p != 2 and p % 3 == 2:
                return True
            while n % p == 0:
                n //= p
        p = 3 if p == 2 else p + 2
    return n > 1 and n != 2 and n % 3 == 2


def check_k3(g, report, context):
    require(isinstance(report, dict), f"{context}: missing K3 report")
    p, q = g[0][1], g[0][2]
    form = [3 * g[1][1] - p * p, 6 * g[1][2] - 2 * p * q, 3 * g[2][2] - q * q]
    content = gcd(gcd(form[0], form[1]), form[2])
    primitive = [a // content for a in form]
    split = p % 3 == 0 and q % 3 == 0
    mod3 = any((primitive[0] * y * y + primitive[1] * y * z + primitive[2] * z * z) % 3 == 1 for y in range(3) for z in range(3))
    expected = not has_arithmetic_obstruction(content) and (not split or mod3)
    require(report.get("discriminant_form") == form, f"{context}: incorrect discriminant form")
    require(report.get("content") == content, f"{context}: incorrect form content")
    require(report.get("primitive_form") == primitive, f"{context}: incorrect primitive form")
    require(report.get("h_splits_orthogonally") is split, f"{context}: incorrect orthogonal-splitting flag")
    require(report.get("admissible") is expected, f"{context}: incorrect lattice K3 decision")
    witness = report.get("mod3_witness")
    if witness is not None:
        require(isinstance(witness, list) and len(witness) == 2 and all(integer(x) for x in witness), f"{context}: invalid mod-3 witness")
        y, z = witness
        require((primitive[0] * y * y + primitive[1] * y * z + primitive[2] * z * z) % 3 == 1, f"{context}: false mod-3 witness")
    else:
        require(not mod3, f"{context}: a mod-3 witness is missing")


def verify_result(result, roots):
    require(isinstance(result, dict), "Result must be a JSON object")
    require(result.get("schema_version") == "1.0", "Unsupported or missing schema_version")
    require(result.get("complete") is True, "The supplied record does not claim a completed computation")
    d1, d2 = result.get("d1"), result.get("d2")
    require(all(integer(d) and d > 6 and d % 6 in (0, 2) for d in (d1, d2)), "Invalid Hassett discriminants")
    require(d1 != d2, "The discriminants must be distinct")
    require(d1 % 6 == 2 if d1 % 6 != d2 % 6 else d1 < d2, "Discriminants are not normalized")
    require(sorted(result.get("input_pair", [])) == sorted([d1, d2]), "input_pair disagrees with the normalized pair")
    p, q = int(d1 % 6 == 2), int(d2 % 6 == 2)
    a1, a2 = (d1 + p) // 3, (d2 + q) // 3
    prefix = f"C_{d1} ∩ C_{d2}"
    candidates = result.get("candidates")
    require(isinstance(candidates, list), f"{prefix}: candidates must be a list")
    by_tau = {}
    for candidate in candidates:
        require(isinstance(candidate, dict), f"{prefix}: invalid candidate")
        tau = candidate.get("tau")
        require(integer(tau) and tau not in by_tau, f"{prefix}: repeated or invalid candidate tau")
        require(p * q != 0 or tau >= 0, f"{prefix}: negative tau in a sign-normalized case")
        g = gram(candidate.get("gram"), f"{prefix}, candidate {tau}")
        require(g == [[3, p, q], [p, a1, tau], [q, tau, a2]], f"{prefix}: incorrect starting Gram matrix")
        require(candidate.get("determinant") == det(g), f"{prefix}: incorrect candidate determinant")
        require(isinstance(candidate.get("root_free"), bool), f"{prefix}: root_free must be a Boolean")
        witness = candidate.get("root_witness")
        if candidate["root_free"]:
            require(witness is None, f"{prefix}: root-free candidate also has a root witness")
            roots.check_root_free(g, f"{prefix}, candidate {tau}")
        else:
            require(isinstance(witness, list) and len(witness) == 3 and all(integer(x) for x in witness), f"{prefix}: rejected candidate lacks an integral root witness")
            require(pairing(g, witness, witness) == 2, f"{prefix}: false root witness")
        by_tau[tau] = candidate

    components = result.get("components")
    require(isinstance(components, list) and components, f"{prefix}: missing components")
    require(result.get("component_count") == len(components), f"{prefix}: incorrect component_count")
    ids, origin_count = set(), 0
    accepted_overlattices = {tau: 0 for tau in by_tau}
    for number, component in enumerate(components, 1):
        require(isinstance(component, dict), f"{prefix}: component must be an object")
        identifier = component.get("id")
        require(isinstance(identifier, str) and identifier not in ids, f"{prefix}: missing or repeated component id")
        ids.add(identifier)
        context = f"{prefix}, component {number}"
        g = gram(component.get("gram"), context)
        require(component.get("determinant") == det(g), f"{context}: incorrect determinant")
        require(component.get("rank") == 3 and component.get("h") == [1, 0, 0], f"{context}: invalid rank or distinguished vector")
        roots.check_root_free(g, context)
        check_k3(g, component.get("k3_association"), context)
        origins = component.get("origins")
        require(isinstance(origins, list) and origins, f"{context}: missing construction origins")
        require(component.get("tau") == origins[0].get("tau") and component.get("index") == origins[0].get("index"), f"{context}: displayed origin disagrees with the first origin")
        for origin in origins:
            require(isinstance(origin, dict), f"{context}: invalid construction origin")
            origin_count += 1
            n, a, b, tau = (origin.get(k) for k in ("index", "a", "b", "tau"))
            require(all(integer(x) for x in (n, a, b, tau)) and n > 0, f"{context}: invalid construction parameters")
            require(0 <= a < n and 0 <= b < n and gcd(b, n) == 1, f"{context}: residue/primitivity condition failed")
            require(tau in by_tau and by_tau[tau]["root_free"], f"{context}: origin is absent from retained starting candidates")
            base = gram(origin.get("base_gram"), context + " base")
            origin_g = gram(origin.get("overlattice_gram"), context + " origin")
            require(base == by_tau[tau]["gram"], f"{context}: origin base disagrees with its candidate")
            s = matrix(origin.get("basis_map_to_representative"), context + " basis map")
            e = matrix(origin.get("embedding"), context + " embedding")
            e0 = [[1, 0, -a], [0, 1, -b], [0, 0, n]]
            require(abs(det(s)) == 1 and first_column(s) == [1, 0, 0], f"{context}: basis map is not a unimodular h-fixed map")
            require(congruence(g, s) == origin_g, f"{context}: basis-map Gram identity failed")
            require(congruence(origin_g, e0) == base, f"{context}: cyclic-overlattice construction identity failed")
            require(e == mul(s, e0), f"{context}: embedding does not equal S E0")
            require(congruence(g, e) == base, f"{context}: embedding Gram identity failed")
            require(abs(det(e)) == n and first_column(e) == [1, 0, 0], f"{context}: incorrect embedding index or h image")
            require(det(g) * n * n == det(base), f"{context}: index/discriminant identity failed")
            for j, d in ((1, d1), (2, d2)):
                require(primitive_pair(e, j), f"{context}: marking {j} is not primitive")
                require(label_discriminant(g, e, j) == d, f"{context}: marking {j} has the wrong discriminant")
            if n > 1:
                accepted_overlattices[tau] += 1

    for tau, candidate in by_tau.items():
        require(candidate.get("accepted_overlattices") == accepted_overlattices[tau], f"{prefix}: accepted-overlattice count disagrees with stored origins")
    diagnostics = result.get("diagnostics")
    require(isinstance(diagnostics, dict), f"{prefix}: missing diagnostics")
    require(diagnostics.get("accepted_marked_lattices") == origin_count, f"{prefix}: incorrect marked-lattice count")
    require(diagnostics.get("duplicate_count") == origin_count - len(components), f"{prefix}: incorrect duplicate count")
    require(diagnostics.get("positive_definite_taus") == list(by_tau), f"{prefix}: incorrect candidate parameter diagnostic")
    require(diagnostics.get("root_free_taus") == [t for t, c in by_tau.items() if c["root_free"]], f"{prefix}: incorrect root-free parameter diagnostic")
    return {"pair": [d1, d2], "components_checked": len(components), "origins_checked": origin_count}


def unpack(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("pairs"), list):
            return data["pairs"]
        if isinstance(data.get("results"), list):
            return data["results"]
        return [data]
    raise VerificationError("Expected a result, result list, or catalogue object")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--max-vectors", type=int, default=2_000_000, help="global budget for independent root-box checks")
    parser.add_argument("--no-limits", action="store_true")
    args = parser.parse_args(argv)
    if args.max_vectors < 1:
        parser.error("--max-vectors must be positive")
    roots = RootVerifier(None if args.no_limits else args.max_vectors)
    total_pairs = total_components = total_origins = 0
    try:
        for path in args.files:
            records = unpack(json.loads(path.read_text(encoding="utf-8")))
            require(records, f"{path}: no result records")
            checks = [verify_result(record, roots) for record in records]
            count_components = sum(c["components_checked"] for c in checks)
            count_origins = sum(c["origins_checked"] for c in checks)
            total_pairs += len(checks)
            total_components += count_components
            total_origins += count_origins
            print(f"PASS {path}: {len(checks)} pair(s), {count_components} component certificates, {count_origins} origins")
    except (VerificationError, OSError, json.JSONDecodeError, TypeError, KeyError, AttributeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"Verified {total_pairs} pair(s), {total_components} component certificates, {total_origins} origins; {roots.vectors} independent root-box vectors checked.")
    print("Certificate validation passed. This does not independently establish enumeration completeness or pairwise nonisometry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
