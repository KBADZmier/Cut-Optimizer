from dataclasses import dataclass
from typing import List, Protocol

import numpy as np


@dataclass(frozen=True)
class TextBox:


    text: str
    confidence: float
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def y_center(self) -> float:
        return (self.y_min + self.y_max) / 2


class OcrEngine(Protocol):
    def read(self, image_bgr: np.ndarray) -> List[TextBox]:

        ...


class RapidOcrEngine:


    def __init__(self) -> None:
        self._engine, self.backend_name = self._create_engine()

    @staticmethod
    def _create_engine():
        try:
            from rapidocr import RapidOCR


            try:
                engine = RapidOCR(params={"Global.log_level": "warning"})
            except Exception:
                engine = RapidOCR()
            return engine, "rapidocr"
        except ImportError:
            pass

        try:
            from rapidocr_onnxruntime import RapidOCR as LegacyRapidOCR

            return LegacyRapidOCR(), "rapidocr-onnxruntime"
        except ImportError as error:
            raise ImportError(
                "Brak biblioteki OCR. Zainstaluj: pip install rapidocr "
                "onnxruntime   (na Pythonie < 3.13 działa też: "
                "pip install rapidocr-onnxruntime)"
            ) from error

    def read(self, image_bgr: np.ndarray) -> List[TextBox]:
        if self.backend_name == "rapidocr":
            output = self._engine(image_bgr)
            if output is None or output.txts is None or len(output.txts) == 0:
                return []
            raw = zip(output.boxes, output.txts, output.scores)
        else:
            result, _timing = self._engine(image_bgr)
            if not result:
                return []
            raw = result

        boxes: List[TextBox] = []
        for points, text, score in raw:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            boxes.append(
                TextBox(
                    text=str(text),
                    confidence=float(score),
                    x_min=float(min(xs)),
                    y_min=float(min(ys)),
                    x_max=float(max(xs)),
                    y_max=float(max(ys)),
                )
            )
        return boxes
