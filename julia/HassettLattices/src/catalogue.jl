const PUBLISHED = Dict(
  (8, 14) => (
    "Auel et al., Theorem 4",
    "https://arxiv.org/abs/1205.0237v4",
    [21, 29, 32, 36, 37],
  ),
  (8, 26) => (
    "Awada, Proposition 3.2",
    "https://arxiv.org/abs/1910.10182v2",
    [29, 36, 48, 53, 61, 64, 68, 69],
  ),
  (8, 38) => (
    "Awada, Theorem 1.1(2)",
    "https://arxiv.org/abs/1910.10182v2",
    [36, 45, 61, 68, 80, 85, 93, 96, 100, 101],
  ),
  (12, 20) => (
    "Yang--Yu, Theorem 7.11",
    "https://arxiv.org/abs/2103.09132",
    [20, 32, 53, 68, 77, 80],
  ),
  (20, 38) => (
    "Yang--Yu, Theorem 7.9",
    "https://arxiv.org/abs/2103.09132",
    [
      45,
      77,
      92,
      120,
      133,
      157,
      168,
      188,
      197,
      213,
      220,
      232,
      237,
      245,
      248,
      252,
      253,
    ],
  ),
)

pair_key(pair) = join(minmax(pair...), "-")

function validation(r)
  fixture = get(PUBLISHED, minmax(r.pair...), nothing)
  if fixture === nothing
    return Dict(
      "status" => "computed",
      "reference" => "Exact algorithm; not an independent published fixture",
    )
  end
  reference, url, expected = fixture
  require(
    sort([c.determinant for c in r]) == expected,
    "Published fixture mismatch",
  )
  return Dict(
    "status" => "matched",
    "reference" => reference,
    "url" => url,
    "expected_count" => length(expected),
    "expected_discriminants" => expected,
  )
end

"""Summarize component records, K3 decisions, and saturation routes for one pair."""
function catalogue_summary(r::IntersectionResult)
  ds = [BigInt(c.determinant) for c in r]
  indices = [BigInt(o.index) for c in r for o in c.origins]
  admissible = count(c -> c.k3_association.admissible, r)
  return Dict{String, Any}(
    "key" => pair_key(r.pair),
    "d1" => BigInt(r.pair[1]),
    "d2" => BigInt(r.pair[2]),
    "component_count" => length(r),
    "marked_origin_count" => length(indices),
    "duplicate_count" => length(indices) - length(r),
    "determinants" => Dict(
      "min" => minimum(ds),
      "max" => maximum(ds),
      "distinct" => length(unique(ds)),
      "sum" => sum(ds),
    ),
    "k3" => Dict(
      "admissible" => admissible,
      "nonadmissible" => length(r) - admissible,
    ),
    "saturation" => Dict(
      "components" => count(c -> any(o.index > 1 for o in c.origins), r),
      "origins" => count(>(1), indices),
      "max_index" => maximum(indices),
    ),
  )
end

function aggregate(rows)
  total(key) = sum((e[key] for e in rows); init = 0)
  nested(key, field) = sum((e[key][field] for e in rows); init = 0)
  return Dict(
    "total_components" => total("component_count"),
    "total_component_records" => total("component_count"),
    "total_marked_origins" => total("marked_origin_count"),
    "total_k3_admissible_components" => nested("k3", "admissible"),
    "total_k3_nonadmissible_components" => nested("k3", "nonadmissible"),
    "total_components_with_saturation" => nested("saturation", "components"),
    "total_proper_overlattice_origins" => nested("saturation", "origins"),
    "total_duplicate_routes" => total("duplicate_count"),
    "max_saturation_index" =>
      maximum((e["saturation"]["max_index"] for e in rows); init = 0),
    "min_component_determinant" =>
      isempty(rows) ? nothing : minimum(e["determinants"]["min"] for e in rows),
    "max_component_determinant" =>
      isempty(rows) ? nothing : maximum(e["determinants"]["max"] for e in rows),
    "total_bytes" => total("bytes"),
    "total_uncompressed_bytes" => total("uncompressed_bytes"),
  )
end

"""
    build_catalogue(directory, bound; compressed=true, resume=true,
                    stop_after=nothing, checkpoint_every=10, limits=Limits(),
                    recheck_classification=false, progress=nothing)

Build all unordered label pairs through bound as atomic JSON/gzip shards and a
schema-1.1 index compatible with the explorer. Existing shards are certificate
checked before reuse; corrupt files are recomputed. Optionally re-enumerate
each reused classification. Limits apply separately to each pair/check.

`stop_after` bounds pairs processed in this invocation (including reuse).
Resource failures are recorded for retry, and an incomplete index stays marked
incomplete. Other exceptions propagate after a checkpoint. `progress`, if set,
is called with each checkpoint index. Use one writer per output directory.
"""
function build_catalogue(
  directory::AbstractString,
  bound;
  compressed::Bool = true,
  resume::Bool = true,
  stop_after = nothing,
  checkpoint_every::Integer = 10,
  limits::Limits = Limits(),
  recheck_classification::Bool = false,
  progress = nothing,
)
  b = _integer(bound)
  b >= 8 || throw(ArgumentError("The catalogue bound must be at least 8"))
  checkpoint_every > 0 && !(checkpoint_every isa Bool) ||
    throw(ArgumentError("checkpoint_every must be positive"))
  stop_after === nothing ||
    (_integer(stop_after) > 0) ||
    throw(ArgumentError("stop_after must be positive or nothing"))
  labels = valid_discriminants(b)
  pairs = [
    (labels[i], labels[j]) for i in eachindex(labels) for
    j in (i + 1):length(labels)
  ]
  extension = compressed ? ".json.gz" : ".json"
  mkpath(joinpath(directory, "pairs"))
  allowed = Set(pair_key(pair) * extension for pair in pairs)
  # Never silently produce a manifest with unlisted old pair files.
  for name in readdir(joinpath(directory, "pairs"))
    if (endswith(name, ".json") || endswith(name, ".json.gz")) &&
       !(name in allowed)
      throw(
        ArgumentError(
          "Existing shard $name is outside this bound/compression; use a new directory",
        ),
      )
    end
  end
  rows, failures = Dict{String, Any}[], Dict{String, Any}[]
  started = time_ns()
  processed = computed = reused = repaired = 0
  function checkpoint(stage)
    stats = aggregate(rows)
    pending = length(pairs) - length(rows) - length(failures)
    index = Dict{String, Any}(
      "schema_version" => "1.1",
      "title" => "Hassett Lattice Explorer",
      "catalogue_version" => "1.1.0",
      "algorithm" => "Yang--Yu Algorithm 7.6",
      "reference" => "https://arxiv.org/abs/2103.09132",
      "license" => "MIT",
      "max_discriminant" => BigInt(b),
      "discriminants" => json_value(labels),
      "expected_pair_count" => length(pairs),
      "pair_count" => length(rows),
      "component_count" => stats["total_components"],
      "component_records" => stats["total_components"],
      "failed_pair_count" => length(failures),
      "pending_pair_count" => pending,
      "complete" => length(rows) == length(pairs) && isempty(failures),
      "scope" => "Finite range of distinct label pairs; component records across pairs are not globally distinct loci. Reduced components only.",
      "pairs" => rows,
      "statistics" => stats,
      "failures" => failures,
    )
    atomic_write(joinpath(directory, "catalogue-index.json"), json_bytes(index))
    atomic_write(
      joinpath(directory, "failures.json"),
      json_bytes(Dict("schema_version" => "1.0", "failures" => failures)),
    )
    state = Dict(
      "stage" => stage,
      "updated_at" => string(Dates.now(Dates.UTC)),
      "elapsed_seconds" => Float64(time_ns() - started) / 1.0e9,
      "processed_this_run" => processed,
      "computed_this_run" => computed,
      "reused_this_run" => reused,
      "invalid_existing_files" => repaired,
    )
    atomic_write(joinpath(directory, "run-state.json"), json_bytes(state))
    progress === nothing || progress(index)
    return index
  end
  try
    for pair in pairs
      stop_after !== nothing && processed >= stop_after && break
      key = pair_key(pair)
      relative = "pairs/$key$extension"
      path = joinpath(directory, "pairs", key * extension)
      result = nothing
      if resume && isfile(path)
        try
          result =
            read_result(path; classification = recheck_classification, limits)
          require(
            minmax(result.pair...) == pair,
            "Shard has the wrong label pair",
          )
          validation(result)
          reused += 1
        catch e
          e isa InterruptException && rethrow()
          if e isa ResourceLimitError
            push!(
              failures,
              Dict(
                "key" => key,
                "d1" => BigInt(pair[1]),
                "d2" => BigInt(pair[2]),
                "error" => sprint(showerror, e),
              ),
            )
            processed += 1
            mod(processed, checkpoint_every) == 0 && checkpoint("running")
            continue
          end
          result = nothing
          repaired += 1
        end
      end
      try
        if result === nothing
          result = intersection_components(pair...; limits)
          computed += 1
        end
        data = result_dict(result; timing = false)
        data["input_pair"] = json_value(pair)
        data["validation"] = validation(result)
        raw = json_bytes(data)
        stored = compressed ? transcode(CodecZlib.GzipCompressor, raw) : raw
        atomic_write(path, stored)
        row = catalogue_summary(result)
        merge!(
          row,
          Dict(
            "path" => relative,
            "compression" => compressed ? "gzip" : "none",
            "sha256" => bytes2hex(SHA.sha256(stored)),
            "uncompressed_sha256" => bytes2hex(SHA.sha256(raw)),
            "bytes" => length(stored),
            "uncompressed_bytes" => length(raw),
            "validation" => data["validation"]["status"],
          ),
        )
        push!(rows, row)
      catch e
        e isa ResourceLimitError || rethrow()
        push!(
          failures,
          Dict(
            "key" => key,
            "d1" => BigInt(pair[1]),
            "d2" => BigInt(pair[2]),
            "error" => sprint(showerror, e),
          ),
        )
      end
      processed += 1
      mod(processed, checkpoint_every) == 0 && checkpoint("running")
    end
  catch
    checkpoint("interrupted")
    rethrow()
  end
  return checkpoint("finished")
end
