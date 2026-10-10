from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
from config.settings import CuttingSettings
from models.cutting import Cut, CuttingPlan, PlacedCut
from models.profile import StockProfile
from .constants import SCALE
from .types import ModelVariables, ScaledInputs


def extract_plans(
    settings: CuttingSettings,
    cuts: List[Cut],
    profiles: List[StockProfile],
    scaled: ScaledInputs,
    solver: cp_model.CpSolver,
    variables: ModelVariables,
) -> List[CuttingPlan]:
    plans = []

    for profile_index, profile in enumerate(profiles):
        if solver.Value(variables.profile_used[profile_index]) == 0:
            continue

        assigned_cuts = _extract_assigned_cuts(
            cuts, profile_index, solver, variables.assignment
        )

        placed_cuts = _order_and_place_cuts(settings, assigned_cuts)

        plans.append(
            _build_plan(
                profile, profile_index, placed_cuts, scaled, solver, variables
            )
        )

    return plans


def _extract_assigned_cuts(
    cuts: List[Cut],
    profile_index: int,
    solver: cp_model.CpSolver,
    assignment: Dict[Tuple[int, int], cp_model.IntVar],
) -> List[Cut]:
    assigned_cuts = []

    for cut_index, cut in enumerate(cuts):
        variable = assignment.get((cut_index, profile_index))

        if variable is None:
            continue

        if solver.Value(variable) == 1:
            assigned_cuts.append(cut)

    return assigned_cuts


def _order_and_place_cuts(
    settings: CuttingSettings,
    assigned_cuts: List[Cut],
) -> List[PlacedCut]:

    assigned_cuts = sorted(
        assigned_cuts, key=lambda cut: (-cut.length_mm, cut.id)
    )

    placed_cuts = []
    current_position = settings.start_margin_mm

    for index, cut in enumerate(assigned_cuts):
        if index > 0:
            current_position += settings.kerf_mm

        start = current_position
        end = start + cut.length_mm

        placed_cuts.append(
            PlacedCut(
                cut=cut,
                start_mm=round(start, 1),
                end_mm=round(end, 1),
            )
        )

        current_position = end

    return placed_cuts


def _build_plan(
    profile: StockProfile,
    profile_index: int,
    placed_cuts: List[PlacedCut],
    scaled: ScaledInputs,
    solver: cp_model.CpSolver,
    variables: ModelVariables,
) -> CuttingPlan:

    usable_length_scaled = scaled.usable_lengths[profile_index]
    remaining_scaled = solver.Value(variables.remaining[profile_index])
    waste_scaled = solver.Value(variables.waste[profile_index])

    usable_length = usable_length_scaled / SCALE
    used_length = (usable_length_scaled - remaining_scaled) / SCALE
    remaining_mm = remaining_scaled / SCALE
    waste_mm = waste_scaled / SCALE
    reusable = waste_scaled == 0 and remaining_scaled > 0

    return CuttingPlan(
        profile_id=profile.id,
        profile_length_mm=profile.length_mm,
        cuts=placed_cuts,
        usable_length_mm=round(usable_length, 1),
        used_length_mm=round(used_length, 1),
        remaining_mm=round(remaining_mm, 1),
        reusable_offcut=reusable,
        waste_mm=round(waste_mm, 1),
    )