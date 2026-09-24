from typing import List

from config.settings import CuttingSettings
from models.cutting import (
    Cut,
    CuttingPlan,
    PlacedCut,
)
from models.profile import StockProfile


def usable_profile_length(
    profile: StockProfile,
    settings: CuttingSettings,
) -> float:

    return (
        profile.length_mm
        - settings.start_margin_mm
        - settings.end_margin_mm
    )


def can_fit(
    plan: CuttingPlan,
    cut: Cut,
    settings: CuttingSettings,
) -> bool:

    additional_length = cut.length_mm

    if plan.cuts:
        additional_length += settings.kerf_mm

    return (
        plan.used_length_mm
        + additional_length
        <= plan.usable_length_mm
    )


def add_cut(
    plan: CuttingPlan,
    cut: Cut,
    settings: CuttingSettings,
) -> None:

    if not plan.cuts:

        start = settings.start_margin_mm

    else:

        start = (
            settings.start_margin_mm
            + plan.used_length_mm
            + settings.kerf_mm
        )

    end = start + cut.length_mm

    plan.cuts.append(
        PlacedCut(
            cut=cut,
            start_mm=round(start, 1),
            end_mm=round(end, 1),
        )
    )

    if plan.cuts and len(plan.cuts) == 1:

        plan.used_length_mm += cut.length_mm

    else:

        plan.used_length_mm += (
            settings.kerf_mm
            + cut.length_mm
        )


def update_plan(
    plan: CuttingPlan,
    settings: CuttingSettings,
) -> None:

    plan.remaining_mm = round(
        plan.usable_length_mm
        - plan.used_length_mm,
        1,
    )

    if (
        plan.remaining_mm
        >= settings.min_reusable_offcut_mm
    ):

        plan.reusable_offcut = True
        plan.waste_mm = 0.0

    else:

        plan.reusable_offcut = False
        plan.waste_mm = max(
            0.0,
            plan.remaining_mm,
        )


def optimize(
    cuts: List[Cut],
    profiles: List[StockProfile],
    settings: CuttingSettings,
) -> List[CuttingPlan]:

    # Najpierw najdłuższe elementy.
    sorted_cuts = sorted(
        cuts,
        key=lambda cut: cut.length_mm,
        reverse=True,
    )

    # Krótsze profile pierwsze.
    sorted_profiles = sorted(
        profiles,
        key=lambda profile: profile.length_mm,
    )

    plans: List[CuttingPlan] = []

    for cut in sorted_cuts:

        best_plan = None
        best_remaining = float("inf")

        # Próbujemy umieścić element
        # w już rozpoczętym profilu.
        for plan in plans:

            if not can_fit(
                plan,
                cut,
                settings,
            ):
                continue

            additional = cut.length_mm

            if plan.cuts:
                additional += settings.kerf_mm

            remaining = (
                plan.usable_length_mm
                - plan.used_length_mm
                - additional
            )

            if remaining < best_remaining:

                best_remaining = remaining
                best_plan = plan

        if best_plan is not None:

            add_cut(
                best_plan,
                cut,
                settings,
            )

            continue

        # Otwieramy nowy profil.
        selected_profile = None

        for profile in sorted_profiles:

            if any(
                plan.profile_id == profile.id
                for plan in plans
            ):
                continue

            usable = usable_profile_length(
                profile,
                settings,
            )

            if cut.length_mm <= usable:

                selected_profile = profile
                break

        if selected_profile is None:

            raise ValueError(
                f"Brak profilu dla elementu "
                f"{cut.length_mm} mm."
            )

        new_plan = CuttingPlan(
            profile_id=selected_profile.id,
            profile_length_mm=selected_profile.length_mm,
            cuts=[],
            usable_length_mm=usable_profile_length(
                selected_profile,
                settings,
            ),
            used_length_mm=0.0,
            remaining_mm=0.0,
            reusable_offcut=False,
            waste_mm=0.0,
        )

        add_cut(
            new_plan,
            cut,
            settings,
        )

        plans.append(new_plan)

    for plan in plans:
        update_plan(
            plan,
            settings,
        )

    return plans