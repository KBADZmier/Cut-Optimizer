"""Pozostałość materiału na profilu.

Profil użytkowy:  długość profilu - margines początku - margines końca
Zużycie:          długość elementów + rzazy pomiędzy elementami
"""

from typing import List

from ortools.sat.python import cp_model

from models.profile import StockProfile

from .types import ScaledInputs


def add_remaining_variables(
    model: cp_model.CpModel,
    profiles: List[StockProfile],
    scaled: ScaledInputs,
    profile_used: List[cp_model.IntVar],
    cut_count: List[cp_model.IntVar],
    material_length: List[cp_model.IntVar],
) -> List[cp_model.IntVar]:
    remaining = []

    for profile_index in range(len(profiles)):
        variable = model.NewIntVar(
            0,
            scaled.usable_lengths[profile_index],
            f"remaining_{profile_index}",
        )
        remaining.append(variable)

        # Liczba rzazów pomiędzy elementami: N elementów -> N - 1 rzazów.
        kerf_expression = (
            scaled.kerf * cut_count[profile_index]
            - scaled.kerf * profile_used[profile_index]
        )

        model.Add(
            variable
            == (
                scaled.usable_lengths[profile_index]
                * profile_used[profile_index]
                - material_length[profile_index]
                - kerf_expression
            )
        )

    return remaining