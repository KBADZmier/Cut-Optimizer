from typing import List, Optional
from ortools.sat.python import cp_model
from config.settings import CuttingSettings
from models.cutting import (
    Cut,
    CuttingPlan,
    PlacedCut,
)
from models.profile import StockProfile


class OrToolsOptimizer:
    """
    
    1. wykonać wszystkie elementy,
    2. minimalizować rzeczywisty odpad,
    3. minimalizować liczbę wykorzystanych profili,
    4. minimalizować całkowitą pozostałość materiału,
    5. preferować krótsze profile, jeżeli wcześniejsze
       kryteria są takie same.

    """

    def __init__(
        self,
        settings: CuttingSettings,
    ):
        self.settings = settings

    def optimize(
        self,
        cuts: List[Cut],
        profiles: List[StockProfile],
    ) -> List[CuttingPlan]:

        if not cuts:
            return []

        if not profiles:
            raise ValueError(
                "Brak dostępnych profili."
            )

        self._validate_profiles(
            profiles
        )

        scale = 10

        cut_lengths = [
            int(round(cut.length_mm * scale))
            for cut in cuts
        ]

        profile_lengths = [
            int(round(profile.length_mm * scale))
            for profile in profiles
        ]

        start_margin = int(
            round(self.settings.start_margin_mm * scale)
        )
        end_margin = int(
            round(self.settings.end_margin_mm * scale)
        )
        kerf = int(
            round(self.settings.kerf_mm * scale)
        )
        min_reusable_offcut = int(
            round(self.settings.min_reusable_offcut_mm * scale)
        )

        usable_lengths = [
            profile_length - start_margin - end_margin
            for profile_length in profile_lengths
        ]

        for profile, usable in zip(profiles, usable_lengths):
            if usable <= 0:
                raise ValueError(
                    f"Profil {profile.id} ({profile.length_mm:.1f} mm) "
                    "jest za krótki względem sumy marginesów "
                    f"({self.settings.start_margin_mm:.1f} mm + "
                    f"{self.settings.end_margin_mm:.1f} mm)."
                )

        model = cp_model.CpModel()


        assignment = {}

        for cut_index in range(len(cuts)):
            for profile_index in range(len(profiles)):
                if cut_lengths[cut_index] <= usable_lengths[profile_index]:
                    assignment[cut_index, profile_index] = model.NewBoolVar(
                        f"cut_{cut_index}_profile_{profile_index}"
                    )

        for cut_index in range(len(cuts)):
            possible_profiles = [
                assignment[cut_index, profile_index]
                for profile_index in range(len(profiles))
                if (cut_index, profile_index) in assignment
            ]

            if not possible_profiles:
                raise ValueError(
                    "Brak profilu dla elementu "
                    f"{cuts[cut_index].length_mm:.1f} mm."
                )

            model.AddExactlyOne(possible_profiles)


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


        cut_count = []

        for profile_index in range(len(profiles)):
            variable = model.NewIntVar(0, len(cuts), f"cut_count_{profile_index}")
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


        material_length = []

        for profile_index in range(len(profiles)):
            variable = model.NewIntVar(
                0,
                usable_lengths[profile_index],
                f"material_length_{profile_index}",
            )
            material_length.append(variable)

            expression = sum(
                cut_lengths[cut_index] * assignment[cut_index, profile_index]
                for cut_index in range(len(cuts))
                if (cut_index, profile_index) in assignment
            )

            model.Add(variable == expression)

        remaining = []

        for profile_index in range(len(profiles)):
            variable = model.NewIntVar(
                0,
                usable_lengths[profile_index],
                f"remaining_{profile_index}",
            )
            remaining.append(variable)

            kerf_expression = (
                kerf * cut_count[profile_index]
                - kerf * profile_used[profile_index]
            )

            model.Add(
                variable
                == (
                    usable_lengths[profile_index] * profile_used[profile_index]
                    - material_length[profile_index]
                    - kerf_expression
                )
            )


        waste = []

        for profile_index in range(len(profiles)):
            waste_variable = model.NewIntVar(
                0,
                usable_lengths[profile_index],
                f"waste_{profile_index}",
            )
            waste.append(waste_variable)

            reusable = model.NewBoolVar(f"reusable_{profile_index}")

            model.Add(reusable <= profile_used[profile_index])

            model.Add(
                remaining[profile_index] >= min_reusable_offcut * reusable
            )

            model.Add(
                remaining[profile_index]
                <= (min_reusable_offcut - 1)
                + (usable_lengths[profile_index] * reusable)
            )

            model.Add(
                waste_variable
                <= usable_lengths[profile_index] * (1 - reusable)
            )

            model.Add(
                waste_variable
                >= remaining[profile_index]
                - (usable_lengths[profile_index] * reusable)
            )

            model.Add(waste_variable <= remaining[profile_index])

        # FUNKCJA CELU 
        # 1. MINIMALNY ODPAD
        # 2. MINIMALNA LICZBA PROFILI
        # 3. MINIMALNA CAŁKOWITA POZOSTAŁOŚĆ
        # 4. MINIMALNA DŁUGOŚĆ WYKORZYSTANYCH PROFILI
        #

        total_waste = sum(waste)
        total_profiles = sum(profile_used)
        total_remaining = sum(remaining)
        total_profile_length = sum(
            profile_lengths[index] * profile_used[index]
            for index in range(len(profiles))
        )

        total_time_budget = 120.0
        stage_time_budget = total_time_budget / 4.0

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 8

        def solve_stage(objective_expression, stage_name: str) -> int:
            model.Minimize(objective_expression)
            solver.parameters.max_time_in_seconds = stage_time_budget

            status = solver.Solve(model)

            if status == cp_model.INFEASIBLE:
                raise ValueError(
                    "OR-Tools potwierdził, że problem jest niewykonalny "
                    f"(etap: {stage_name})."
                )

            if status == cp_model.MODEL_INVALID:
                raise ValueError(
                    f"OR-Tools zgłosił nieprawidłowy model (etap: {stage_name}). "
                    f"Szczegóły walidacji: {model.Validate()}"
                )

            if status == cp_model.UNKNOWN:
                raise ValueError(
                    "OR-Tools nie zakończył obliczeń w wyznaczonym czasie "
                    f"(etap: {stage_name}). Limit: {stage_time_budget:.1f} s."
                )

            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                raise ValueError(
                    f"Nieoczekiwany status OR-Tools: {status} (etap: {stage_name})"
                )

            return solver.Value(objective_expression)

        # Etap 1: minimalny odpad.
        best_waste = solve_stage(total_waste, "minimalny odpad")
        model.Add(total_waste == best_waste)

        # Etap 2: minimalna liczba profili, przy zachowaniu odpadu z etapu 1.
        best_profiles = solve_stage(total_profiles, "minimalna liczba profili")
        model.Add(total_profiles == best_profiles)

        # Etap 3: minimalna całkowita pozostałość, przy zachowaniu etapów 1-2.
        best_remaining = solve_stage(
            total_remaining, "minimalna całkowita pozostałość"
        )
        model.Add(total_remaining == best_remaining)

        # Etap 4: minimalna długość wykorzystanych profili (preferuj krótsze).
        solve_stage(total_profile_length, "minimalna długość profili")

   

        plans = []

        for profile_index, profile in enumerate(profiles):

            if solver.Value(profile_used[profile_index]) == 0:
                continue

            assigned_cuts = []

            for cut_index, cut in enumerate(cuts):
                variable = assignment.get((cut_index, profile_index))

                if variable is None:
                    continue

                if solver.Value(variable) == 1:
                    assigned_cuts.append(cut)

        
            assigned_cuts.sort(
                key=lambda cut: (-cut.length_mm, cut.id)
            )

            placed_cuts = []
            current_position = self.settings.start_margin_mm

            for index, cut in enumerate(assigned_cuts):
                if index > 0:
                    current_position += self.settings.kerf_mm

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

           

            usable_length_scaled = usable_lengths[profile_index]
            material_length_scaled = solver.Value(material_length[profile_index])
            remaining_scaled = solver.Value(remaining[profile_index])
            waste_scaled = solver.Value(waste[profile_index])

            usable_length = usable_length_scaled / scale
            used_length = (usable_length_scaled - remaining_scaled) / scale
            remaining_mm = remaining_scaled / scale
            waste_mm = waste_scaled / scale
            reusable = waste_scaled == 0 and remaining_scaled > 0

            plans.append(
                CuttingPlan(
                    profile_id=profile.id,
                    profile_length_mm=profile.length_mm,
                    cuts=placed_cuts,
                    usable_length_mm=round(usable_length, 1),
                    used_length_mm=round(used_length, 1),
                    remaining_mm=round(remaining_mm, 1),
                    reusable_offcut=reusable,
                    waste_mm=round(waste_mm, 1),
                )
            )

        return plans

    @staticmethod
    def _validate_profiles(
        profiles: List[StockProfile],
    ) -> None:

        ids = [profile.id for profile in profiles]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Id profili muszą być unikalne."
            )

        for profile in profiles:
            if profile.length_mm <= 0:
                raise ValueError(
                    f"Profil {profile.id} "
                    f"musi mieć długość większą od 0."
                )