
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model


@dataclass(frozen=True)
class ScaledInputs:

    cut_lengths: List[int]
    profile_lengths: List[int]
    usable_lengths: List[int]
    start_margin: int
    end_margin: int
    kerf: int
    min_reusable_offcut: int


@dataclass
class ModelVariables:

    assignment: Dict[Tuple[int, int], cp_model.IntVar]
    profile_used: List[cp_model.IntVar]
    cut_count: List[cp_model.IntVar]
    material_length: List[cp_model.IntVar]
    remaining: List[cp_model.IntVar]
    waste: List[cp_model.IntVar]