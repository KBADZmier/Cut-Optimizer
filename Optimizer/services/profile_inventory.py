"""Magazyn NIESTANDARDOWYCH profili
Profile o standardowej długości (domyślnie 5m) NIE są tu przechowywane
Format pliku 

    [
      {"nr": "R1", "dł": 2130.0, "kolor": "bialy"},
      {"nr": "R2", "dł": 1700.0, "kolor": "braz"}
    ]

"""

import json
import re
from pathlib import Path
from typing import List, Set, Union

from models.cutting import CuttingPlan
from models.profile import StockProfile

_FIELD_ID = "nr"
_FIELD_LENGTH = "dł"
_FIELD_COLOR = "kolor"

_OFFCUT_ID_PATTERN = re.compile(r"^R(\d+)$")


def load_profiles_from_json(
    path: Union[str, Path],
    create_if_missing: bool = True,
) -> List[StockProfile]:
   
    path = Path(path)

    if not path.exists():
        if create_if_missing:
            return []
        raise FileNotFoundError(f"Nie znaleziono pliku magazynu: {path}")

    raw_text = path.read_text(encoding="utf-8")

    if not raw_text.strip():

        if create_if_missing:
            return []
        raise ValueError(
            f"Plik magazynu {path} istnieje, ale jest pusty. Wpisz do "
            "niego [] (pusta lista JSON) albo usuń go, żeby został "
            "utworzony od nowa."
        )

    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Plik magazynu {path} zawiera niepoprawny JSON: {error}"
        ) from error

    if not isinstance(raw, list):
        raise ValueError(
            f"Plik magazynu {path} powinien zawierać listę profili "
            "(tablicę JSON w nawiasach []), a zawiera coś innego."
        )

    profiles = []
    for index, entry in enumerate(raw):
        try:
            profiles.append(
                StockProfile(
                    id=str(entry[_FIELD_ID]),
                    length_mm=float(entry[_FIELD_LENGTH]),
                    color=str(entry[_FIELD_COLOR]),
                    is_offcut=True,
                )
            )
        except KeyError as error:
            raise ValueError(
                f"Wpis nr {index} w magazynie {path} nie ma wymaganego "
                f"pola {error}."
            ) from error

    return profiles


def save_profiles_to_json(
    path: Union[str, Path],
    profiles: List[StockProfile],
) -> None:


    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = [
        {
            _FIELD_ID: profile.id,
            _FIELD_LENGTH: profile.length_mm,
            _FIELD_COLOR: profile.color,
        }
        for profile in profiles
    ]

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def generate_standard_profiles(
    quantity: int,
    color: str,
    length_mm: float = 5000.0,
    id_prefix: str = "STD",
) -> List[StockProfile]:


    return [
        StockProfile(
            id=f"{id_prefix}-{color}-{index + 1}",
            length_mm=length_mm,
            color=color,
            is_offcut=False,
        )
        for index in range(quantity)
    ]


def apply_plans_to_inventory(
    all_profiles: List[StockProfile],
    plans: List[CuttingPlan],
    inventory_ids: Set[str],
) -> List[StockProfile]:
   

    plan_by_profile_id = {plan.profile_id: plan for plan in plans}
    next_number = _next_offcut_number(all_profiles)

    updated_profiles: List[StockProfile] = []

    for profile in all_profiles:
        was_in_inventory = profile.id in inventory_ids
        plan = plan_by_profile_id.get(profile.id)

        if plan is None:
            if was_in_inventory:
                
                updated_profiles.append(profile)
            
            continue

        if plan.reusable_offcut:
            updated_profiles.append(
                StockProfile(
                    id=f"R{next_number}",
                    length_mm=plan.remaining_mm,
                    color=profile.color,
                    is_offcut=True,
                )
            )
            next_number += 1
        

    return updated_profiles


def _next_offcut_number(profiles: List[StockProfile]) -> int:
    highest = 0
    for profile in profiles:
        match = _OFFCUT_ID_PATTERN.match(profile.id)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1