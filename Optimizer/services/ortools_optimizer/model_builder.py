from typing import List
from ortools.sat.python import cp_model
from models.cutting import Cut
from models.profile import StockProfile
from .model_assignment import add_assignment_variables, add_exactly_one_constraints
from .model_material import add_material_length_variables
from .model_remaining import add_remaining_variables
from .model_symmetry import add_symmetry_breaking_constraints
from .model_usage import add_cut_count_variables, add_profile_used_variables
from .model_waste import add_waste_variables
from .types import ModelVariables, ScaledInputs


def build_model(
    model: cp_model.CpModel,
    cuts: List[Cut],
    profiles: List[StockProfile],
    scaled: ScaledInputs,
) -> ModelVariables:

    assignment = add_assignment_variables(model, cuts, profiles, scaled)
    add_exactly_one_constraints(model, cuts, assignment)

    profile_used = add_profile_used_variables(model, cuts, profiles, assignment)

    add_symmetry_breaking_constraints(model, profiles, scaled, profile_used)

    cut_count = add_cut_count_variables(model, cuts, profiles, assignment)

    material_length = add_material_length_variables(
        model, cuts, profiles, scaled, assignment
    )

    remaining = add_remaining_variables(
        model, profiles, scaled, profile_used, cut_count, material_length
    )

    waste = add_waste_variables(model, profiles, scaled, profile_used, remaining)

    return ModelVariables(
        assignment=assignment,
        profile_used=profile_used,
        cut_count=cut_count,
        material_length=material_length,
        remaining=remaining,
        waste=waste,
    )