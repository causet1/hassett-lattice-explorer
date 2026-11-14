"""
    intersection_components(d1, d2; limits=Limits())

Compute every reduced irreducible component of two distinct Hassett divisors
using Yang--Yu Algorithm 7.6. Returns an iterable [`IntersectionResult`](@ref)
with exact integral certificates and all construction origins. Rank-two
markings are primitive; their sum need not be saturated. Deduplication fixes h.
Resource exhaustion throws [`ResourceLimitError`](@ref), never a partial answer.
Scheme multiplicities and rationality are outside the scope of this algorithm.
"""
function intersection_components(d1, d2; limits::Limits = Limits())
  pair = normalize_pair(d1, d2)
  budget, cache = Budget(limits), LatticeCache()
  candidates = Candidate[]
  found = Component[]
  buckets = Dict{ZZRingElem, Vector{Component}}()
  counts = Dict{String, Any}(
    key => 0 for key in (
      "overlattice_parameter_candidates",
      "integral_overlattices",
      "rejected_parity",
      "rejected_roots",
      "accepted_marked_lattices",
      "duplicate_count",
    )
  )

  function accept!(g, base, tau, n, a, b)
    counts["accepted_marked_lattices"] += 1
    determinant = Nemo.det(g)
    embedding = ZZ[1 0 -a; 0 1 -b; 0 0 n]
    identity = Nemo.identity_matrix(ZZ, 3)
    bucket = get!(buckets, determinant, Component[])
    for c in bucket
      tick!(budget)
      change = _h_fixed_isometry(g, c.lattice.gram, budget, cache)
      if change !== nothing
        push!(
          c.origins,
          ConstructionOrigin(tau, n, a, b, base, g, change, change * embedding),
        )
        counts["duplicate_count"] += 1
        return nothing
      end
    end
    origin = ConstructionOrigin(tau, n, a, b, base, g, identity, embedding)
    id = "$(pair[1])-$(pair[2])-c$(lpad(length(found) + 1, 2, '0'))"
    c = Component(
      id,
      MarkedLattice(g),
      determinant,
      [origin],
      _k3_association(g, budget),
    )
    push!(found, c)
    push!(bucket, c)
    return nothing
  end

  # Keep all index-one constructions first, preserving historical component IDs.
  for tau in positive_parameters(pair...)
    tick!(budget)
    g = base_gram(pair..., tau)
    root = _root(g, budget, cache)
    push!(candidates, Candidate(tau, g, Nemo.det(g), root, 0))
    root === nothing && accept!(g, g, tau, ZZ(1), ZZ(0), ZZ(0))
  end
  for record in candidates
    record.root_witness === nothing || continue
    base, tau = record.gram, record.tau
    p, q, aa, bb = base[1, 2], base[1, 3], base[2, 2], base[3, 3]
    for n in _saturation_indices(record.determinant, budget)
      n == 1 && continue
      for (a, b) in _saturation_residues(pair..., tau, n, budget)
        tick!(budget)
        counts["overlattice_parameter_candidates"] += 1
        wn = 3 * a^2 + aa * b^2 + bb + 2 * p * a * b + 2 * q * a + 2 * tau * b
        iszero(mod(wn, n^2)) || continue
        hp = divexact(3 * a + p * b + q, n)
        up = divexact(p * a + aa * b + tau, n)
        wp = divexact(wn, n^2)
        counts["integral_overlattices"] += 1
        if isodd(wp - hp)
          counts["rejected_parity"] += 1
          continue
        end
        g = ZZ[3 p hp; p aa up; hp up wp]
        if _root(g, budget, cache) !== nothing
          counts["rejected_roots"] += 1
          continue
        end
        @assert Nemo.det(g) * n^2 == record.determinant
        record.accepted_overlattices += 1
        accept!(g, base, tau, n, a, b)
      end
    end
  end
  check_time(budget)
  counts["positive_definite_taus"] = [r.tau for r in candidates]
  counts["root_free_taus"] =
    [r.tau for r in candidates if r.root_witness === nothing]
  counts["work_units"] = budget.work
  counts["elapsed_seconds"] = elapsed(budget)
  return IntersectionResult((ZZ(d1), ZZ(d2)), pair, found, candidates, counts)
end
