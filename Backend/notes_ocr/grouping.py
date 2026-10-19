"""Składanie fragmentów tekstu z OCR w linie, tak jak je widzi człowiek.

OCR często tnie jedną linię `1500 x 900 2 szt` na kilka osobnych
fragmentów. Parser potrzebuje całej linii naraz, więc fragmenty o
podobnej wysokości na obrazie łączymy w jedną linię, od lewej do prawej.
"""

from dataclasses import dataclass
from statistics import median
from typing import List

from .engine import TextBox


@dataclass(frozen=True)
class TextLine:
    text: str
    confidence: float  # najniższa pewność spośród fragmentów linii
    y_center: float


def group_into_lines(
    boxes: List[TextBox],
    line_tolerance: float = 0.6,
) -> List[TextLine]:
    """`line_tolerance` to ułamek mediany wysokości tekstu: fragment
    należy do bieżącej linii, jeśli jego środek w pionie leży bliżej niż
    tyle od środka linii."""

    if not boxes:
        return []

    typical_height = median(box.height for box in boxes) or 1.0
    max_offset = line_tolerance * typical_height

    sorted_boxes = sorted(boxes, key=lambda box: box.y_center)

    lines: List[List[TextBox]] = [[sorted_boxes[0]]]
    for box in sorted_boxes[1:]:
        current = lines[-1]
        current_center = sum(b.y_center for b in current) / len(current)
        if abs(box.y_center - current_center) <= max_offset:
            current.append(box)
        else:
            lines.append([box])

    result: List[TextLine] = []
    for line_boxes in lines:
        line_boxes.sort(key=lambda box: box.x_min)
        result.append(
            TextLine(
                text=" ".join(box.text for box in line_boxes),
                confidence=min(box.confidence for box in line_boxes),
                y_center=sum(b.y_center for b in line_boxes) / len(line_boxes),
            )
        )
    return result
