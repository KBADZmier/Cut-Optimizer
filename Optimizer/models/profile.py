from dataclasses import dataclass


@dataclass
class StockProfile:
    """
    Jeden fizyczny profil dostępny do wykorzystania
    w aktualnym zleceniu.
    """

    id: str
    length_mm: float