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

from xhtml2pdf import pisa

# Safety limits (overridable via env).
MAX_FILES = int(os.environ.get("PDF_MAX_FILES", "50"))
MAX_PAGES = int(os.environ.get("PDF_MAX_PAGES", "100"))


class PdfToolsHandler:
    def _pdf_stream(self, pdf_bytes: bytes, filename: str):
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    async def images_to_pdf(self, files):
        if len(files) > MAX_FILES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Too many images. Maximum is {MAX_FILES}."},
            )

        doc = fitz.open()
        try:
            for file in files:
                data = await file.read()
                if not data:
                    continue
                try:
                    img = Image.open(io.BytesIO(data))
                    img.load()
                except Exception:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": f"Invalid image: {file.filename}"},
                    )
                img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="PDF")  # Pillow: image → single-page PDF
                img_pdf = fitz.open(stream=buf.getvalue(), filetype="pdf")
                doc.insert_pdf(img_pdf)
                img_pdf.close()

            if doc.page_count == 0:
                return JSONResponse(status_code=400, content={"detail": "No valid images provided."})
            out = doc.tobytes()
        finally:
            doc.close()

        return self._pdf_stream(out, "images.pdf")

    async def merge(self, files):
        if len(files) > MAX_FILES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Too many PDFs. Maximum is {MAX_FILES}."},
            )

        doc = fitz.open()
        try:
            for file in files:
                data = await file.read()
                if not data:
                    continue
                try:
                    src = fitz.open(stream=data, filetype="pdf")
                except Exception:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": f"Invalid PDF: {file.filename}"},
                    )
                doc.insert_pdf(src)
                src.close()

            if doc.page_count == 0:
                return JSONResponse(status_code=400, content={"detail": "No valid PDFs provided."})
            out = doc.tobytes()
        finally:
            doc.close()

        return self._pdf_stream(out, "merged.pdf")

    def _parse_ranges(self, spec, total):
        spec = (spec or "").strip()
        if not spec or spec.lower() == "all":
            return [(i, i) for i in range(1, total + 1)]

        ranges = []
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                if "-" in part:
                    a, b = part.split("-", 1)
                    a, b = int(a), int(b)
                else:
                    a = b = int(part)
            except ValueError:
                raise ValueError(f"Invalid page spec: {part}")
            if a < 1 or b > total or a > b:
                raise ValueError(f"Page range out of bounds: {part}")
            ranges.append((a, b))

        if not ranges:
            raise ValueError("Empty page spec")
        return ranges

    async def split(self, file, pages_spec):
        data = await file.read()
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception:
            return JSONResponse(status_code=400, content={"detail": "Invalid PDF."})

        total = doc.page_count
        if total == 0:
            doc.close()
            return JSONResponse(status_code=400, content={"detail": "PDF has no pages."})

        try:
            ranges = self._parse_ranges(pages_spec, total)
        except ValueError as exc:
            doc.close()
            return JSONResponse(status_code=400, content={"detail": str(exc)})

        # A single explicit range → return that range as a single PDF.
        if pages_spec.strip().lower() != "all" and len(ranges) == 1:
            a, b = ranges[0]
            out_doc = fitz.open()
            out_doc.insert_pdf(doc, from_page=a - 1, to_page=b - 1)
            out = out_doc.tobytes()
            out_doc.close()
            doc.close()
            filename = f"page_{a}.pdf" if a == b else f"pages_{a}-{b}.pdf"
            return self._pdf_stream(out, filename)

        # Otherwise stream a ZIP of the requested pages/ranges.
        return StreamingResponse(
            self._zip_stream(doc, ranges),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="split.zip"'},
        )

    def _zip_stream(self, doc, ranges):
        try:
            with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as spool:
                with zipfile.ZipFile(spool, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for a, b in ranges:
                        out_doc = fitz.open()
                        out_doc.insert_pdf(doc, from_page=a - 1, to_page=b - 1)
                        name = f"page_{a}.pdf" if a == b else f"pages_{a}-{b}.pdf"
                        zf.writestr(name, out_doc.tobytes())
                        out_doc.close()
                spool.seek(0)
                while True:
                    chunk = spool.read(256 * 1024)
                    if not chunk:
                        break
                    yield chunk
        finally:
            doc.close()

    async def extract_text(self, file):
        data = await file.read()
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception:
            return JSONResponse(status_code=400, content={"detail": "Invalid PDF."})

        if doc.page_count > MAX_PAGES:
            doc.close()
            return JSONResponse(
                status_code=413,
                content={"detail": f"PDF has {doc.page_count} pages, maximum is {MAX_PAGES}."},
            )

        pages = []
        for i in range(doc.page_count):
            pages.append({"page": i + 1, "text": doc.load_page(i).get_text()})
        doc.close()

        full = "\n\n".join(p["text"] for p in pages)
        return {"page_count": len(pages), "text": full, "pages": pages}

    def html_to_pdf(self, html):
        out = io.BytesIO()
        try:
            pisa.CreatePDF(src=html, dest=out, encoding="utf-8")
        except Exception as exc:
            return JSONResponse(status_code=400, content={"detail": f"Failed to convert HTML: {exc}"})

        pdf_bytes = out.getvalue()
        if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
            return JSONResponse(status_code=400, content={"detail": "HTML conversion produced no valid PDF."})

        return self._pdf_stream(pdf_bytes, "output.pdf")
