from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import StreamingResponse, JSONResponse
import pdf2image
import io
import zipfile

app = FastAPI(
    title="Free API Collection",
    description="A collection of free utility APIs.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Welcome to Free API Collection. See /docs for available endpoints."}


@app.post(
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
    is_pdf_content_type = file.content_type == "application/pdf"
    is_pdf_filename = (file.filename or "").lower().endswith(".pdf")
    if not is_pdf_content_type and not is_pdf_filename:
        return JSONResponse(status_code=400, content={"detail": "Uploaded file must be a PDF."})

    pdf_bytes = await file.read()
    if not pdf_bytes:
        return JSONResponse(status_code=400, content={"detail": "Uploaded file is empty."})

    try:
        images = pdf2image.convert_from_bytes(pdf_bytes, dpi=dpi)
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Failed to convert PDF. Ensure the file is a valid PDF."})

    mime = "image/jpeg" if fmt == "jpeg" else "image/png"
    ext = "jpg" if fmt == "jpeg" else "png"
    pil_format = fmt.upper()

    def prepare(image):
        if fmt == "jpeg":
            if image.mode == "P":
                image = image.convert("RGBA")
            if image.mode in ("RGBA", "LA"):
                image = image.convert("RGB")
        return image

    if len(images) == 1:
        buf = io.BytesIO()
        prepare(images[0]).save(buf, format=pil_format)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type=mime,
            headers={"Content-Disposition": f'attachment; filename="page_1.{ext}"'},
        )

    # Multi-page: return a ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, image in enumerate(images, start=1):
            img_buf = io.BytesIO()
            prepare(image).save(img_buf, format=pil_format)
            zf.writestr(f"page_{i}.{ext}", img_buf.getvalue())
    zip_buf.seek(0)
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="pages.zip"'},
    )
