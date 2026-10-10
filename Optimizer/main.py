from config.settings import CuttingSettings
from services.cut_generator import generate_cuts
from services.ortools_optimizer import OrToolsOptimizer
from tests.test_frame import orders
from tests.test_profile import profiles
from services.profile_inventory import (
    apply_plans_to_inventory, generate_standard_profiles,
    load_profiles_from_json, save_profiles_to_json,
)
def main():


   

    settings = CuttingSettings(
        start_margin_mm=100,
        end_margin_mm=20,
        kerf_mm=3,
        min_reusable_offcut_mm=400,
    )

    cuts = generate_cuts(orders)

    optimizer = OrToolsOptimizer(settings)

    plans = optimizer.optimize(
        cuts=cuts,
        profiles=profiles,
    )

    lines = []

    lines.append("ELEMENTY DO WYCIĘCIA:")
    lines.append("")

    for cut in cuts:
        lines.append(
            f"{cut.id:02d} | "
            f"{cut.frame_name} | "
            f"{cut.side:10} | "
            f"{cut.length_mm:.1f} mm"
        )

    lines.append("")
    lines.append("=" * 70)
    lines.append("PLAN CIĘCIA")
    lines.append("=" * 70)

    for plan in plans:

        lines.append("")
        lines.append(
            f"{plan.profile_id} "
            f"({plan.profile_length_mm:.0f} mm)"
        )

        for placed in plan.cuts:
            lines.append(
                f"  {placed.cut.length_mm:7.1f} mm "
                f"| {placed.cut.frame_name} "
                f"| {placed.cut.side:10} "
                f"| {placed.start_mm:7.1f}"
                f" - {placed.end_mm:7.1f}"
            )

        lines.append(
            f"  Zużyto:      "
            f"{plan.used_length_mm:.1f} mm"
        )
        lines.append(
            f"  Pozostałość: "
            f"{plan.remaining_mm:.1f} mm"
        )

        if plan.reusable_offcut:
            lines.append("  → RESZTKA")
        else:
            lines.append("  → ODPAD")

    # --- Zapis do pliku ---
    output_file = "wynik.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

        #magazyn save
    PATH = "Profiles/profiles_data.json"

    inventory = load_profiles_from_json(PATH)
    inventory_ids = {p.id for p in inventory}
    standard = generate_standard_profiles(quantity=40, color="orzech", length_mm=5000.0)
    all_profiles = standard + inventory

    plans = optimizer.optimize(cuts, all_profiles)

    inventory = apply_plans_to_inventory(all_profiles, plans, inventory_ids)
    save_profiles_to_json(PATH, inventory)
    
    # --- Wypisanie w konsoli ---
    print("\n".join(lines))
    print()
    print(f"Wynik zapisano do pliku: {output_file}")


if __name__ == "__main__":
    main()