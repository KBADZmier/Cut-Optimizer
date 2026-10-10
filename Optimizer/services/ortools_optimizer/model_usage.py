from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
from models.cutting import Cut
from models.profile import StockProfile


def add_profile_used_variables(
    model: cp_model.CpModel,
    cuts: List[Cut],
    profiles: List[StockProfile],
    assignment: Dict[Tuple[int, int], cp_model.IntVar],
) -> List[cp_model.IntVar]:
    profile_used = []

    for profile_index in range(len(profiles)):
        variable = model.NewBoolVar(f"profile_used_{profile_index}")
        profile_used.append(variable)

        assigned = [
            assignment[cut_index, profile_index]
            for cut_index in range(len(cuts))
            if (cut_index, profile_index) in assignment
        ]

        if assigned:
            model.AddMaxEquality(variable, assigned)
        else:
            model.Add(variable == 0)

    return profile_used


def add_cut_count_variables(
    model: cp_model.CpModel,
    cuts: List[Cut],
    profiles: List[StockProfile],
    assignment: Dict[Tuple[int, int], cp_model.IntVar],
) -> List[cp_model.IntVar]:
    cut_count = []

    for profile_index in range(len(profiles)):
        variable = model.NewIntVar(
            0, len(cuts), f"cut_count_{profile_index}"
        )
        cut_count.append(variable)

        assigned = [
            assignment[cut_index, profile_index]
            for cut_index in range(len(cuts))
            if (cut_index, profile_index) in assignment
        ]

        if assigned:
            model.Add(variable == sum(assigned))
        else:
            model.Add(variable == 0)

    return cut_count