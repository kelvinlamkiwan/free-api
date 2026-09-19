import io
import zipfile

import fitz
from PIL import Image
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'✅' if ok else '❌'} {name} {detail}")


def make_image(color="red", size=(100, 100)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def make_pdf_with_text(text, pages=1):
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), text)
    return doc.tobytes()


# 1. images-to-pdf
files = [
    ("files", ("a.png", make_image("red"), "image/png")),
    ("files", ("b.png", make_image("blue"), "image/png")),
]
r = client.post("/images-to-pdf", files=files)
ok = r.status_code == 200 and r.content.startswith(b"%PDF")
if ok:
    d = fitz.open(stream=r.content, filetype="pdf")
    ok = d.page_count == 2
check("images-to-pdf (2 img -> 2-page PDF)", ok, f"({r.status_code})")

# 2. pdf-merge
pdf1 = make_pdf_with_text("doc one", pages=2)
pdf2 = make_pdf_with_text("doc two", pages=1)
files = [
    ("files", ("1.pdf", pdf1, "application/pdf")),
    ("files", ("2.pdf", pdf2, "application/pdf")),
]
r = client.post("/pdf-merge", files=files)
ok = r.status_code == 200 and r.content.startswith(b"%PDF")
if ok:
    d = fitz.open(stream=r.content, filetype="pdf")
    ok = d.page_count == 3
check("pdf-merge (2+1 -> 3-page PDF)", ok, f"({r.status_code})")

# 3. pdf-split all -> ZIP of 3
pdf3 = make_pdf_with_text("page text", pages=3)
r = client.post("/pdf-split", params={"pages": "all"}, files={"file": ("d.pdf", pdf3, "application/pdf")})
ok = r.status_code == 200 and r.headers["content-type"] == "application/zip"
if ok:
    z = zipfile.ZipFile(io.BytesIO(r.content))
    ok = len(z.namelist()) == 3
check("pdf-split all (3-page -> ZIP of 3)", ok, f"({r.status_code})")

# 4. pdf-split single range -> single PDF
r = client.post("/pdf-split", params={"pages": "1-2"}, files={"file": ("d.pdf", pdf3, "application/pdf")})
ok = r.status_code == 200 and r.headers["content-type"] == "application/pdf"
if ok:
    d = fitz.open(stream=r.content, filetype="pdf")
    ok = d.page_count == 2
check("pdf-split 1-2 (single PDF, 2 pages)", ok, f"({r.status_code})")

# 5. pdf-extract-text
pdf4 = make_pdf_with_text("Hello World this is a test", pages=1)
r = client.post("/pdf-extract-text", files={"file": ("e.pdf", pdf4, "application/pdf")})
body = r.json()
ok = r.status_code == 200 and "Hello World" in body.get("text", "")
check("pdf-extract-text", ok, f"({r.status_code})")

# 6. html-to-pdf
r = client.post(
    "/html-to-pdf",
    json={"html": "<h1>Invoice</h1><p>Total: $100</p><table><tr><td>A</td><td>B</td></tr></table>"},
)
ok = r.status_code == 200 and r.content.startswith(b"%PDF")
check("html-to-pdf", ok, f"({r.status_code})")

print(f"\n=== {sum(1 for _, ok, _ in results if ok)}/{len(results)} passed ===")
