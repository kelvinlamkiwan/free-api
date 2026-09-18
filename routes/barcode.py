from typing import Literal

from fastapi import APIRouter, Query

from handlers import BarcodeHandler


router = APIRouter(tags=["barcode"])
handler = BarcodeHandler()


@router.get(
    "/barcode",
    summary="Generate a barcode",
    description="Generate a 1D barcode (Code128, EAN-13, etc.) as a PNG image.",
    responses={
        200: {"description": "Barcode image (PNG)"},
        400: {"description": "Invalid barcode input"},
    },
)
async def barcode(
    data: str = Query(..., min_length=1, max_length=200, description="Data to encode"),
    fmt: Literal[
        "code128", "ean13", "ean8", "upc", "code39", "itf", "isbn13", "isbn10", "pzn", "gs1_128"
    ] = Query("code128", description="Barcode symbology"),
):
    return handler.generate(data=data, fmt=fmt)
