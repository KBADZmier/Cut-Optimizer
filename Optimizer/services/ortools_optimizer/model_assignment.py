
from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
from models.cutting import Cut
from models.profile import StockProfile
from .types import ScaledInputs


def add_assignment_variables(
    model: cp_model.CpModel,
    cuts: List[Cut],
    profiles: List[StockProfile],
    scaled: ScaledInputs,
) -> Dict[Tuple[int, int], cp_model.IntVar]:

    assignment: Dict[Tuple[int, int], cp_model.IntVar] = {}

    for cut_index in range(len(cuts)):
        for profile_index in range(len(profiles)):
            fits_length = (
                scaled.cut_lengths[cut_index]
                <= scaled.usable_lengths[profile_index]
            )
            matches_color = (
                cuts[cut_index].color == profiles[profile_index].color
            )

            if fits_length and matches_color:
                assignment[cut_index, profile_index] = model.NewBoolVar(
                    f"cut_{cut_index}_profile_{profile_index}"
                )

    return assignment


def add_exactly_one_constraints(
    model: cp_model.CpModel,
    cuts: List[Cut],
    assignment: Dict[Tuple[int, int], cp_model.IntVar],
) -> None:
    """Każdy element musi trafić na dokładnie jeden profil."""

    for cut_index in range(len(cuts)):
        possible_profiles = [
            variable
            for (c_idx, _p_idx), variable in assignment.items()
            if c_idx == cut_index
        ]

        if not possible_profiles:
            raise ValueError(
                "Brak profilu dla elementu "
                f"{cuts[cut_index].length_mm:.1f} mm "
                f"w kolorze '{cuts[cut_index].color}'."
            )

        model.AddExactlyOne(possible_profiles)