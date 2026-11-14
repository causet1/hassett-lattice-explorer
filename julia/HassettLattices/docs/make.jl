using Documenter
using HassettLattices

makedocs(;
  modules = [HassettLattices],
  sitename = "HassettLattices.jl",
  authors = "Hassett Lattice Explorer contributors",
  format = Documenter.HTML(;
    prettyurls = get(ENV, "CI", "false") == "true",
    repolink = "https://github.com/causet1/hassett-lattice-explorer/tree/main/julia/HassettLattices",
  ),
  pages = [
    "Guide" => "index.md",
    "Algorithm and backends" => "algorithm.md",
    "API" => "api.md",
  ],
  checkdocs = :exports,
  doctest = true,
  remotes = nothing,
)
