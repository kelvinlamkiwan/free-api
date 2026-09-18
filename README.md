# free-api

A collection of free utility APIs built with **FastAPI** (Python). No API keys, no GPU, no external services — everything runs locally with pure-Python dependencies.

## Setup

```bash
pip install -r requirements.txt
```

> **Note:** PDF-to-image conversion uses [PyMuPDF](https://pymupdf.readthedocs.io/) — a pure-Python wheel with no system dependencies (no Poppler required).

## Run

```bash
uvicorn main:app --reload
```

The interactive API docs are available at `http://localhost:8000/docs`.

## Run with Docker

```bash
docker build -t free-api .
docker run --rm -p 8080:8080 free-api
```

The container image includes the application code and Python dependencies only (no system packages required).

---

## Project Structure

- `main.py` sets up the FastAPI app and registers routes only.
- `routes/` contains the API endpoint definitions.
- `handlers/` contains the classes that handle endpoint logic.

---

## Endpoints

### 📄 PDF → Image

#### `POST /pdf-to-image`

Convert a PDF file to images.

| Parameter | Type   | Default | Description                          |
|-----------|--------|---------|--------------------------------------|
| `file`    | file   | —       | PDF file (multipart/form-data)       |
| `fmt`     | string | `jpeg`  | Output format: `jpeg` or `png`       |
| `dpi`     | int    | `150`   | Resolution in DPI (72–600)           |

**Response:**
- Single-page PDF → returns the image directly (`image/jpeg` or `image/png`).
- Multi-page PDF → returns a ZIP archive (`application/zip`) containing one image per page.

**Example (curl):**

```bash
# Single page — saves page_1.jpg
curl -X POST "http://localhost:8000/pdf-to-image?fmt=jpeg&dpi=200" \
  -F "file=@document.pdf" \
  --output page_1.jpg

# Multi-page — saves pages.zip
curl -X POST "http://localhost:8000/pdf-to-image?fmt=png" \
  -F "file=@multipage.pdf" \
  --output pages.zip
```

---

### 🖼️ Image Processing

#### `POST /image/resize`

Resize an image (provide `width`, `height`, or both — the other is scaled to keep aspect ratio).

| Parameter | Type | Default | Description                         |
|-----------|------|---------|-------------------------------------|
| `file`    | file | —       | Image file (multipart/form-data)    |
| `width`   | int  | —       | Target width in pixels (1–8000)     |
| `height`  | int  | —       | Target height in pixels (1–8000)    |
| `fmt`     | str  | `png`   | Output format: `jpeg`/`png`/`webp`  |

```bash
curl -X POST "http://localhost:8000/image/resize?width=200&fmt=png" \
  -F "file=@photo.jpg" --output thumb.png
```

#### `POST /image/convert`

Convert an image to another format.

| Parameter | Type | Default | Description                        |
|-----------|------|---------|------------------------------------|
| `file`    | file | —       | Image file (multipart/form-data)   |
| `fmt`     | str  | `jpeg`  | Output: `jpeg`/`png`/`webp`        |
| `quality` | int  | `85`    | JPEG/WEBP quality (1–100)          |

```bash
curl -X POST "http://localhost:8000/image/convert?fmt=webp&quality=90" \
  -F "file=@photo.png" --output photo.webp
```

#### `POST /image/watermark`

Overlay a text watermark on an image.

| Parameter   | Type  | Default       | Description                                             |
|-------------|-------|---------------|---------------------------------------------------------|
| `file`      | file  | —             | Image file (multipart/form-data)                        |
| `text`      | str   | —             | Watermark text (required, ≤200 chars)                   |
| `position`  | str   | `bottom-right`| `center`/`top-left`/`top-right`/`bottom-left`/`bottom-right` |
| `opacity`   | float | `0.8`         | Text opacity (0–1)                                      |
| `color`     | str   | `#FF0000`     | Text color (hex)                                        |
| `font_size` | int   | `40`          | Font size in pixels (8–500)                             |

```bash
curl -X POST "http://localhost:8000/image/watermark?text=NOVI&position=bottom-right" \
  -F "file=@photo.jpg" --output watermarked.png
```

---

### 🔳 QR Code

#### `GET /qrcode`

Generate a PNG QR code.

| Parameter | Type | Default   | Description                  |
|-----------|------|-----------|------------------------------|
| `data`    | str  | —         | Text or URL to encode        |
| `size`    | int  | `10`      | Box size in pixels (1–50)    |
| `border`  | int  | `4`       | Quiet-zone border (0–20)     |
| `fill`    | str  | `#000000` | Module color (hex)           |
| `back`    | str  | `#FFFFFF` | Background color (hex)       |

```bash
curl "http://localhost:8000/qrcode?data=https://example.com" --output qr.png
```

---

### 〰️ Barcode

#### `GET /barcode`

Generate a 1D barcode as a PNG.

| Parameter | Type | Default    | Description                                                          |
|-----------|------|------------|----------------------------------------------------------------------|
| `data`    | str  | —          | Data to encode                                                       |
| `fmt`     | str  | `code128`  | `code128`/`ean13`/`ean8`/`upc`/`code39`/`itf`/`isbn13`/`isbn10`/`pzn`/`gs1_128` |

```bash
curl "http://localhost:8000/barcode?data=12345678&fmt=code128" --output barcode.png
```

---

### 🧰 Utilities

#### `GET /utils/uuid`

| Parameter | Type | Default | Description                    |
|-----------|------|---------|--------------------------------|
| `count`   | int  | `1`     | Number of UUIDs (1–100)        |
| `version` | int  | `4`     | UUID version: `1`, `4` or `5`  |

```bash
curl "http://localhost:8000/utils/uuid?count=5"
```

#### `GET /utils/hash`

| Parameter | Type | Default  | Description                      |
|-----------|------|----------|----------------------------------|
| `text`    | str  | —        | Text to hash                     |
| `algo`    | str  | `sha256` | `md5`/`sha1`/`sha256`/`sha512`   |

```bash
curl "http://localhost:8000/utils/hash?text=hello&algo=sha256"
```

#### `POST /utils/base64/encode`

```bash
curl -X POST "http://localhost:8000/utils/base64/encode" \
  -H "Content-Type: application/json" \
  -d '{"text": "hello"}'
```

#### `POST /utils/base64/decode`

```bash
curl -X POST "http://localhost:8000/utils/base64/decode" \
  -H "Content-Type: application/json" \
  -d '{"text": "aGVsbG8="}'
```

#### `POST /utils/csv-to-json`

Upload a CSV (first row = headers), get a JSON array back.

```bash
curl -X POST "http://localhost:8000/utils/csv-to-json" \
  -F "file=@data.csv"
```

#### `POST /utils/json-to-csv`

Send a JSON array of objects, get CSV back.

```bash
curl -X POST "http://localhost:8000/utils/json-to-csv" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"name": "apple", "price": "1.5"}, {"name": "banana", "price": "2.0"}]}'
```

---

## Limits

- Image uploads are capped at **15 MB** (override with the `IMAGE_MAX_BYTES` env var).
- PDF conversion is capped at **50 pages** (override with `PDF_MAX_PAGES`).
