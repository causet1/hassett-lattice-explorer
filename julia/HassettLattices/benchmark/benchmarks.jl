# Run with the developer project; resolve this checkout without changing it.
push!(LOAD_PATH, dirname(@__DIR__))

using BenchmarkTools
using HassettLattices

const SUITE = BenchmarkGroup()
const LIMITS = Limits(; max_work = nothing, timeout_seconds = nothing)
for pair in ((8, 26), (8, 96), (446, 494), (456, 488), (498, 500))
  intersection_components(pair...; limits = LIMITS) # Compile before timing.
  SUITE[join(pair, "-")] =
    @benchmarkable intersection_components($pair...; limits = $LIMITS)
end
results = run(SUITE; seconds = 2)
show(stdout, MIME("text/plain"), results)
println()
