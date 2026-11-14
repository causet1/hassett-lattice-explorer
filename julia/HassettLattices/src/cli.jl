function cli_settings()
  settings = ArgParse.ArgParseSettings(;
    description = "Exact Hassett lattice computations with Hecke/Nemo",
    exc_handler = ArgParse.debug_handler,
  )
  ArgParse.@add_arg_table! settings begin
    "command"
    help = "intersect, admissible, labels, verify, or catalogue"
    required = true
    "arguments"
    help = "labels, certificate path, or catalogue directory and bound"
    nargs = '*'
    "--output", "-o"
    help = "certificate output (.json or .json.gz); default stdout"
    "--bound"
    help = "marking search bound for labels"
    arg_type = BigInt
    default = big(500)
    "--component"
    help = "one-based component number for labels"
    arg_type = Int
    default = 1
    "--max-work"
    arg_type = Int
    default = 5_000_000
    "--timeout"
    arg_type = Float64
    default = 60.0
    "--no-limits"
    action = :store_true
    "--classification"
    help = "recompute classification during verification or catalogue reuse"
    action = :store_true
    "--stop-after"
    arg_type = Int
    "--plain"
    help = "write uncompressed catalogue shards"
    action = :store_true
  end
  return settings
end

"""
    main(args=ARGS; out=stdout, err=stderr)

Run the command-line interface, returning exit status 0 on success, 1 for an
incomplete catalogue, or 2 on invalid input, resource exhaustion or failed
verification. The executable wrapper calls `exit(main())`.
"""
function main(args = ARGS; out::IO = stdout, err::IO = stderr)
  try
    options = ArgParse.parse_args(args, cli_settings())
    command, positional = options["command"], options["arguments"]
    limits =
      options["no-limits"] ?
      Limits(; max_work = nothing, timeout_seconds = nothing) :
      Limits(;
        max_work = options["max-work"],
        timeout_seconds = options["timeout"],
      )
    arity(n) =
      length(positional) == n ||
      throw(ArgumentError("$command requires $n arguments"))
    data = nothing
    if command == "intersect"
      arity(2)
      result = intersection_components(parse.(BigInt, positional)...; limits)
      if options["output"] !== nothing
        write_result(options["output"], result)
        return 0
      end
      data = result_dict(result; timing = false)
    elseif command == "admissible"
      arity(1)
      d = parse(BigInt, only(positional))
      data = Dict(
        "discriminant" => d,
        "valid" => valid_discriminant(d),
        "admissible" => admissible_discriminant(d; limits),
      )
    elseif command == "verify"
      arity(1)
      r = read_result(
        only(positional);
        classification = options["classification"],
        limits,
      )
      data = Dict(
        "verified" => true,
        "component_count" => length(r),
        "classification_recomputed" => options["classification"],
      )
    elseif command == "labels"
      arity(1)
      r = read_result(only(positional); limits)
      i = options["component"]
      1 <= i <= length(r) ||
        throw(ArgumentError("Component index is out of range"))
      markings = primitive_markings(r[i], options["bound"]; limits)
      data = [
        Dict(
          "discriminant" => BigInt(m.discriminant),
          "vector" => json_value(m.vector),
          "gram" => json_value(m.gram),
          "admissible" => m.admissible,
        ) for m in markings
      ]
    elseif command == "catalogue"
      arity(2)
      data = build_catalogue(
        positional[1],
        parse(BigInt, positional[2]);
        limits,
        compressed = !options["plain"],
        stop_after = options["stop-after"],
        recheck_classification = options["classification"],
      )
      write(out, json_bytes(data))
      return data["complete"] ? 0 : 1
    else
      throw(ArgumentError("Unknown command: $command"))
    end
    write(out, json_bytes(data))
    return 0
  catch e
    e isa InterruptException && rethrow()
    println(err, sprint(showerror, e))
    return 2
  end
end
