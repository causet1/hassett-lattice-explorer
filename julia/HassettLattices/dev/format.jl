using JuliaFormatter

root = dirname(@__DIR__)
for directory in ("src", "test", "bin", "examples", "benchmark", "dev")
  path = joinpath(root, directory)
  isdir(path) && format(path; verbose = true)
end
format_file(joinpath(root, "docs", "make.jl"); indent = 2, margin = 80)
