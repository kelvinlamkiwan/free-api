from fastapi import APIRouter, File, Query, UploadFile

from handlers import PdfToImageHandler


router = APIRouter()
handler = PdfToImageHandler()


@router.post(
    "/pdf-to-image",
    summary="Convert PDF to images",
    description=(
        "Upload a PDF file and receive its pages converted to images.\n\n"
        "- For a single-page PDF, returns the image directly (JPEG or PNG).\n"
        "- For a multi-page PDF, returns a ZIP archive containing one image per page."
    ),
    responses={
        200: {"description": "Image file (single page) or ZIP archive (multi-page)"},
        400: {"description": "Invalid input"},
    },
)
async def pdf_to_image(
    file: UploadFile = File(..., description="PDF file to convert"),
    fmt: str = Query("jpeg", enum=["jpeg", "png"], description="Output image format"),
    dpi: int = Query(150, ge=72, le=600, description="Resolution in DPI (72–600)"),
):
    return await handler.convert(file=file, fmt=fmt, dpi=dpi)
