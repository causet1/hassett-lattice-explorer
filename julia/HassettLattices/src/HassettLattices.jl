module HassettLattices

import ArgParse
import CodecZlib
import Dates
import Hecke
import JSON
import Nemo
import SHA
import Hecke: discriminant, gram_matrix, rank

using Nemo: ZZ, QQ, ZZRingElem, ZZMatrix, divexact

export Limits, ResourceLimitError, VerificationError
export MarkedLattice, K3Association, ConstructionOrigin, Component
export Candidate, IntersectionResult, LabelEmbedding
export valid_discriminant, valid_discriminants, admissible_discriminant
export normalize_pair, positive_parameters, base_gram, saturation_indices
export saturation_residues, intersection_components, component_count
export components, origins, gram_matrix, discriminant, rank
export hecke_lattice, change_basis, norm_two_vector, h_fixed_isometry
export lattice_k3_association, primitive_markings, k3_witness
export lattice_invariants, verify_result, result_dict, read_result, write_result
export build_catalogue, catalogue_summary, main

include("types.jl")
include("arithmetic.jl")
include("lattices.jl")
include("intersection.jl")
include("certificates.jl")
include("catalogue.jl")
include("cli.jl")

end
