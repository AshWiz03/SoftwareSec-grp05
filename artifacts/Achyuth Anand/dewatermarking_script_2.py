import fitz
import requests

link = "2487c0bc44283712239cc2d37b9af18fcad9de3f"
BASE = "http://softsec-group-03.dsv.local.su.se:5000"

r = requests.get(f"{BASE}/api/get-version/{link}", timeout=10)
data = r.content

eof_pos = data.rfind(b"%%EOF")
stripped = data[:eof_pos + 5]
print(f"Removed {len(data) - len(stripped)} bytes after EOF")

with open("/tmp/group_03_step1.pdf", "wb") as f:
    f.write(stripped)

doc = fitz.open("/tmp/group_03_step1.pdf")

for page in doc:
    blocks = page.get_text("blocks")
    for block in blocks:
        block_text = block[4].strip()
        if "WM-" in block_text or len(block_text) > 100:
            print(f"Redacting: '{block_text[:60]}'")
            rect = fitz.Rect(block[0], block[1], block[2], block[3])
            page.add_redact_annot(rect)
        else:
            print(f"Keeping: '{block_text[:60]}'")
    page.apply_redactions()

doc.save("group_03_dewatermarked.pdf")

doc2 = fitz.open("group_03_dewatermarked.pdf")
data2 = open("group_03_dewatermarked.pdf", "rb").read()
print(f"EOF watermark present: {'%%WM-OMAR' in data2.decode('latin-1', errors='ignore')}")
print(f"WM- in text: {'WM-' in doc2[0].get_text('text')}")
