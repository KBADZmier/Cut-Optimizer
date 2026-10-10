from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
from models.cutting import Cut
from models.profile import StockProfile
from .types import ScaledInputs


def add_material_length_variables(
    model: cp_model.CpModel,
    cuts: List[Cut],
    profiles: List[StockProfile],
    scaled: ScaledInputs,
    assignment: Dict[Tuple[int, int], cp_model.IntVar],
) -> List[cp_model.IntVar]:
    material_length = []

    for profile_index in range(len(profiles)):
        variable = model.NewIntVar(
            0,
            scaled.usable_lengths[profile_index],
            f"material_length_{profile_index}",
        )
        material_length.append(variable)

        expression = sum(
            scaled.cut_lengths[cut_index]
            * assignment[cut_index, profile_index]
            for cut_index in range(len(cuts))
            if (cut_index, profile_index) in assignment
        )

        model.Add(variable == expression)

    return material_length