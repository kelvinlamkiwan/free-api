import io
import os

from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse

# Cap upload size to bound memory usage per request.
MAX_IMAGE_BYTES = int(os.environ.get("IMAGE_MAX_BYTES", str(15 * 1024 * 1024)))


class ImageHandler:
    async def _load(self, file: UploadFile) -> Image.Image:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Image exceeds the maximum size of {MAX_IMAGE_BYTES} bytes.",
            )
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            return img
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Failed to read image. Ensure the file is a valid image.",
            )

    def _save(self, img: Image.Image, fmt: str, quality: int = 85) -> io.BytesIO:
        buf = io.BytesIO()
        if fmt == "jpeg":
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=quality)
        elif fmt == "webp":
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            img.save(buf, format="WEBP", quality=quality)
        else:  # png
            img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    async def resize(self, file: UploadFile, width, height, fmt):
        img = await self._load(file)

        w, h = img.size
        if width and height:
            size = (width, height)
        elif width:
            size = (width, max(1, int(h * width / w)))
        elif height:
            size = (max(1, int(w * height / h)), height)
        else:
            size = (w, h)

        img = img.resize(size)
        buf = self._save(img, fmt)
        return StreamingResponse(
            buf,
            media_type=f"image/{fmt}",
            headers={"Content-Disposition": f'attachment; filename="resized.{fmt}"'},
        )

    async def convert(self, file: UploadFile, fmt, quality):
        img = await self._load(file)
        buf = self._save(img, fmt, quality)
        return StreamingResponse(
            buf,
            media_type=f"image/{fmt}",
            headers={"Content-Disposition": f'attachment; filename="converted.{fmt}"'},
        )

    async def watermark(self, file: UploadFile, text, position, opacity, color, font_size):
        img = await self._load(file)

        base = img.convert("RGBA")
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        W, H = base.size
        pad = 12

        if position == "top-left":
            xy = (pad, pad)
        elif position == "top-right":
            xy = (W - tw - pad, pad)
        elif position == "bottom-left":
            xy = (pad, H - th - pad)
        elif position == "bottom-right":
            xy = (W - tw - pad, H - th - pad)
        else:  # center
            xy = ((W - tw) // 2, (H - th) // 2)

        try:
            rgb = tuple(int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        except Exception:
            rgb = (255, 0, 0)
        rgba = rgb + (int(opacity * 255),)

        draw.text(xy, text, font=font, fill=rgba)
        out = Image.alpha_composite(base, overlay).convert("RGB")
        buf = self._save(out, "png")
        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={"Content-Disposition": 'attachment; filename="watermarked.png"'},
        )
