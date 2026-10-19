"""Backend OCR
"""
import io
import threading
import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from notes_ocr import RapidOcrEngine, extract_orders

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  

_state: dict = {}


_inference_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):

    _state["engine"] = RapidOcrEngine()
    yield
    _state.clear()


app = FastAPI(title="Odczyt notatek -- OCR", lifespan=lifespan)

##zawęzenie do adresow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderOut(BaseModel):
    name: str
    length_mm: float
    height_mm: float
    quantity: int
    reduction_mm: float
    needs_review: bool
    warnings: List[str]
    confidence: float
    raw_text: str


class GroupOut(BaseModel):
    marker_text: str  #separator
    orders: List[OrderOut]


class OcrLineOut(BaseModel):
    text: str
    confidence: float


class OcrResponse(BaseModel):
    backend: str
    elapsed_ms: int
    image_width: int
    image_height: int
    groups: List[GroupOut]
    unparsed_lines: List[str]
    ocr_lines: List[OcrLineOut]


@app.get("/api/health")
def health():
    engine = _state.get("engine")
    return {"ok": engine is not None, "backend": getattr(engine, "backend_name", None)}


@app.post("/api/ocr", response_model=OcrResponse)
def read_note(
    file: UploadFile = File(...),
    enhance_contrast: bool = Query(True, description="Wyrównanie oświetlenia (CLAHE)"),
):
    data = file.file.read(MAX_UPLOAD_BYTES + 1)

    if not data:
        raise HTTPException(status_code=400, detail="Przesłany plik jest pusty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Plik jest za duży (limit {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
        )

    try:
        with Image.open(io.BytesIO(data)) as probe:
            width, height = probe.size
            probe.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise HTTPException(
            status_code=400,
            detail="To nie jest poprawny obraz (obsługiwane: JPG, PNG, WEBP, BMP).",
        )

    started = time.perf_counter()
    with _inference_lock:
        result = extract_orders(
            data,
            engine=_state["engine"],
            enhance_contrast=enhance_contrast,
        )
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    return OcrResponse(
        backend=_state["engine"].backend_name,
        elapsed_ms=elapsed_ms,
        image_width=width,
        image_height=height,
        groups=result.groups(),
        unparsed_lines=result.unparsed_lines,
        ocr_lines=[
            OcrLineOut(text=line.text, confidence=round(line.confidence, 3))
            for line in result.ocr_lines
        ],
    )