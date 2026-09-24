from dataclasses import dataclass


@dataclass
class FrameOrder:
    """
    Jedna pozycja zamówienia na moskitiery.
    """

    name: str
    length_mm: float
    height_mm: float
    quantity: int

    reduction_mm: float = 52.0

    has_drip_cap: bool = False
    drip_cap_reduction_mm: float = 15.0