from typing import List

from ortools.sat.python import cp_model

from config.settings import CuttingSettings
from models.cutting import Cut, CuttingPlan, PlacedCut
from models.profile import StockProfile


class OrToolsOptimizer:


    def __init__(self, settings: CuttingSettings):
        self.settings = settings

    def optimize(
        self,
        cuts: List[Cut],
        profiles: List[StockProfile],
    ) -> List[CuttingPlan]:

        if not cuts:
            return []

        if not profiles:
            raise ValueError("Brak dostępnych profili.")

        model = cp_model.CpModel()

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

        min_offcut = int(
            round(self.settings.min_reusable_offcut_mm * scale)
        )

        usable_lengths = [
            length - start_margin - end_margin
            for length in profile_lengths
        ]

        # --------------------------------------------------
        # ZMIENNE
        # --------------------------------------------------

        # assignment[c, p] = 1,
        # jeżeli element c znajduje się na profilu p.
        assignment = {}

        for c in range(len(cuts)):
            for p in range(len(profiles)):

                if cut_lengths[c] <= usable_lengths[p]:
                    assignment[c, p] = model.NewBoolVar(
                        f"cut_{c}_profile_{p}"
                    )

        # Każdy element musi zostać przydzielony dokładnie
        # do jednego profilu.
        for c in range(len(cuts)):

            possible_profiles = [
                assignment[c, p]
                for p in range(len(profiles))
                if (c, p) in assignment
            ]

            if not possible_profiles:
                raise ValueError(
                    f"Element {cuts[c].length_mm} mm "
                    f"nie mieści się na żadnym profilu."
                )

            model.AddExactlyOne(possible_profiles)

        # --------------------------------------------------
        # CZY PROFIL JEST UŻYTY
        # --------------------------------------------------

        profile_used = []

        for p in range(len(profiles)):

            variable = model.NewBoolVar(
                f"profile_used_{p}"
            )

            profile_used.append(variable)

            assigned_cuts = [
                assignment[c, p]
                for c in range(len(cuts))
                if (c, p) in assignment
            ]

            if assigned_cuts:
                model.AddMaxEquality(
                    variable,
                    assigned_cuts,
                )
            else:
                model.Add(variable == 0)

        # --------------------------------------------------
        # KOLEJNOŚĆ ELEMENTÓW NA PROFILU
        # --------------------------------------------------

        # position[c] określa kolejność elementu
        # w obrębie jego profilu.
        #
        # Dzięki temu możemy policzyć rzazy.

        positions = {}

        max_position = len(cuts)

        for c in range(len(cuts)):

            positions[c] = model.NewIntVar(
                0,
                max_position - 1,
                f"position_{c}",
            )

        # Elementy przypisane do tego samego profilu
        # muszą mieć różne pozycje.
        for p in range(len(profiles)):

            for c1 in range(len(cuts)):
                for c2 in range(c1 + 1, len(cuts)):

                    if (
                        (c1, p) not in assignment
                        or (c2, p) not in assignment
                    ):
                        continue

                    same_profile = model.NewBoolVar(
                        f"same_{c1}_{c2}_{p}"
                    )

                    model.AddBoolAnd(
                        [
                            assignment[c1, p],
                            assignment[c2, p],
                        ]
                    ).OnlyEnforceIf(same_profile)

                    model.AddBoolOr(
                        [
                            assignment[c1, p].Not(),
                            assignment[c2, p].Not(),
                        ]
                    ).OnlyEnforceIf(
                        same_profile.Not()
                    )

                    model.Add(
                        positions[c1] != positions[c2]
                    ).OnlyEnforceIf(same_profile)

        # --------------------------------------------------
        # ZUŻYCIE PROFILI
        # --------------------------------------------------

        used_length = []

        for p in range(len(profiles)):

            max_length = usable_lengths[p]

            variable = model.NewIntVar(
                0,
                max_length,
                f"used_length_{p}",
            )

            used_length.append(variable)

            # Suma długości elementów.
            model.Add(
                variable
                >= sum(
                    cut_lengths[c] * assignment[c, p]
                    for c in range(len(cuts))
                    if (c, p) in assignment
                )
            )

        # --------------------------------------------------
        # ODPAD / POZOSTAŁOŚĆ
        # --------------------------------------------------

        remaining = []

        for p in range(len(profiles)):

            variable = model.NewIntVar(
                0,
                usable_lengths[p],
                f"remaining_{p}",
            )

            remaining.append(variable)

            model.Add(
                variable
                == usable_lengths[p] - used_length[p]
            )

        # --------------------------------------------------
        # FUNKCJA CELU
        # --------------------------------------------------

        # Priorytet 1:
        # minimalna liczba użytych profili.
        #
        # Priorytet 2:
        # minimalna suma pozostałości.
        #
        # Profilów będzie maksymalnie kilkanaście,
        # więc bardzo duża waga pozwala zachować
        # kolejność priorytetów.

        total_profiles = sum(profile_used)

        total_remaining = sum(remaining)

        model.Minimize(
            total_profiles * 1_000_000
            + total_remaining
        )

        # --------------------------------------------------
        # SOLVER
        # --------------------------------------------------

        solver = cp_model.CpSolver()

        solver.parameters.max_time_in_seconds = 10.0

        solver.parameters.num_search_workers = 8

        status = solver.Solve(model)

        if status not in (
            cp_model.OPTIMAL,
            cp_model.FEASIBLE,
        ):
            raise ValueError(
                "OR-Tools nie znalazł rozwiązania."
            )

        # --------------------------------------------------
        # ODCZYT ROZWIĄZANIA
        # --------------------------------------------------

        plans: List[CuttingPlan] = []

        for p, profile in enumerate(profiles):

            if solver.Value(profile_used[p]) == 0:
                continue

            assigned = []

            for c, cut in enumerate(cuts):

                if (c, p) not in assignment:
                    continue

                if solver.Value(
                    assignment[c, p]
                ) == 0:
                    continue

                assigned.append(c)

            # Sortowanie według pozycji.
            assigned.sort(
                key=lambda c: solver.Value(
                    positions[c]
                )
            )

            placed_cuts = []

            current_position = (
                self.settings.start_margin_mm
            )

            for index in assigned:

                cut = cuts[index]

                if placed_cuts:

                    current_position += (
                        self.settings.kerf_mm
                    )

                start = current_position

                end = (
                    start
                    + cut.length_mm
                )

                placed_cuts.append(
                    PlacedCut(
                        cut=cut,
                        start_mm=round(
                            start,
                            1,
                        ),
                        end_mm=round(
                            end,
                            1,
                        ),
                    )
                )

                current_position = end

            used_mm = (
                current_position
                - self.settings.start_margin_mm
            )

            usable_mm = (
                profile.length_mm
                - self.settings.start_margin_mm
                - self.settings.end_margin_mm
            )

            remaining_mm = max(
                0.0,
                usable_mm - used_mm,
            )

            reusable = (
                remaining_mm
                >= self.settings.min_reusable_offcut_mm
            )

            waste_mm = (
                0.0
                if reusable
                else remaining_mm
            )

            plans.append(
                CuttingPlan(
                    profile_id=profile.id,
                    profile_length_mm=profile.length_mm,
                    cuts=placed_cuts,
                    usable_length_mm=round(
                        usable_mm,
                        1,
                    ),
                    used_length_mm=round(
                        used_mm,
                        1,
                    ),
                    remaining_mm=round(
                        remaining_mm,
                        1,
                    ),
                    reusable_offcut=reusable,
                    waste_mm=round(
                        waste_mm,
                        1,
                    ),
                )
            )

        return plans