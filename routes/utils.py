from typing import List, Literal

from fastapi import APIRouter, File, Query, UploadFile
from pydantic import BaseModel

from handlers import UtilsHandler


router = APIRouter(tags=["utils"])
handler = UtilsHandler()


class TextPayload(BaseModel):
    text: str


class JsonToCsvPayload(BaseModel):
    data: List[dict]


@router.get(
    "/utils/uuid",
    summary="Generate UUIDs",
    description="Generate one or more UUIDs (v1, v4 or v5).",
)
async def uuid(
    count: int = Query(1, ge=1, le=100, description="Number of UUIDs to generate"),
    version: Literal[1, 4, 5] = Query(4, description="UUID version"),
):
    return handler.uuid(count=count, version=version)


@router.get(
    "/utils/hash",
    summary="Hash a string",
    description="Compute the digest of a string using MD5, SHA1, SHA256 or SHA512.",
)
async def hash_text(
    text: str = Query(..., min_length=1, description="Text to hash"),
    algo: Literal["md5", "sha1", "sha256", "sha512"] = Query("sha256", description="Hash algorithm"),
):
    return handler.hash_text(text=text, algo=algo)


@router.post(
    "/utils/base64/encode",
    summary="Base64 encode",
    description="Encode a UTF-8 string to Base64.",
)
async def base64_encode(payload: TextPayload):
    return handler.base64_encode(payload.text)


@router.post(
    "/utils/base64/decode",
    summary="Base64 decode",
    description="Decode a Base64 string to UTF-8 text.",
    responses={400: {"description": "Invalid base64 string"}},
)
async def base64_decode(payload: TextPayload):
    return handler.base64_decode(payload.text)


@router.post(
    "/utils/csv-to-json",
    summary="CSV to JSON",
    description="Upload a CSV file and convert it to a JSON array of objects (first row = headers).",
    responses={400: {"description": "Invalid CSV"}},
)
async def csv_to_json(file: UploadFile = File(..., description="CSV file to convert")):
    return await handler.csv_to_json(file)


@router.post(
    "/utils/json-to-csv",
    summary="JSON to CSV",
    description="Convert a JSON array of objects to a CSV file.",
    responses={400: {"description": "Invalid input"}},
)
async def json_to_csv(payload: JsonToCsvPayload):
    return handler.json_to_csv(payload.data)
