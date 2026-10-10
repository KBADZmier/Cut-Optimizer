
from typing import List
from config.settings import CuttingSettings
from models.cutting import Cut
from models.profile import StockProfile
from .constants import SCALE
from .types import ScaledInputs


def scale_inputs(
    settings: CuttingSettings,
    cuts: List[Cut],
    profiles: List[StockProfile],
) -> ScaledInputs:
    cut_lengths = [
        int(round(cut.length_mm * SCALE)) for cut in cuts
    ]

    profile_lengths = [
        int(round(profile.length_mm * SCALE)) for profile in profiles
    ]

    start_margin = int(round(settings.start_margin_mm * SCALE))
    end_margin = int(round(settings.end_margin_mm * SCALE))
    kerf = int(round(settings.kerf_mm * SCALE))
    min_reusable_offcut = int(round(settings.min_reusable_offcut_mm * SCALE))

    usable_lengths = [
        profile_length - start_margin - end_margin
        for profile_length in profile_lengths
    ]

    return ScaledInputs(
        cut_lengths=cut_lengths,
        profile_lengths=profile_lengths,
        usable_lengths=usable_lengths,
        start_margin=start_margin,
        end_margin=end_margin,
        kerf=kerf,
        min_reusable_offcut=min_reusable_offcut,
    )