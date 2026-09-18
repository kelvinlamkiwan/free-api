import io
import os
import tempfile
import zipfile

from PIL import Image
from fastapi import UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24
except ImportError:
    import fitz  # older PyMuPDF

# Maximum number of pages to convert in one request (bounds memory / bandwidth).
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

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = doc.page_count
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"detail": "Failed to read PDF. Ensure the file is a valid PDF."},
            )

        if page_count <= 0:
            doc.close()
            return JSONResponse(status_code=400, content={"detail": "PDF has no pages."})

        if page_count > MAX_PAGES:
            doc.close()
            return JSONResponse(
                status_code=413,
                content={"detail": f"PDF has {page_count} pages, the maximum is {MAX_PAGES}."},
            )

        mime = "image/jpeg" if fmt == "jpeg" else "image/png"
        ext = "jpg" if fmt == "jpeg" else "png"
        pil_format = fmt.upper()

        if page_count == 1:
            img = self._render(doc, 0, dpi)
            doc.close()
            buf = io.BytesIO()
            self._prepare_image(img, fmt).save(buf, format=pil_format)
            buf.seek(0)
            return StreamingResponse(
                buf,
                media_type=mime,
                headers={"Content-Disposition": f'attachment; filename="page_1.{ext}"'},
            )

        # Multi-page: stream a ZIP, rendering one page at a time to bound memory.
        return StreamingResponse(
            self._zip_stream(doc, dpi, fmt, pil_format, ext, page_count),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="pages.zip"'},
        )

    def _render(self, doc, page_index, dpi):
        page = doc.load_page(page_index)
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    def _zip_stream(self, doc, dpi, fmt, pil_format, ext, page_count):
        try:
            with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as spool:
                with zipfile.ZipFile(spool, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for page_index in range(page_count):
                        img = self._render(doc, page_index, dpi)
                        buf = io.BytesIO()
                        self._prepare_image(img, fmt).save(buf, format=pil_format)
                        zf.writestr(f"page_{page_index + 1}.{ext}", buf.getvalue())
                spool.seek(0)
                while True:
                    chunk = spool.read(256 * 1024)
                    if not chunk:
                        break
                    yield chunk
        finally:
            doc.close()

    def _prepare_image(self, image, fmt):
        if fmt == "jpeg" and image.mode != "RGB":
            image = image.convert("RGB")
        return image
