import base64
import csv
import hashlib
import io
import uuid as uuid_lib

from fastapi import UploadFile
from fastapi.responses import JSONResponse, Response


class UtilsHandler:
    def uuid(self, count: int, version: int):
        if version == 1:
            values = [str(uuid_lib.uuid1()) for _ in range(count)]
        elif version == 5:
            values = [
                str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, str(uuid_lib.uuid4())))
                for _ in range(count)
            ]
        else:
            values = [str(uuid_lib.uuid4()) for _ in range(count)]
        return {"count": count, "version": version, "uuids": values}

    def hash_text(self, text: str, algo: str):
        h = hashlib.new(algo)
        h.update(text.encode("utf-8"))
        return {"algorithm": algo, "digest": h.hexdigest()}

    def base64_encode(self, text: str):
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return {"encoded": encoded}

    def base64_decode(self, text: str):
        try:
            decoded = base64.b64decode(text.encode("ascii"), validate=True).decode("utf-8")
        except Exception:
            return JSONResponse(status_code=400, content={"detail": "Invalid base64 string."})
        return {"decoded": decoded}

    async def csv_to_json(self, file: UploadFile):
        data = await file.read()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return JSONResponse(status_code=400, content={"detail": "CSV must be UTF-8 encoded."})
        try:
            reader = csv.DictReader(io.StringIO(text))
            rows = [dict(row) for row in reader]
        except Exception as exc:
            return JSONResponse(status_code=400, content={"detail": f"Failed to parse CSV: {exc}"})
        return {"count": len(rows), "rows": rows}

    def json_to_csv(self, data):
        if not data:
            return JSONResponse(status_code=400, content={"detail": "data must be a non-empty list of objects."})

        fieldnames = []
        for row in data:
            if not isinstance(row, dict):
                return JSONResponse(status_code=400, content={"detail": "data must be a list of objects."})
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="output.csv"'},
        )
