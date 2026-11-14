using HassettLattices

directory = isempty(ARGS) ? "hassett-catalogue" : only(ARGS)
index = build_catalogue(
  directory,
  42;
  limits = Limits(; timeout_seconds = 180.0),
  progress = i -> println(i["pair_count"], "/", i["expected_pair_count"]),
)
@assert index["complete"]
