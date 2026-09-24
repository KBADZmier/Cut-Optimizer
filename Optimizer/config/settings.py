from dataclasses import dataclass


@dataclass
class CuttingSettings:
    """
    Parametry technologiczne cięcia.
    """

    start_margin_mm: float = 100.0
    end_margin_mm: float = 20.0

    kerf_mm: float = 3.0

    min_reusable_offcut_mm: float = 150.0