import io

import barcode
from barcode.writer import ImageWriter
from fastapi.responses import JSONResponse, StreamingResponse


class BarcodeHandler:
    def generate(self, data: str, fmt: str):
        try:
            code = barcode.get(fmt, data, writer=ImageWriter())
            buf = io.BytesIO()
            code.write(buf)
            buf.seek(0)
            return StreamingResponse(
                buf,
                media_type="image/png",
                headers={"Content-Disposition": f'attachment; filename="{fmt}.png"'},
            )
        except Exception as exc:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid barcode input: {exc}"},
            )
