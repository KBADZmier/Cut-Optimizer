from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .engine import OcrEngine, RapidOcrEngine
from .grouping import TextLine, group_into_lines
from .parser import ParsedLine, parse_line
from .preprocess import ImageSource, load_image, preprocess


MARKER_OPENS_GROUP = True


@dataclass
class ExtractionResult:
    lines: List[ParsedLine]
    ocr_lines: List[TextLine] = field(default_factory=list)

    @property
    def unparsed_lines(self) -> List[str]:
        """Linie, które wyglądały na pozycje (zawierały liczby), ale nie
        dało się z nich odczytać wymiarów -- do ręcznego przepisania."""
        return [line.raw_text for line in self.lines if line.kind == "unparsed"]

    @staticmethod
    def _order_dict(line: ParsedLine, default_reduction_mm: float) -> Dict:
        return {
            "name": line.name,
            "length_mm": line.length_mm,
            "height_mm": line.height_mm,
            "quantity": line.quantity,
            "reduction_mm": default_reduction_mm,
            "needs_review": line.needs_review,
            "warnings": line.warnings,
            "confidence": round(line.confidence, 3),
            "raw_text": line.raw_text,
        }

    def groups(self, default_reduction_mm: float = 52.0) -> List[Dict]:


        groups: List[Dict] = []
        current: Optional[Dict] = None

        def new_group(marker_text: str) -> Dict:
            group = {"marker_text": marker_text, "orders": []}
            groups.append(group)
            return group

        def merge(existing: str, extra: str) -> str:
            return " ".join(part for part in (existing, extra) if part)

        for line in self.lines:
            if line.kind == "marker":
                if MARKER_OPENS_GROUP:
                    if current is not None and not current["orders"]:
                        current["marker_text"] = merge(current["marker_text"], line.marker_text)
                    else:
                        current = new_group(line.marker_text)
                else:
  
                    if current is not None:
                        current["marker_text"] = merge(current["marker_text"], line.marker_text)
                        current = None

            elif line.kind == "order":
                order = self._order_dict(line, default_reduction_mm)

                if line.marker_text and MARKER_OPENS_GROUP:
                    if current is not None and not current["orders"]:
                        current["marker_text"] = merge(current["marker_text"], line.marker_text)
                    else:
                        current = new_group(line.marker_text)
                elif current is None:
                    current = new_group("")

                current["orders"].append(order)

                if line.marker_text and not MARKER_OPENS_GROUP:
                    current["marker_text"] = merge(current["marker_text"], line.marker_text)
                    current = None

        return [group for group in groups if group["orders"]]

    def orders(self, default_reduction_mm: float = 52.0) -> List[Dict]:
        """Płaska lista pozycji (bez podziału na grupy)."""
        return [
            order
            for group in self.groups(default_reduction_mm)
            for order in group["orders"]
        ]


def parse_text_lines(text_lines: List[TextLine]) -> List[ParsedLine]:


    parsed: List[ParsedLine] = []
    order_counter = 0

    for text_line in text_lines:
        line = parse_line(text_line.text, confidence=text_line.confidence)

        if line.kind == "order":
            order_counter += 1
            if line.name is None:
                line.name = f"Poz{order_counter}"

        parsed.append(line)

    return parsed


def extract_orders(
    image: ImageSource,
    engine: Optional[OcrEngine] = None,
    enhance_contrast: bool = True,
) -> ExtractionResult:


    engine = engine or RapidOcrEngine()

    image_bgr = preprocess(load_image(image), enhance_contrast=enhance_contrast)
    boxes = engine.read(image_bgr)
    text_lines = group_into_lines(boxes)

    return ExtractionResult(
        lines=parse_text_lines(text_lines),
        ocr_lines=text_lines,
    )