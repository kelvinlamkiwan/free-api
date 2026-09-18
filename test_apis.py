import io

from PIL import Image
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'✅' if ok else '❌'} {name} {detail}")


# helper: build a test PNG in memory
def make_test_png(color="red", size=(300, 200)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# --- QR code ---
r = client.get("/qrcode", params={"data": "https://example.com"})
check("QR code", r.status_code == 200 and r.headers["content-type"] == "image/png", f"({r.status_code}, {r.headers.get('content-type')})")

# --- Barcode ---
r = client.get("/barcode", params={"data": "12345678", "fmt": "code128"})
check("Barcode code128", r.status_code == 200 and r.headers["content-type"] == "image/png", f"({r.status_code}, {r.headers.get('content-type')})")

r = client.get("/barcode", params={"data": "123", "fmt": "ean13"})
check("Barcode ean13 invalid -> 400", r.status_code == 400, f"({r.status_code})")

# --- Image resize ---
r = client.post("/image/resize", params={"width": 100}, files={"file": ("test.png", make_test_png(), "image/png")})
check("Image resize", r.status_code == 200 and r.headers["content-type"] == "image/png", f"({r.status_code}, {r.headers.get('content-type')})")

# --- Image convert ---
r = client.post("/image/convert", params={"fmt": "jpeg", "quality": 90}, files={"file": ("test.png", make_test_png(), "image/png")})
check("Image convert->jpeg", r.status_code == 200 and r.headers["content-type"] == "image/jpeg", f"({r.status_code}, {r.headers.get('content-type')})")

# --- Image watermark ---
r = client.post("/image/watermark", params={"text": "TEST", "position": "center"}, files={"file": ("test.png", make_test_png(), "image/png")})
check("Image watermark", r.status_code == 200 and r.headers["content-type"] == "image/png", f"({r.status_code}, {r.headers.get('content-type')})")

# --- Utils ---
r = client.get("/utils/uuid", params={"count": 3})
body = r.json()
check("Utils uuid", r.status_code == 200 and len(body["uuids"]) == 3, f"({body.get('count')} uuids)")

r = client.get("/utils/hash", params={"text": "hello", "algo": "sha256"})
body = r.json()
check("Utils hash", r.status_code == 200 and len(body["digest"]) == 64, f"({body['digest'][:12]}...)")

r = client.post("/utils/base64/encode", json={"text": "hello"})
check("Utils base64 encode", r.status_code == 200 and r.json()["encoded"] == "aGVsbG8=", f"({r.json().get('encoded')})")

r = client.post("/utils/base64/decode", json={"text": "aGVsbG8="})
check("Utils base64 decode", r.status_code == 200 and r.json()["decoded"] == "hello", f"({r.json().get('decoded')})")

csv_content = "name,price\napple,1.5\nbanana,2.0"
r = client.post("/utils/csv-to-json", files={"file": ("data.csv", csv_content.encode(), "text/csv")})
body = r.json()
check("Utils csv-to-json", r.status_code == 200 and body["count"] == 2 and body["rows"][0]["name"] == "apple", f"({body.get('count')} rows)")

r = client.post("/utils/json-to-csv", json={"data": [{"name": "apple", "price": "1.5"}, {"name": "banana", "price": "2.0"}]})
ok = r.status_code == 200 and "name,price" in r.text and "apple" in r.text
check("Utils json-to-csv", ok, f"({r.status_code})")

print("\n=== SUMMARY ===")
passed = sum(1 for _, ok, _ in results if ok)
print(f"{passed}/{len(results)} passed")
