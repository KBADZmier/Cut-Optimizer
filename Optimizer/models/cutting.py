from dataclasses import dataclass
from typing import List

from .order import FrameOrder


@dataclass
class Cut:
    """
    Pojedynczy element, który trzeba wyciąć.
    """

    id: int
    frame_name: str
    side: str
    length_mm: float


@dataclass
class PlacedCut:
    """
    Element umieszczony na konkretnym profilu.
    """

    cut: Cut
    start_mm: float
    end_mm: float


@dataclass
class CuttingPlan:
    """
    Plan cięcia jednego profilu.
    """

    profile_id: str
    profile_length_mm: float

    cuts: List[PlacedCut]

    usable_length_mm: float
    used_length_mm: float
    remaining_mm: float

    reusable_offcut: bool
    waste_mm: float