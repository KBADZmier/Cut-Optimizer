from config.settings import CuttingSettings
from models.order import FrameOrder
from models.profile import StockProfile

from services.cut_generator import generate_cuts
from services.ortools_optimizer import OrToolsOptimizer


def main():

    orders = [
        FrameOrder(
            name="M1",
            length_mm=1500,
            height_mm=900,
            quantity=2,
            reduction_mm=52,
            has_drip_cap=False,
        ),
        FrameOrder(
            name="M2",
            length_mm=1325,
            height_mm=1000,
            quantity=1,
            reduction_mm=52,
            has_drip_cap=False,
        ),
    ]

    profiles = [
        StockProfile("P1", 6000),
        StockProfile("P2", 6000),
        StockProfile("P3", 6000),

        StockProfile("P4", 3000),
        StockProfile("P5", 1600),
    ]

    settings = CuttingSettings(
        start_margin_mm=100,
        end_margin_mm=20,
        kerf_mm=3,
        min_reusable_offcut_mm=150,
    )

    cuts = generate_cuts(orders)

    print("ELEMENTY DO WYCIĘCIA:")
    print()

    for cut in cuts:
        print(
            f"{cut.id:02d} | "
            f"{cut.frame_name} | "
            f"{cut.side:10} | "
            f"{cut.length_mm:.1f} mm"
        )

    optimizer = OrToolsOptimizer(settings)

    plans = optimizer.optimize(
        cuts=cuts,
        profiles=profiles,
    )

    print()
    print("=" * 70)
    print("PLAN CIĘCIA")
    print("=" * 70)

    for plan in plans:

        print()
        print(
            f"{plan.profile_id} "
            f"({plan.profile_length_mm:.0f} mm)"
        )

        for placed in plan.cuts:

            print(
                f"  {placed.cut.length_mm:7.1f} mm "
                f"| {placed.cut.frame_name} "
                f"| {placed.cut.side:10} "
                f"| {placed.start_mm:7.1f}"
                f" - {placed.end_mm:7.1f}"
            )

        print(
            f"  Zużyto:      "
            f"{plan.used_length_mm:.1f} mm"
        )

        print(
            f"  Pozostałość: "
            f"{plan.remaining_mm:.1f} mm"
        )

        if plan.reusable_offcut:
            print("  → RESZTKA")
        else:
            print("  → ODPAD")


if __name__ == "__main__":
    main()