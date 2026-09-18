import io

import qrcode
from fastapi.responses import StreamingResponse


class QrCodeHandler:
    def generate(self, data: str, size: int, border: int, fill: str, back: str):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill, back_color=back)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={"Content-Disposition": 'attachment; filename="qrcode.png"'},
        )
