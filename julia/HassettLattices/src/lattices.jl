function _matrix(g, rows::Int, cols::Int)
  if g isa Union{Nemo.ZZMatrix, AbstractMatrix}
    size(g) == (rows, cols) || throw(ArgumentError("Wrong matrix dimensions"))
    return Nemo.matrix(
      ZZ,
      rows,
      cols,
      [_integer(g[i, j]) for i in 1:rows for j in 1:cols],
    )
  elseif g isa AbstractVector
    length(g) == rows &&
    all(r isa AbstractVector && length(r) == cols for r in g) ||
      throw(ArgumentError("Wrong matrix dimensions"))
    return Nemo.matrix(
      ZZ,
      rows,
      cols,
      [_integer(g[i][j]) for i in 1:rows for j in 1:cols],
    )
  end
  throw(ArgumentError("Expected an integral matrix"))
end

function _gram(g)
  m = _matrix(g, 3, 3)
  m == transpose(m) || throw(ArgumentError("Gram matrix must be symmetric"))
  m[1, 1] == 3 ||
    throw(ArgumentError("The first basis vector must have square 3"))
  3 * m[2, 2] - m[1, 2]^2 > 0 && Nemo.det(m) > 0 ||
    throw(ArgumentError("Gram matrix must be positive definite"))
  return m
end

_marked(l::MarkedLattice) = l
_marked(c::Component) = c.lattice
_marked(g) = MarkedLattice(g)
_gram(l::MarkedLattice) = gram_matrix(l)
_gram(c::Component) = gram_matrix(c)

"""Convert a marked lattice or component to an independent Hecke integer lattice."""
function hecke_lattice(l)
  return Hecke.integer_lattice(; gram = _marked(l).gram, cached = false)
end

"""Change basis by an integral unimodular column matrix fixing the first vector."""
function change_basis(l, u)
  g = _marked(l).gram
  s = _matrix(u, 3, 3)
  abs(Nemo.det(s)) == 1 && s[:, 1] == ZZRingElem[1, 0, 0] ||
    throw(ArgumentError("Basis change must be unimodular and fix h"))
  return MarkedLattice(transpose(s) * g * s)
end

gram_key(g::ZZMatrix) = ntuple(k -> g[div(k - 1, 3) + 1, mod(k - 1, 3) + 1], 9)

mutable struct LatticeCache
  lattices::Dict{NTuple{9, ZZRingElem}, Hecke.ZZLat}
  roots::Dict{NTuple{9, ZZRingElem}, Union{Vector{ZZRingElem}, Nothing}}
end

LatticeCache() = LatticeCache(Dict(), Dict())

function cached_lattice(g, cache)
  return get!(cache.lattices, gram_key(g)) do
    Hecke.integer_lattice(; gram = g, cached = false)
  end
end

function _root(g, budget, cache)
  tick!(budget)
  key = gram_key(g)
  haskey(cache.roots, key) && return cache.roots[key]
  a = 3 * g[2, 2] - g[1, 2]^2
  b = 3 * g[2, 3] - g[1, 2] * g[1, 3]
  c = 3 * g[3, 3] - g[1, 3]^2
  # H(y,z) >= (min(a,c)-abs(b))*(y^2+z^2). A norm-two vector
  # would require H(y,z) <= 6; y=z=0 cannot have square two.
  if min(a, c) - abs(b) > 6
    cache.roots[key] = nothing
    return nothing
  end
  value = backend(budget) do
    l = cached_lattice(g, cache)
    vectors = Hecke.short_vectors_iterator(l, 2, 2, ZZRingElem)
    item = iterate(vectors)
    return item === nothing ? nothing : ZZRingElem[item[1][1]...]
  end
  cache.roots[key] = value
  return value
end

"""Find an exact norm-two witness using Hecke, or return nothing if none exists."""
function norm_two_vector(g; limits::Limits = Limits())
  return _root(_gram(g), Budget(limits), LatticeCache())
end

function _h_fixed_isometry(source, target, budget, cache)
  source == target && return Nemo.identity_matrix(ZZ, 3)
  Nemo.det(source) == Nemo.det(target) || return nothing
  left, right = cached_lattice(source, cache), cached_lattice(target, cache)
  ok, rational = backend(budget) do
    Hecke.is_isometric_with_isometry(left, right)
  end
  ok || return nothing
  transform = Nemo.matrix(ZZ, rational)
  # Hecke uses row coordinates. Transport the image of h through the finite
  # target automorphism orbit; only this marked-vector bookkeeping is ours.
  start = transform[1:1, :]
  desired = ZZ[1 0 0]
  start == desired && return transpose(transform)
  start == -desired && return -transpose(transform)
  generators = backend(budget) do
    [
      Nemo.matrix(ZZ, a) for a in Hecke.automorphism_group_generators(
        right;
        ambient_representation = false,
      )
    ]
  end
  orbit = [start]
  transports = [Nemo.identity_matrix(ZZ, 3)]
  seen = Set([Tuple(start[1, j] for j in 1:3)])
  position = 1
  while position <= length(orbit)
    for a in generators
      tick!(budget)
      image = orbit[position] * a
      key = Tuple(image[1, j] for j in 1:3)
      key in seen && continue
      transport = transports[position] * a
      if image == desired || image == -desired
        u = transpose(transform * transport)
        image == -desired && (u = -u)
        @assert transpose(u) * target * u == source
        @assert u[:, 1] == ZZRingElem[1, 0, 0]
        return u
      end
      push!(seen, key)
      push!(orbit, image)
      push!(transports, transport)
    end
    position += 1
  end
  return nothing
end

"""
    h_fixed_isometry(source, target; limits=Limits())

Return U with `transpose(U)*target*U == source`, `U*e1 == e1`, and determinant
plus or minus one, or `nothing`. Reuses Hecke's Plesken--Souvignier isometry and
automorphism computations, then checks the distinguished-vector orbit.
"""
function h_fixed_isometry(source, target; limits::Limits = Limits())
  return _h_fixed_isometry(
    _gram(source),
    _gram(target),
    Budget(limits),
    LatticeCache(),
  )
end

function schur_form(g)
  p, q = g[1, 2], g[1, 3]
  return ZZ[
    3 * g[2, 2] - p^2 3 * g[2, 3] - p * q;
    3 * g[2, 3] - p * q 3 * g[3, 3] - q^2
  ]
end

function _k3_association(g, budget)
  h = schur_form(g)
  form = (h[1, 1], 2 * h[1, 2], h[2, 2])
  content = gcd(gcd(form[1], form[2]), form[3])
  primitive = map(x -> divexact(x, content), form)
  split = iszero(mod(g[1, 2], 3)) && iszero(mod(g[1, 3], 3))
  obstructions = arithmetic_obstructions(content, budget)
  witness = nothing
  for y in 0:2, z in 0:2
    if mod(primitive[1] * y^2 + primitive[2] * y * z + primitive[3] * z^2, 3) ==
       1
      witness = (y, z)
      break
    end
  end
  if split && witness === nothing
    push!(
      obstructions,
      "primitive discriminant form does not represent 1 modulo 3",
    )
  end
  return K3Association(
    isempty(obstructions),
    form,
    content,
    primitive,
    split,
    witness,
    obstructions,
  )
end

"""Apply Yang--Yu Theorems 8.8--8.9 to the whole marked lattice."""
function lattice_k3_association(l; limits::Limits = Limits())
  return _k3_association(_marked(l).gram, Budget(limits))
end

"""
    primitive_markings(l, bound; admissible_only=false, limits=Limits())

Enumerate primitive rank-two sublattices through h with valid discriminant at
most bound. Representatives have second vector `(0,y,z)` and are taken modulo
sign and addition of h. Reuses Hecke short vectors of the binary Schur form.
"""
function primitive_markings(
  l,
  bound;
  admissible_only::Bool = false,
  limits::Limits = Limits(),
)
  result =
    _primitive_markings(_marked(l).gram, bound, admissible_only, Budget(limits))
  return result
end

function _primitive_markings(g, bound, admissible_only, budget)
  b = _integer(bound)
  b >= 0 || throw(ArgumentError("The bound must be nonnegative"))
  b < 8 && return LabelEmbedding[]
  binary = Hecke.integer_lattice(; gram = schur_form(g), cached = false)
  vectors = backend(() -> Hecke.short_vectors(binary, 8, b, ZZRingElem), budget)
  found = LabelEmbedding[]
  for (v, square) in vectors
    tick!(budget)
    y, z = v
    gcd(y, z) == 1 || continue
    d = ZZ(square)
    valid_discriminant(d) || continue
    admissible = isempty(arithmetic_obstructions(d, budget))
    admissible_only && !admissible && continue
    if y < 0 || (y == 0 && z < 0)
      y, z = -y, -z
    end
    embedding = ZZ[1 0; 0 y; 0 z]
    push!(
      found,
      LabelEmbedding(
        d,
        ZZRingElem[0, y, z],
        transpose(embedding) * g * embedding,
        admissible,
      ),
    )
  end
  sort!(found; by = m -> (m.discriminant, m.vector[2], m.vector[3]))
  return found
end

"""Return an admissible primitive marking within bound, or nothing (a bounded search)."""
function k3_witness(l, bound = 10000; limits::Limits = Limits())
  markings = primitive_markings(l, bound; admissible_only = true, limits)
  return isempty(markings) ? nothing : first(markings)
end

"""
    k3_certificate(l; limits=Limits())

Return `(association, witness, search_bound)`. A positive decision includes a
primitive admissible `LabelEmbedding`; a negative decision includes the exact
arithmetic obstructions and `witness = nothing`. Doubling discriminant bounds
exhausts the positive search, using Hecke and one shared work/time budget.
Resource exhaustion throws `ResourceLimitError`, never a negative decision.
This certifies an untwisted K3 association, not rationality.
"""
function k3_certificate(l; limits::Limits = Limits())
  g, budget = _marked(l).gram, Budget(limits)
  association = _k3_association(g, budget)
  bound, witness = ZZ(0), nothing
  if association.admissible
    bound = ZZ(16)
    while witness === nothing
      found = _primitive_markings(g, bound, true, budget)
      if isempty(found)
        bound *= 2
      else
        witness = first(found)
      end
    end
  end
  check_time(budget)
  return (association = association, witness = witness, search_bound = bound)
end

"""Return determinant, Smith invariants, h-divisibility, and the K3 criterion."""
function lattice_invariants(l; limits::Limits = Limits())
  marked = _marked(l)
  budget = Budget(limits)
  smith = backend(() -> Nemo.snf(marked.gram), budget)
  elementary = ZZRingElem[smith[i, i] for i in 1:3 if smith[i, i] != 1]
  return (
    rank = 3,
    determinant = discriminant(marked),
    discriminant_group = elementary,
    h_divisibility = gcd(
      gcd(marked.gram[1, 1], marked.gram[1, 2]),
      marked.gram[1, 3],
    ),
    k3_association = _k3_association(marked.gram, budget),
  )
end
