import io
from pathlib import Path
from typing import Union
import cv2
import numpy as np
from PIL import Image, ImageOps

ImageSource = Union[str, Path, bytes, bytearray, np.ndarray]


def load_image(source: ImageSource) -> np.ndarray:

    if isinstance(source, np.ndarray):
        return source

    if isinstance(source, (bytes, bytearray)):
        pil_image = Image.open(io.BytesIO(source))
    else:
        pil_image = Image.open(source)

    pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")
    return np.array(pil_image)[:, :, ::-1].copy()


def preprocess(
    image_bgr: np.ndarray,
    max_side: int = 2000,
    enhance_contrast: bool = True,
) -> np.ndarray:
    
    height, width = image_bgr.shape[:2]
    scale = max_side / max(height, width)

    if scale < 1.0:
        image_bgr = cv2.resize(
            image_bgr,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_AREA,
        )

    if enhance_contrast:
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        lightness, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lightness = clahe.apply(lightness)
        image_bgr = cv2.cvtColor(
            cv2.merge((lightness, a_channel, b_channel)), cv2.COLOR_LAB2BGR
        )

    return image_bgr
