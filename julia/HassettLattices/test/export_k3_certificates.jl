# Development integration: native certificates for every embedded component.
using HassettLattices
import JSON

catalogue = JSON.parse(read(ARGS[1], String))
records = Any[]
for pair in catalogue["pairs"], component in pair["components"]
  g = component["gram"]
  c = k3_certificate(g)
  w = c.witness
  witness =
    w === nothing ? nothing :
    Dict(
      "discriminant" => BigInt(w.discriminant),
      "vector" => HassettLattices.json_value(w.vector),
      "gram" => HassettLattices.json_value(w.gram),
      "admissible" => w.admissible,
    )
  push!(
    records,
    Dict(
      "id" => component["id"],
      "gram" => g,
      "certificate" => Dict(
        "association" => HassettLattices.k3_dict(c.association),
        "witness" => witness,
        "search_bound" => BigInt(c.search_bound),
      ),
    ),
  )
end
mkpath(dirname(abspath(ARGS[2])))
write(ARGS[2], JSON.json(records))
println("Exported $(length(records)) native Julia K3 certificates.")
