from fastapi import APIRouter, Query

from handlers import QrCodeHandler


router = APIRouter(tags=["qrcode"])
handler = QrCodeHandler()


@router.get(
    "/qrcode",
    summary="Generate a QR code",
    description="Generate a PNG QR code from text or a URL.",
    responses={200: {"description": "QR code image (PNG)"}},
)
async def qrcode(
    data: str = Query(..., min_length=1, max_length=2000, description="Text or URL to encode"),
    size: int = Query(10, ge=1, le=50, description="Box size (module pixel size)"),
    border: int = Query(4, ge=0, le=20, description="Quiet zone border width"),
    fill: str = Query("#000000", description="Module color (hex)"),
    back: str = Query("#FFFFFF", description="Background color (hex)"),
):
    return handler.generate(data=data, size=size, border=border, fill=fill, back=back)
