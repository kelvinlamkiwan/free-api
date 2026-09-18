from typing import Literal, Optional

from fastapi import APIRouter, File, Query, UploadFile

from handlers import ImageHandler


router = APIRouter(tags=["image"])
handler = ImageHandler()


@router.post(
    "/image/resize",
    summary="Resize an image",
    description="Upload an image and resize it. Provide width, height, or both (the other is scaled to keep aspect ratio).",
    responses={
        200: {"description": "Resized image"},
        400: {"description": "Invalid input"},
        413: {"description": "Image too large"},
    },
)
async def resize(
    file: UploadFile = File(..., description="Image file to resize"),
    width: Optional[int] = Query(None, ge=1, le=8000, description="Target width in pixels"),
    height: Optional[int] = Query(None, ge=1, le=8000, description="Target height in pixels"),
    fmt: Literal["jpeg", "png", "webp"] = Query("png", description="Output format"),
):
    return await handler.resize(file=file, width=width, height=height, fmt=fmt)


@router.post(
    "/image/convert",
    summary="Convert an image format",
    description="Upload an image and convert it to JPEG, PNG or WEBP, optionally setting JPEG/WEBP quality.",
    responses={
        200: {"description": "Converted image"},
        400: {"description": "Invalid input"},
        413: {"description": "Image too large"},
    },
)
async def convert(
    file: UploadFile = File(..., description="Image file to convert"),
    fmt: Literal["jpeg", "png", "webp"] = Query("jpeg", description="Output format"),
    quality: int = Query(85, ge=1, le=100, description="JPEG/WEBP quality (1-100)"),
):
    return await handler.convert(file=file, fmt=fmt, quality=quality)


@router.post(
    "/image/watermark",
    summary="Add a text watermark",
    description="Upload an image and overlay a text watermark at a chosen position.",
    responses={
        200: {"description": "Watermarked image (PNG)"},
        400: {"description": "Invalid input"},
        413: {"description": "Image too large"},
    },
)
async def watermark(
    file: UploadFile = File(..., description="Image file to watermark"),
    text: str = Query(..., min_length=1, max_length=200, description="Watermark text"),
    position: Literal["center", "top-left", "top-right", "bottom-left", "bottom-right"] = Query(
        "bottom-right", description="Watermark position"
    ),
    opacity: float = Query(0.8, ge=0.0, le=1.0, description="Text opacity (0-1)"),
    color: str = Query("#FF0000", description="Text color (hex, e.g. #FF0000)"),
    font_size: int = Query(40, ge=8, le=500, description="Font size in pixels"),
):
    return await handler.watermark(
        file=file,
        text=text,
        position=position,
        opacity=opacity,
        color=color,
        font_size=font_size,
    )
