const ExactInteger = Union{Integer, ZZRingElem}

function _integer(x)
  x isa ExactInteger && !(x isa Bool) ||
    throw(ArgumentError("Expected an exact integer"))
  return ZZ(x)
end

"""Test whether d is an integer greater than 6 and congruent to 0 or 2 mod 6."""
function valid_discriminant(d)
  return d isa ExactInteger && !(d isa Bool) && d > 6 && mod(d, 6) in (0, 2)
end

"""Return every valid Hassett label up to and including bound."""
function valid_discriminants(bound)
  b = _integer(bound)
  b >= 0 || throw(ArgumentError("The bound must be nonnegative"))
  return ZZRingElem[d for d in ZZ(8):b if valid_discriminant(d)]
end

function arithmetic_obstructions(d::ZZRingElem, budget::Budget)
  out = String[]
  iszero(mod(d, 4)) && push!(out, "divisible by 4")
  iszero(mod(d, 9)) && push!(out, "divisible by 9")
  factors = backend(() -> Nemo.factor(d), budget)
  for p in sort!([p for (p, _) in factors])
    if p != 2 && mod(p, 3) == 2
      push!(out, "divisible by the odd prime $p, congruent to 2 modulo 3")
    end
  end
  return out
end

"""Test Hassett's arithmetic condition for an untwisted K3 label."""
function admissible_discriminant(d; limits::Limits = Limits())
  valid_discriminant(d) || return false
  return isempty(arithmetic_obstructions(ZZ(d), Budget(limits)))
end

"""Normalize two distinct valid labels as required by Yang--Yu Algorithm 7.6."""
function normalize_pair(d1, d2)
  valid_discriminant(d1) && valid_discriminant(d2) || throw(
    ArgumentError("Labels must be integers > 6, congruent to 0 or 2 mod 6"),
  )
  d1 != d2 ||
    throw(ArgumentError("Self-intersection is not a rank-three problem"))
  a, b = ZZ(d1), ZZ(d2)
  if mod(a, 6) == mod(b, 6)
    return minmax(a, b)
  end
  return mod(a, 6) == 2 ? (a, b) : (b, a)
end

"""Return the exact finite parameter interval of positive starting lattices."""
function positive_parameters(d1, d2)
  a, b = normalize_pair(d1, d2)
  eps = Int(mod(a, 6) == 2 && mod(b, 6) == 2)
  radius = isqrt(a * b - 1)
  lower, upper = cld(eps - radius, 3), fld(eps + radius, 3)
  return (eps == 0 ? max(ZZ(0), lower) : lower):upper
end

"""Construct the normalized starting Gram matrix at an integer parameter tau."""
function base_gram(d1, d2, tau)
  a, b = normalize_pair(d1, d2)
  t = _integer(tau)
  p, q = Int(mod(a, 6) == 2), Int(mod(b, 6) == 2)
  return ZZ[3 p q; p divexact(a + p, 3) t; q t divexact(b + q, 3)]
end

"""Return all positive n such that n^2 divides the positive determinant d."""
function saturation_indices(d; limits::Limits = Limits())
  return _saturation_indices(_integer(d), Budget(limits))
end

function _saturation_indices(d::ZZRingElem, budget::Budget)
  d > 0 || throw(ArgumentError("The determinant must be positive"))
  ds = backend(() -> Nemo.divisors(d), budget)
  return sort!(ZZRingElem[n for n in ds if iszero(mod(d, n * n))])
end

function linear_residues(c::ZZRingElem, rhs::ZZRingElem, n::ZZRingElem)
  g = gcd(c, n)
  iszero(mod(rhs, g)) || return ZZRingElem[]
  modulus = divexact(n, g)
  start =
    modulus == 1 ? ZZ(0) :
    mod(invmod(divexact(c, g), modulus) * divexact(rhs, g), modulus)
  return start:modulus:(n - 1)
end

"""
    saturation_residues(d1, d2, tau, n)

Return `(a, b)` in `[0,n)^2` satisfying both linear integrality conditions and
`gcd(b,n)=1`, sorted in construction order. Norm integrality and parity are
checked by the intersection algorithm. Solving the eliminated congruence
`d1*b = p*q - 3*tau (mod n)` avoids an n-squared search.
"""
function saturation_residues(d1, d2, tau, n; limits::Limits = Limits())
  a, b = normalize_pair(d1, d2)
  return _saturation_residues(a, b, _integer(tau), _integer(n), Budget(limits))
end

function _saturation_residues(d1, d2, tau, n, budget)
  n > 0 || throw(ArgumentError("The index must be positive"))
  p, q = ZZ(mod(d1, 6) == 2), ZZ(mod(d2, 6) == 2)
  aa = divexact(d1 + p, 3)
  found = Tuple{ZZRingElem, ZZRingElem}[]
  for b in linear_residues(d1, p * q - 3 * tau, n)
    tick!(budget)
    gcd(b, n) == 1 || continue
    for a in linear_residues(ZZ(3), -p * b - q, n)
      tick!(budget)
      iszero(mod(p * a + aa * b + tau, n)) && push!(found, (a, b))
    end
  end
  return sort!(found)
end
