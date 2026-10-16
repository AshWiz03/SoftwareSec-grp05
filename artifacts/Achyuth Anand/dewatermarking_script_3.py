import fitz
import requests

link = "8add5a297e10f5bd545d4e6f906ea65c"
BASE = "http://softsec-group-29.dsv.local.su.se:5000"

r = requests.get(f"{BASE}/api/get-version/{link}", timeout=10)
with open("group_29_watermarked.pdf", "wb") as f:
    f.write(r.content)

doc = fitz.open("group_29_watermarked.pdf")

for page in doc:
    blocks = page.get_text("blocks")
    for block in blocks:
        block_text = block[4].strip()
        if block_text.startswith("<mwm:") or "WM-" in block_text or len(block_text) > 150:
            print(f"Redacting: '{block_text[:60]}'")
            rect = fitz.Rect(block[0], block[1], block[2], block[3])
            page.add_redact_annot(rect)
        else:
            print(f"Keeping: '{block_text[:60]}'")
    page.apply_redactions()

doc.save("group_29_dewatermarked.pdf")

doc2 = fitz.open("group_29_dewatermarked.pdf")
text = doc2[0].get_text("text")
print(f"Watermark present: {'<mwm:' in text}")
