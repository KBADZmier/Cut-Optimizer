"""
remaining < min_reusable_offcut  -> odpad
remaining >= min_reusable_offcut -> użyteczna resztka
"""

from typing import List

from ortools.sat.python import cp_model

from models.profile import StockProfile

from .types import ScaledInputs


def add_waste_variables(
    model: cp_model.CpModel,
    profiles: List[StockProfile],
    scaled: ScaledInputs,
    profile_used: List[cp_model.IntVar],
    remaining: List[cp_model.IntVar],
) -> List[cp_model.IntVar]:
    waste = []

    for profile_index in range(len(profiles)):
        waste_variable = model.NewIntVar(
            0,
            scaled.usable_lengths[profile_index],
            f"waste_{profile_index}",
        )
        waste.append(waste_variable)

        reusable = model.NewBoolVar(f"reusable_{profile_index}")
        usable_length = scaled.usable_lengths[profile_index]


        model.Add(reusable <= profile_used[profile_index])

        model.Add(
            remaining[profile_index] >= scaled.min_reusable_offcut * reusable
        )

  
        model.Add(
            remaining[profile_index]
            <= (scaled.min_reusable_offcut - 1) + (usable_length * reusable)
        )


        model.Add(waste_variable <= usable_length * (1 - reusable))


        model.Add(
            waste_variable
            >= remaining[profile_index] - (usable_length * reusable)
        )

        model.Add(waste_variable <= remaining[profile_index])

    return waste