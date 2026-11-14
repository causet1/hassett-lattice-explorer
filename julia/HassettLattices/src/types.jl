"""
    Limits(; max_work=5_000_000, timeout_seconds=60.0)

Cooperative search limits. Set either limit to `nothing` to disable it.
Work counts application search iterations and backend calls, not FLINT/Hecke
instructions. Backend calls cannot be interrupted; elapsed time is checked
before and after them. Exceeding a limit never returns a partial result.
"""
struct Limits
  max_work::Union{Int, Nothing}
  timeout_seconds::Union{Float64, Nothing}

  function Limits(; max_work = 5_000_000, timeout_seconds = 60.0)
    if max_work !== nothing
      max_work isa Integer && !(max_work isa Bool) && max_work > 0 ||
        throw(ArgumentError("max_work must be a positive integer or nothing"))
    end
    if timeout_seconds !== nothing
      timeout_seconds isa Real &&
      !(timeout_seconds isa Bool) &&
      isfinite(timeout_seconds) &&
      timeout_seconds > 0 ||
        throw(ArgumentError("timeout_seconds must be finite and positive"))
    end
    return new(max_work, timeout_seconds)
  end
end

"""A cooperative resource limit was exceeded without a complete result."""
struct ResourceLimitError <: Exception
  message::String
end

"""An emitted lattice certificate or result is inconsistent."""
struct VerificationError <: Exception
  message::String
end

Base.showerror(io::IO, e::ResourceLimitError) = print(io, e.message)
Base.showerror(io::IO, e::VerificationError) = print(io, e.message)

mutable struct Budget
  limits::Limits
  started::UInt64
  work::Int
end

Budget(limits::Limits) = Budget(limits, time_ns(), 0)
elapsed(b::Budget) = Float64(time_ns() - b.started) / 1.0e9

function check_time(b::Budget)
  t = b.limits.timeout_seconds
  if t !== nothing && elapsed(b) > t
    throw(ResourceLimitError("Time limit exceeded; no complete result"))
  end
  return nothing
end

function tick!(b::Budget)
  if b.work == typemax(Int) ||
     (b.limits.max_work !== nothing && b.work >= b.limits.max_work)
    throw(ResourceLimitError("Work limit exceeded; no complete result"))
  end
  b.work += 1
  check_time(b)
  return nothing
end

function backend(f, b::Budget)
  tick!(b)
  value = f()
  check_time(b)
  return value
end

"""
    MarkedLattice(gram)

A positive-definite integral rank-three lattice whose first basis vector is
the distinguished class `h` of square 3. Its orthogonal complement must be even.
The input is copied. Use [`gram_matrix`](@ref) for a defensive copy and
[`hecke_lattice`](@ref) for access to the general lattice algorithms in Hecke.
"""
struct MarkedLattice
  gram::ZZMatrix

  function MarkedLattice(g)
    m = _gram(g)
    all(iseven(m[i, i] - m[1, i]) for i in 1:3) ||
      throw(ArgumentError("The first vector is not distinguished"))
    return new(m)
  end
end

"""Exact whole-lattice K3 criterion, including the split congruence test."""
struct K3Association
  admissible::Bool
  discriminant_form::NTuple{3, ZZRingElem}
  content::ZZRingElem
  primitive_form::NTuple{3, ZZRingElem}
  h_splits_orthogonally::Bool
  mod3_witness::Union{NTuple{2, Int}, Nothing}
  obstructions::Vector{String}
end

"""A saturation construction and its column-coordinate inclusion certificates."""
struct ConstructionOrigin
  tau::ZZRingElem
  index::ZZRingElem
  a::ZZRingElem
  b::ZZRingElem
  base_gram::ZZMatrix
  overlattice_gram::ZZMatrix
  basis_map_to_representative::ZZMatrix
  embedding::ZZMatrix
end

"""One reduced irreducible component, with every retained construction route."""
struct Component
  id::String
  lattice::MarkedLattice
  determinant::ZZRingElem
  origins::Vector{ConstructionOrigin}
  k3_association::K3Association
end

"""One positive-definite starting lattice and its root/saturation diagnostics."""
mutable struct Candidate
  tau::ZZRingElem
  gram::ZZMatrix
  determinant::ZZRingElem
  root_witness::Union{Vector{ZZRingElem}, Nothing}
  accepted_overlattices::Int
end

"""
    IntersectionResult

A completed computation. Iteration, indexing and `length` operate on its
components. `input_pair` preserves caller order; `pair` is normalized. Fields
`candidates` and `diagnostics` expose the finite search. No incomplete instance
is returned by [`intersection_components`](@ref).
"""
struct IntersectionResult
  input_pair::NTuple{2, ZZRingElem}
  pair::NTuple{2, ZZRingElem}
  components::Vector{Component}
  candidates::Vector{Candidate}
  diagnostics::Dict{String, Any}
end

"""A primitive rank-two marking through h, modulo sign and addition of h."""
struct LabelEmbedding
  discriminant::ZZRingElem
  vector::Vector{ZZRingElem}
  gram::ZZMatrix
  admissible::Bool
end

"""Return the component vector of a completed intersection."""
components(r::IntersectionResult) = r.components
"""Return every retained saturation origin of a component."""
origins(c::Component) = c.origins
"""Return the number of reduced components of a completed intersection."""
component_count(r::IntersectionResult) = length(r.components)
Base.length(r::IntersectionResult) = component_count(r)
Base.getindex(r::IntersectionResult, i::Integer) = r.components[i]
Base.iterate(r::IntersectionResult, state...) = iterate(r.components, state...)
Base.eltype(::Type{IntersectionResult}) = Component

"""Return a copy of the integral Gram matrix, with h first."""
gram_matrix(l::MarkedLattice) = deepcopy(l.gram)
gram_matrix(c::Component) = gram_matrix(c.lattice)
"""Return the determinant of the rank-three lattice, not a Hassett label."""
discriminant(l::MarkedLattice) = Nemo.det(l.gram)
discriminant(c::Component) = deepcopy(c.determinant)
"""Return the rank (three) of a marked lattice or component."""
rank(::MarkedLattice) = 3
rank(::Component) = 3

function Base.show(io::IO, l::MarkedLattice)
  print(io, "Marked rank-three lattice of discriminant ", discriminant(l))
end

function Base.show(io::IO, c::Component)
  print(io, "Component ", c.id, " (determinant ", c.determinant, ")")
end

function Base.show(io::IO, r::IntersectionResult)
  print(
    io,
    "C_",
    r.input_pair[1],
    " intersect C_",
    r.input_pair[2],
    ": ",
    length(r),
    " reduced components (complete)",
  )
end
