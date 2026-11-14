"""Exact rank-three Hassett-divisor intersection computations.

The implementation follows Algorithm 7.6 of Song Yang and Xun Yu,
*On lattice polarizable cubic fourfolds*, arXiv:2103.09132.
"""

from .core import (
    Limits,
    ResourceLimitError,
    admissible_discriminant,
    determinant,
    h_fixed_isometry,
    intersection_components,
    lattice_k3_association,
    primitive_markings,
    k3_witness,
    k3_certificate,
    norm_two_vector,
    valid_discriminant,
)

__version__ = "1.1.0"

__all__ = [
    "Limits", "ResourceLimitError", "admissible_discriminant", "determinant",
    "h_fixed_isometry", "intersection_components", "lattice_k3_association",
    "norm_two_vector", "valid_discriminant",
    "primitive_markings", "k3_witness", "k3_certificate",
]
