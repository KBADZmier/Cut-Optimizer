"""Optymalizator cięcia profili (OR-Tools CP-SAT).

Publiczne API pakietu -- to jedyne, co powinno być importowane z zewnątrz:

    from services.ortools_optimizer import OrToolsOptimizer

Reszta modułów w tym pakiecie (constants, types, validation, scaling,
model_*, solving, plan_extraction) to szczegóły implementacyjne,
podzielone wg pojedynczej odpowiedzialności każdego etapu:

    types.py             -- struktury danych (ScaledInputs, ModelVariables)
    constants.py          -- stałe konfiguracyjne
    validation.py         -- walidacja danych wejściowych
    scaling.py            -- przeliczenie mm (float) -> int (mm * SCALE)
    model_assignment.py    -- przydział elementów do profili
    model_usage.py         -- czy profil użyty / liczba cięć na profilu
    model_material.py      -- łączna długość elementów na profilu
    model_remaining.py     -- pozostałość materiału
    model_waste.py         -- klasyfikacja odpad / użyteczna resztka
    model_builder.py       -- orkiestracja budowy modelu
    solving.py             -- rozwiązywanie leksykograficzne (3 etapy)
    plan_extraction.py     -- odczyt wyniku z rozwiązanego modelu
    optimizer.py           -- klasa OrToolsOptimizer (punkt wejścia)
"""

from .optimizer import OrToolsOptimizer

__all__ = ["OrToolsOptimizer"]