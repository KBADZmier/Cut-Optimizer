
from typing import List
from models.profile import StockProfile
from .types import ScaledInputs


def validate_profiles(profiles: List[StockProfile]) -> None:

    ids = [profile.id for profile in profiles]

    if len(ids) != len(set(ids)):
        raise ValueError("Id profili muszą być unikalne.")

    for profile in profiles:
        if profile.length_mm <= 0:
            raise ValueError(
                f"Profil {profile.id} "
                f"musi mieć długość większą od 0."
            )


def validate_usable_lengths(
    profiles: List[StockProfile],
    scaled: ScaledInputs,
) -> None:

    for profile, usable in zip(profiles, scaled.usable_lengths):
        if usable <= 0:
            raise ValueError(
                f"Profil {profile.id} ({profile.length_mm:.1f} mm) "
                "jest za krótki względem sumy marginesów."
            )