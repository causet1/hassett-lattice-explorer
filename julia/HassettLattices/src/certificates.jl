json_value(x) = x
json_value(x::ZZRingElem) = BigInt(x)
json_value(x::ZZMatrix) =
  [[BigInt(x[i, j]) for j in 1:Nemo.ncols(x)] for i in 1:Nemo.nrows(x)]
json_value(x::Union{Tuple, AbstractVector}) = [json_value(v) for v in x]
json_value(x::AbstractDict) = Dict(string(k) => json_value(v) for (k, v) in x)

function k3_dict(k::K3Association)
  return Dict{String, Any}(
    "admissible" => k.admissible,
    "discriminant_form" => json_value(k.discriminant_form),
    "content" => BigInt(k.content),
    "primitive_form" => json_value(k.primitive_form),
    "h_splits_orthogonally" => k.h_splits_orthogonally,
    "mod3_witness" => json_value(k.mod3_witness),
    "obstructions" => k.obstructions,
    "criterion" =>
      k.h_splits_orthogonally ? "Yang--Yu Theorem 8.9" : "Yang--Yu Theorem 8.8",
    "interpretation" => "Whole-lattice untwisted K3 criterion; not a rationality decision.",
  )
end

function origin_dict(o::ConstructionOrigin)
  return Dict(
    string(f) => json_value(getfield(o, f)) for
    f in fieldnames(ConstructionOrigin)
  )
end

"""Convert a completed result to the explorer's exact-integer JSON schema 1.0."""
function result_dict(r::IntersectionResult; timing::Bool = true)
  cs = [
    Dict(
      "id" => c.id,
      "gram" => json_value(c.lattice.gram),
      "determinant" => BigInt(c.determinant),
      "rank" => 3,
      "h" => [1, 0, 0],
      "tau" => BigInt(first(c.origins).tau),
      "index" => BigInt(first(c.origins).index),
      "origins" => origin_dict.(c.origins),
      "k3_association" => k3_dict(c.k3_association),
    ) for c in r
  ]
  candidates = [
    Dict(
      "tau" => BigInt(c.tau),
      "gram" => json_value(c.gram),
      "determinant" => BigInt(c.determinant),
      "root_free" => c.root_witness === nothing,
      "root_witness" => json_value(c.root_witness),
      "accepted_overlattices" => c.accepted_overlattices,
    ) for c in r.candidates
  ]
  diagnostics = json_value(r.diagnostics)
  timing || pop!(diagnostics, "elapsed_seconds", nothing)
  return Dict{String, Any}(
    "schema_version" => "1.0",
    "algorithm" => "Yang--Yu Algorithm 7.6",
    "reference" => "https://arxiv.org/abs/2103.09132",
    "input_pair" => json_value(r.input_pair),
    "d1" => BigInt(r.pair[1]),
    "d2" => BigInt(r.pair[2]),
    "complete" => true,
    "component_count" => length(r),
    "components" => cs,
    "candidates" => candidates,
    "diagnostics" => diagnostics,
    "scope" => "Reduced irreducible components; scheme multiplicities are not computed.",
  )
end

require(condition::Bool, message) =
  condition || throw(VerificationError(message))

function verify_k3(actual, expected)
  for f in fieldnames(K3Association)
    require(
      getfield(actual, f) == getfield(expected, f),
      "Incorrect K3 field: $f",
    )
  end
end

"""
    verify_result(result; classification=false, limits=Limits())

Verify exact Gram identities, positivity, parity, root-freeness, primitive
markings, K3 decisions, origins and starting-parameter coverage. With
`classification=true`, rerun the finite algorithm and compare its complete
origin partition and representative isometry classes. This uses the same
Hecke backend; the repository's Python verifier supplies an independent check.
Returns `true` or throws; it never treats an interrupted check as successful.
"""
function verify_result(
  r::IntersectionResult;
  classification::Bool = false,
  limits::Limits = Limits(),
)
  budget, cache = Budget(limits), LatticeCache()
  require(
    normalize_pair(r.input_pair...) == r.pair,
    "Incorrect normalized pair",
  )
  require(
    [c.tau for c in r.candidates] == collect(positive_parameters(r.pair...)),
    "Incomplete or unordered starting parameter coverage",
  )
  records = Dict(c.tau => c for c in r.candidates)
  accepted = Dict(c.tau => 0 for c in r.candidates)
  expected_bases = Set{NTuple{4, ZZRingElem}}()
  all_origins = Set{NTuple{4, ZZRingElem}}()
  actual_bases = Set{NTuple{4, ZZRingElem}}()
  for c in r.candidates
    tick!(budget)
    require(
      c.gram == base_gram(r.pair..., c.tau),
      "Incorrect starting Gram matrix",
    )
    require(Nemo.det(c.gram) == c.determinant, "Incorrect starting determinant")
    if c.root_witness === nothing
      require(
        _root(c.gram, budget, cache) === nothing,
        "Undetected starting root",
      )
      push!(expected_bases, (c.tau, ZZ(1), ZZ(0), ZZ(0)))
    else
      require(length(c.root_witness) == 3, "Wrong root dimension")
      v = Nemo.matrix(ZZ, 3, 1, c.root_witness)
      require((transpose(v) * c.gram * v)[1, 1] == 2, "Invalid root witness")
    end
  end
  ids = Set{String}()
  grams = Set{NTuple{9, ZZRingElem}}()
  for c in r
    tick!(budget)
    g = MarkedLattice(c.lattice.gram).gram
    require(!(c.id in ids), "Duplicate component ID")
    require(!(gram_key(g) in grams), "Repeated component Gram matrix")
    push!(ids, c.id)
    push!(grams, gram_key(g))
    require(c.determinant == Nemo.det(g), "Incorrect component determinant")
    require(_root(g, budget, cache) === nothing, "Component contains a root")
    verify_k3(c.k3_association, _k3_association(g, budget))
    require(!isempty(c.origins), "Component has no origins")
    for o in c.origins
      tick!(budget)
      key = (o.tau, o.index, o.a, o.b)
      require(!(key in all_origins), "Repeated construction origin")
      push!(all_origins, key)
      require(haskey(records, o.tau), "Origin outside parameter interval")
      require(
        records[o.tau].root_witness === nothing,
        "Origin starts from a root lattice",
      )
      require(
        o.index > 0 && 0 <= o.a < o.index && 0 <= o.b < o.index,
        "Invalid saturation residues",
      )
      require(gcd(o.b, o.index) == 1, "Second marking is not primitive")
      require(o.base_gram == records[o.tau].gram, "Incorrect origin base")
      over = MarkedLattice(o.overlattice_gram).gram
      u, e = o.basis_map_to_representative, o.embedding
      require(
        abs(Nemo.det(u)) == 1 && u[:, 1] == ZZRingElem[1, 0, 0],
        "Invalid h-fixed basis map",
      )
      require(transpose(u) * g * u == over, "Invalid isometry identity")
      canonical = ZZ[1 0 -o.a; 0 1 -o.b; 0 0 o.index]
      require(e == u * canonical, "Incorrect construction embedding")
      require(transpose(e) * g * e == o.base_gram, "Invalid inclusion identity")
      require(
        c.determinant * o.index^2 == records[o.tau].determinant,
        "Invalid index/discriminant identity",
      )
      if o.index == 1
        push!(actual_bases, key)
      else
        accepted[o.tau] += 1
      end
    end
  end
  require(expected_bases == actual_bases, "Missing starting origin")
  require(
    all(c.accepted_overlattices == accepted[c.tau] for c in r.candidates),
    "Incorrect accepted saturation counts",
  )
  require(
    get(r.diagnostics, "accepted_marked_lattices", nothing) ==
    length(all_origins),
    "Incorrect accepted origin count",
  )
  require(
    get(r.diagnostics, "duplicate_count", nothing) ==
    length(all_origins) - length(r),
    "Incorrect duplicate count",
  )
  require(
    get(r.diagnostics, "positive_definite_taus", nothing) ==
    [c.tau for c in r.candidates],
    "Incorrect positive parameter diagnostics",
  )
  require(
    get(r.diagnostics, "root_free_taus", nothing) ==
    [c.tau for c in r.candidates if c.root_witness === nothing],
    "Incorrect root-free parameter diagnostics",
  )
  if classification
    remaining_work =
      limits.max_work === nothing ? nothing : limits.max_work - budget.work
    remaining_time =
      limits.timeout_seconds === nothing ? nothing :
      limits.timeout_seconds - elapsed(budget)
    (remaining_work === nothing || remaining_work > 0) &&
    (remaining_time === nothing || remaining_time > 0) || throw(
      ResourceLimitError("No budget left for classification verification"),
    )
    expected = intersection_components(
      r.pair...;
      limits = Limits(;
        max_work = remaining_work,
        timeout_seconds = remaining_time,
      ),
    )
    budget.work += expected.diagnostics["work_units"]
    require(length(expected) == length(r), "Incorrect component count")
    partition(c) = Tuple(sort!([(o.tau, o.index, o.a, o.b) for o in c.origins]))
    partitions = Dict(partition(c) => c for c in r)
    for c in expected
      match = get(partitions, partition(c), nothing)
      require(match !== nothing, "Incorrect classification of origins")
      require(
        _h_fixed_isometry(c.lattice.gram, match.lattice.gram, budget, cache) !==
        nothing,
        "Incorrect representative isometry class",
      )
    end
  end
  check_time(budget)
  return true
end

function parse_k3(k)
  k["admissible"] isa Bool && k["h_splits_orthogonally"] isa Bool ||
    throw(VerificationError("K3 flags must be booleans"))
  witness = k["mod3_witness"]
  return K3Association(
    k["admissible"],
    Tuple(_integer.(k["discriminant_form"])),
    _integer(k["content"]),
    Tuple(_integer.(k["primitive_form"])),
    k["h_splits_orthogonally"],
    witness === nothing ? nothing : Tuple(Int.(_integer.(witness))),
    String.(k["obstructions"]),
  )
end

function parse_result(data)
  require(data["schema_version"] == "1.0", "Unsupported pair schema")
  require(data["complete"] === true, "Incomplete result")
  cs = Component[]
  for c in data["components"]
    require(
      _integer(c["rank"]) == 3 && _integer.(c["h"]) == [1, 0, 0],
      "Invalid rank or distinguished vector",
    )
    os = [
      ConstructionOrigin(
        (_integer(o[k]) for k in ("tau", "index", "a", "b"))...,
        (
          _matrix(o[k], 3, 3) for k in (
            "base_gram",
            "overlattice_gram",
            "basis_map_to_representative",
            "embedding",
          )
        )...,
      ) for o in c["origins"]
    ]
    require(!isempty(os), "Component has no origins")
    require(
      _integer(c["tau"]) == first(os).tau &&
        _integer(c["index"]) == first(os).index,
      "Representative metadata disagree with first origin",
    )
    push!(
      cs,
      Component(
        c["id"],
        MarkedLattice(c["gram"]),
        _integer(c["determinant"]),
        os,
        parse_k3(c["k3_association"]),
      ),
    )
  end
  require(
    _integer(data["component_count"]) == length(cs),
    "Incorrect component count",
  )
  candidates = Candidate[]
  for c in data["candidates"]
    require(
      c["root_free"] === (c["root_witness"] === nothing),
      "Inconsistent root flag",
    )
    root =
      c["root_witness"] === nothing ? nothing : _integer.(c["root_witness"])
    push!(
      candidates,
      Candidate(
        _integer(c["tau"]),
        _gram(c["gram"]),
        _integer(c["determinant"]),
        root,
        Int(_integer(c["accepted_overlattices"])),
      ),
    )
  end
  return IntersectionResult(
    Tuple(_integer.(data["input_pair"])),
    (_integer(data["d1"]), _integer(data["d2"])),
    cs,
    candidates,
    Dict{String, Any}(data["diagnostics"]),
  )
end

function atomic_write(path::AbstractString, bytes)
  directory = dirname(abspath(path))
  mkpath(directory)
  temporary, io = mktemp(directory)
  try
    write(io, bytes)
    close(io)
    # mv(...; force=true) unlinks the old destination before renaming. The
    # filesystem rename replaces it directly; mktemp keeps both on one device.
    Base.Filesystem.rename(temporary, path)
  finally
    isopen(io) && close(io)
    isfile(temporary) && rm(temporary)
  end
  return path
end

# JSON.jl handles sorted keys and arbitrary-size integers without a custom encoder.
json_bytes(data) =
  Vector{UInt8}(codeunits(JSON.json(data; sort_keys = true) * "\n"))

"""Atomically write an exact JSON certificate; `.gz` selects gzip compression."""
function write_result(
  path::AbstractString,
  r::IntersectionResult;
  timing::Bool = false,
)
  raw = json_bytes(result_dict(r; timing))
  bytes = endswith(path, ".gz") ? transcode(CodecZlib.GzipCompressor, raw) : raw
  return atomic_write(path, bytes)
end

"""
    read_result(path; classification=false, limits=Limits())

Read JSON or `.gz`, preserving arbitrary-size integers, and verify certificates
before returning. Set `classification=true` to also recompute completeness.
"""
function read_result(
  path::AbstractString;
  classification::Bool = false,
  limits::Limits = Limits(),
)
  raw = read(path)
  endswith(path, ".gz") && (raw = transcode(CodecZlib.GzipDecompressor, raw))
  r = try
    parse_result(JSON.parse(String(raw); dicttype = Dict{String, Any}))
  catch e
    e isa InterruptException && rethrow()
    throw(VerificationError("Invalid result: $(sprint(showerror, e))"))
  end
  verify_result(r; classification, limits)
  return r
end
