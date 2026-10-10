from collections import defaultdict
from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
from models.profile import StockProfile
from .types import ScaledInputs


def add_symmetry_breaking_constraints(
    model: cp_model.CpModel,
    profiles: List[StockProfile],
    scaled: ScaledInputs,
    profile_used: List[cp_model.IntVar],
) -> None:
    groups: Dict[Tuple[int, str], List[int]] = defaultdict(list)

    for profile_index, profile in enumerate(profiles):
        key = (scaled.profile_lengths[profile_index], profile.color)
        groups[key].append(profile_index)

    for indices in groups.values():
        if len(indices) < 2:
            continue

        for earlier, later in zip(indices, indices[1:]):
            model.Add(profile_used[earlier] >= profile_used[later])