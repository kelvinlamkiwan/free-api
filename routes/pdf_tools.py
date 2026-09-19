from typing import List

from fastapi import APIRouter, File, Query, UploadFile
from pydantic import BaseModel

from handlers import PdfToolsHandler


router = APIRouter(tags=["pdf"])
handler = PdfToolsHandler()


class HtmlPayload(BaseModel):
    html: str


@router.post(
    "/images-to-pdf",
    summary="Combine images into a PDF",
    description="Upload multiple image files (PNG/JPG/etc.) and receive a single PDF with one page per image.",
    responses={
        200: {"description": "PDF file"},
        400: {"description": "Invalid input"},
        413: {"description": "Too many files"},
    },
)
async def images_to_pdf(
    files: List[UploadFile] = File(..., description="Image files to combine (one page each)"),
):
    return await handler.images_to_pdf(files)


@router.post(
    "/pdf-merge",
    summary="Merge multiple PDFs",
    description="Upload multiple PDF files and receive a single merged PDF.",
    responses={
        200: {"description": "Merged PDF"},
        400: {"description": "Invalid input"},
        413: {"description": "Too many files"},
    },
)
async def pdf_merge(
    files: List[UploadFile] = File(..., description="PDF files to merge (in order)"),
):
    return await handler.merge(files)


@router.post(
    "/pdf-split",
    summary="Split a PDF",
    description=(
        "Upload a PDF and extract pages. Use `pages=all` (default) for a ZIP of individual pages, "
        "or a range spec like `1-3,5` for specific pages. A single range returns a single PDF."
    ),
    responses={
        200: {"description": "PDF (single range) or ZIP (multiple pages/ranges)"},
        400: {"description": "Invalid input"},
    },
)
async def pdf_split(
    file: UploadFile = File(..., description="PDF file to split"),
    pages: str = Query("all", description="Pages to extract, e.g. '1-3,5' or 'all'"),
):
    return await handler.split(file, pages)


@router.post(
    "/pdf-extract-text",
    summary="Extract text from a PDF",
    description="Upload a PDF and receive its text content as JSON (per-page + full text).",
    responses={
        200: {"description": "JSON with extracted text"},
        400: {"description": "Invalid input"},
        413: {"description": "Too many pages"},
    },
)
async def pdf_extract_text(file: UploadFile = File(..., description="PDF file to extract text from")):
    return await handler.extract_text(file)


@router.post(
    "/html-to-pdf",
    summary="Convert HTML to PDF",
    description="Send an HTML string and receive a PDF. Supports tables and basic CSS (not modern flexbox/grid).",
    responses={
        200: {"description": "PDF file"},
        400: {"description": "Invalid HTML"},
    },
)
async def html_to_pdf(payload: HtmlPayload):
    return handler.html_to_pdf(payload.html)
