using HassettLattices

result = intersection_components(12, 20)
@assert verify_result(result; classification = true)
for component in result
  println(component)
  println(gram_matrix(component))
  println("K3 admissible: ", component.k3_association.admissible)
  println("Construction indices: ", [o.index for o in origins(component)])
end
println("Markings of the first component through 100:")
for marking in primitive_markings(result[1], 100)
  println(marking.discriminant, ": ", marking.vector)
end
