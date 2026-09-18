# free-api

A collection of free utility APIs built with **FastAPI** (Python).

## Setup

```bash
pip install -r requirements.txt
```

> **Note:** The PDF-to-image conversion requires [Poppler](https://poppler.freedesktop.org/) to be installed on your system.
> - **Ubuntu/Debian:** `sudo apt-get install poppler-utils`
> - **macOS:** `brew install poppler`
> - **Windows:** Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases) and add to PATH.

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

The container image includes the application code and the required Poppler system package.

---

## Project Structure

- `main.py` sets up the FastAPI app and registers routes only.
- `routes/` contains the API endpoint definitions.
- `handlers/` contains the classes that handle endpoint logic.

---

## Endpoints

### `POST /pdf-to-image`

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
