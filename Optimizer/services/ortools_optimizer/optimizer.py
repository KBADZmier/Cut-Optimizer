from typing import List
from ortools.sat.python import cp_model
from config.settings import CuttingSettings
from models.cutting import Cut, CuttingPlan
from models.profile import StockProfile
from .model_builder import build_model
from .plan_extraction import extract_plans
from .scaling import scale_inputs
from .solving import solve_lexicographic
from .validation import validate_profiles, validate_usable_lengths


class OrToolsOptimizer:
    """
    Optymalizator cięcia profili wykorzystujący OR-Tools CP-SAT.

    Priorytety optymalizacji (rozwiązywane LEKSYKOGRAFICZNIE, w trzech
    oddzielnych etapach solvera -- patrz `solving.py`):

    1. wykonać wszystkie elementy,
    2. minimalizować rzeczywisty odpad (co, jako efekt uboczny dowodu
       matematycznego, gwarantuje zero odpadu na KAŻDYM pojedynczym
       profilu, nie tylko w sumie),
    3. minimalizować liczbę wykorzystanych profili,
    4. przy tej samej liczbie profili, preferować krótsze/mniejsze
       (w tym w pierwszej kolejności zużywać resztki z magazynu) --
       to naturalnie realizuje zasadę "nie ładuj mniejszych profili bez
       potrzeby, jeśli same standardowe wystarczą".

    """

    def __init__(self, settings: CuttingSettings):
        self.settings = settings

    def optimize(
        self,
        cuts: List[Cut],
        profiles: List[StockProfile],
    ) -> List[CuttingPlan]:
        """Wyznacza plan cięcia minimalizujący kolejno: odpad, liczbę
        profili, pozostałość materiału i długość wykorzystanych profili."""

        if not cuts:
            return []

        if not profiles:
            raise ValueError("Brak dostępnych profili.")

        validate_profiles(profiles)

        scaled = scale_inputs(self.settings, cuts, profiles)
        validate_usable_lengths(profiles, scaled)

        model = cp_model.CpModel()
        variables = build_model(model, cuts, profiles, scaled)

        solver = solve_lexicographic(model, variables, scaled)

        return extract_plans(
            self.settings, cuts, profiles, scaled, solver, variables
        )