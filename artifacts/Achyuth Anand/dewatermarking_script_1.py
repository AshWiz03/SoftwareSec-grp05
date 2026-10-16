import fitz
import requests

link = "74f14b7cf5bcb90b8071925b40aab690"

r = requests.get(f"http://10.100.11.19:5000/api/get-version/{link}", timeout=10)
with open("group_17_watermarked.pdf", "wb") as f:
    f.write(r.content)

doc = fitz.open("group_17_watermarked.pdf")

for page in doc:
    blocks = page.get_text("blocks")
    for block in blocks:
        block_text = block[4].strip()
        if "WM-INVISIBLE-V1" in block_text:
            print(f"Redacting: '{block_text[:60]}'")
            rect = fitz.Rect(block[0], block[1], block[2], block[3])
            page.add_redact_annot(rect)
        else:
            print(f"Keeping: '{block_text[:60]}'")
    page.apply_redactions()

doc.save("group_17_dewatermarked.pdf")

doc2 = fitz.open("group_17_dewatermarked.pdf")
text = doc2[0].get_text("text")
print(f"Watermark present: {'WM-INVISIBLE-V1' in text}")
