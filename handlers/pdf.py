import io
import zipfile

import pdf2image
from fastapi import UploadFile
from fastapi.responses import JSONResponse, StreamingResponse


class PdfToImageHandler:
    async def convert(self, file: UploadFile, fmt: str, dpi: int):
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
            return JSONResponse(
                status_code=400,
                content={"detail": "Failed to convert PDF. Ensure the file is a valid PDF."},
            )

        mime = "image/jpeg" if fmt == "jpeg" else "image/png"
        ext = "jpg" if fmt == "jpeg" else "png"
        pil_format = fmt.upper()

        if len(images) == 1:
            buf = io.BytesIO()
            self._prepare_image(images[0], fmt).save(buf, format=pil_format)
            buf.seek(0)
            return StreamingResponse(
                buf,
                media_type=mime,
                headers={"Content-Disposition": f'attachment; filename="page_1.{ext}"'},
            )

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for index, image in enumerate(images, start=1):
                img_buf = io.BytesIO()
                self._prepare_image(image, fmt).save(img_buf, format=pil_format)
                zf.writestr(f"page_{index}.{ext}", img_buf.getvalue())
        zip_buf.seek(0)
        return StreamingResponse(
            zip_buf,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="pages.zip"'},
        )

    def _prepare_image(self, image, fmt: str):
        if fmt == "jpeg":
            if image.mode == "P":
                image = image.convert("RGBA")
            if image.mode in ("RGBA", "LA"):
                image = image.convert("RGB")
        return image
