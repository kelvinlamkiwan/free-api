import io
import os
import tempfile
import zipfile

from pdf2image import convert_from_bytes, pdfinfo_from_bytes
from fastapi import UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

# Maximum number of pages to convert in one request.
# This bounds memory / bandwidth — raise it only if you accept the cost.
MAX_PAGES = int(os.environ.get("PDF_MAX_PAGES", "50"))


class PdfToImageHandler:
    async def convert(self, file: UploadFile, fmt: str, dpi: int):
        is_pdf_content_type = file.content_type == "application/pdf"
        is_pdf_filename = (file.filename or "").lower().endswith(".pdf")
        if not is_pdf_content_type and not is_pdf_filename:
            return JSONResponse(status_code=400, content={"detail": "Uploaded file must be a PDF."})

        pdf_bytes = await file.read()
        if not pdf_bytes:
            return JSONResponse(status_code=400, content={"detail": "Uploaded file is empty."})

        # 1) Read page count (cheap — no rendering) and enforce the limit.
        try:
            info = pdfinfo_from_bytes(pdf_bytes)
            page_count = int(info.get("Pages") or 0)
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"detail": "Failed to read PDF. Ensure the file is a valid PDF."},
            )

        if page_count <= 0:
            return JSONResponse(status_code=400, content={"detail": "PDF has no pages."})

        if page_count > MAX_PAGES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"PDF has {page_count} pages, the maximum is {MAX_PAGES}."},
            )

        mime = "image/jpeg" if fmt == "jpeg" else "image/png"
        ext = "jpg" if fmt == "jpeg" else "png"
        pil_format = fmt.upper()

        if page_count == 1:
            try:
                images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=1, last_page=1)
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Failed to convert PDF. Ensure the file is a valid PDF."},
                )
            buf = io.BytesIO()
            self._prepare_image(images[0], fmt).save(buf, format=pil_format)
            buf.seek(0)
            return StreamingResponse(
                buf,
                media_type=mime,
                headers={"Content-Disposition": f'attachment; filename="page_1.{ext}"'},
            )

        # 2) Multi-page: stream a ZIP, rendering one page at a time so we never
        #    hold the whole document in memory. The ZIP is written to a spooled
        #    temp file (spills to disk if large) and streamed back in chunks.
        return StreamingResponse(
            self._zip_stream(pdf_bytes, dpi, fmt, pil_format, ext, page_count),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="pages.zip"'},
        )

    def _zip_stream(self, pdf_bytes, dpi, fmt, pil_format, ext, page_count):
        with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as spool:
            with zipfile.ZipFile(spool, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for page in range(1, page_count + 1):
                    try:
                        images = convert_from_bytes(
                            pdf_bytes, dpi=dpi, first_page=page, last_page=page
                        )
                    except Exception:
                        continue  # skip pages that fail to render
                    if not images:
                        continue
                    buf = io.BytesIO()
                    self._prepare_image(images[0], fmt).save(buf, format=pil_format)
                    zf.writestr(f"page_{page}.{ext}", buf.getvalue())
            spool.seek(0)
            while True:
                chunk = spool.read(256 * 1024)
                if not chunk:
                    break
                yield chunk

    def _prepare_image(self, image, fmt: str):
        if fmt == "jpeg":
            if image.mode == "P":
                image = image.convert("RGBA")
            if image.mode in ("RGBA", "LA"):
                image = image.convert("RGB")
        return image
