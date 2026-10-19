import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

NOTE_UNIT = "auto"


MIN_PLAUSIBLE_MM = 100.0
MAX_PLAUSIBLE_MM = 4000.0


ASSUME_CM_BELOW = 400.0

LOW_CONFIDENCE_THRESHOLD = 0.80

_LETTERS = "A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż"
_SEP = r"[xX×✕*/\\]"
_NUM = r"\d{2,4}(?:[.,]\d{1,2})?"

_PAIR_RE = re.compile(rf"(?<![\d.,])({_NUM})\s*{_SEP}\s*({_NUM})(?![\d])")
_PAIR_DASH_RE = re.compile(r"(?<![\d.,])(\d{3,4})\s*[-–—]\s*(\d{3,4})(?!\d)")
_PAIR_SPACE_RE = re.compile(r"(?<![\d.,])(\d{3,4})\s+(\d{3,4})(?!\d)")

_QTY_SZT_RE = re.compile(r"(?<!\d)(\d{1,3})\s*(?:szt|sztuk|sz|pcs)\b", re.I)
_QTY_X_RE = re.compile(rf"{_SEP}\s*(\d{{1,2}})(?!\d)")
_QTY_PAREN_RE = re.compile(r"\((\d{1,2})\)")

_NAME_RE = re.compile(rf"^\s*([{_LETTERS}]{{1,3}}\s?\d{{1,3}})(?=[\s:.)\-])")
_ORDINAL_RE = re.compile(r"^\s*(\d{1,2})\s*[.)]\s+(?=\d)")

_THOUSANDS_RE = re.compile(r"(\d)[.,](\d{3})(?!\d)")

_NON_X_LETTERS = "A-WYZa-wyzĄĆĘŁŃÓŚŹŻąćęłńóśźż"
_DIGITISH_TOKEN_RE = re.compile(
    rf"(?<![{_NON_X_LETTERS}])[0-9OolI|]{{3,5}}(?![{_NON_X_LETTERS}])"
)
_CONFUSIONS = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "|": "1"})


_NOT_MARKER_WORDS = {"szt", "sztuk", "sz", "pcs"}


@dataclass
class ParsedLine:
    raw_text: str
    kind: str  # "order" | "marker" | "unparsed" | "ignored"
    confidence: float = 1.0
    name: Optional[str] = None
    length_mm: Optional[float] = None
    height_mm: Optional[float] = None
    quantity: int = 1
    marker_text: str = ""
    warnings: List[str] = field(default_factory=list)

    @property
    def needs_review(self) -> bool:
        return bool(self.warnings)


def _fix_digit_confusions(text: str) -> str:


    def replace(match: "re.Match[str]") -> str:
        token = match.group(0)
        if any(c.isdigit() for c in token):
            return token.translate(_CONFUSIONS)
        return token

    return _DIGITISH_TOKEN_RE.sub(replace, text)


def _to_float(number_text: str) -> float:
    return float(number_text.replace(",", "."))


def _find_dimension_pair(text: str) -> Optional[Tuple[re.Match, str, str]]:
    for pattern in (_PAIR_RE, _PAIR_DASH_RE, _PAIR_SPACE_RE):
        match = pattern.search(text)
        if match:
            return match, match.group(1), match.group(2)
    return None


def _extract_quantity(text: str) -> Tuple[int, str]:

    for pattern in (_QTY_SZT_RE, _QTY_X_RE, _QTY_PAREN_RE):
        match = pattern.search(text)
        if match:
            return int(match.group(1)), text[: match.start()] + " " + text[match.end():]
    return 1, text


def _marker_text(text: str) -> str:

    words = [
        word
        for word in re.findall(rf"[{_LETTERS}]+", text)
        if len(word) >= 2 and word.lower() not in _NOT_MARKER_WORDS
    ]
    return " ".join(words)


def parse_line(raw_text: str, confidence: float = 1.0) -> ParsedLine:

    result = ParsedLine(raw_text=raw_text, kind="ignored", confidence=confidence)

    text = _THOUSANDS_RE.sub(r"\1\2", _fix_digit_confusions(raw_text))

    name: Optional[str] = None
    name_match = _NAME_RE.match(text)
    if name_match:
        name = re.sub(r"\s+", "", name_match.group(1)).upper()
        text = text[name_match.end():]
    else:
        ordinal_match = _ORDINAL_RE.match(text)
        if ordinal_match:
            name = f"Poz{ordinal_match.group(1)}"
            text = text[ordinal_match.end():]

    pair = _find_dimension_pair(text)

    if pair is None:
        if sum(c.isdigit() for c in text) >= 2:
            result.kind = "unparsed"
            result.warnings.append(
                "Nie udało się odczytać wymiarów z tej linii -- wpisz ręcznie."
            )
            return result

        marker = _marker_text(text)
        if marker:
            result.kind = "marker"
            result.marker_text = marker
        return result

    match, first, second = pair
    text_without_pair = text[: match.start()] + " " + text[match.end():]
    quantity, text_rest = _extract_quantity(text_without_pair)

    length_mm = _to_float(first)
    height_mm = _to_float(second)

    result.kind = "order"
    result.name = name
    result.quantity = quantity
    result.marker_text = _marker_text(text_rest)

    if NOTE_UNIT == "cm":
        length_mm *= 10
        height_mm *= 10
    elif NOTE_UNIT == "auto":
        smaller, larger = sorted((length_mm, height_mm))
        if larger < ASSUME_CM_BELOW:
            length_mm *= 10
            height_mm *= 10
            result.warnings.append(
                "Oba wymiary poniżej 400 -- przyjęto centymetry i przeliczono na mm."
            )
        elif smaller < ASSUME_CM_BELOW <= larger:
            result.warnings.append(
                f"Wymiary różnią się rzędem wielkości ({first} i {second}) -- "
                "sprawdź jednostki albo brakujący przecinek."
            )

    result.length_mm = length_mm
    result.height_mm = height_mm

    for label, value in (("Długość", length_mm), ("Wysokość", height_mm)):
        if not MIN_PLAUSIBLE_MM <= value <= MAX_PLAUSIBLE_MM:
            result.warnings.append(
                f"{label} {value:g} mm jest poza typowym zakresem "
                f"{MIN_PLAUSIBLE_MM:g}-{MAX_PLAUSIBLE_MM:g} mm."
            )

    if quantity > 20:
        result.warnings.append(f"Nietypowo duża ilość: {quantity} szt.")

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        result.warnings.append(
            f"Niska pewność odczytu ({confidence:.0%}) -- sprawdź tę linię."
        )

    return result