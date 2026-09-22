import base64
import hashlib
import re

import fitz  # PyMuPDF
from watermarking_method import (
    WatermarkingMethod,
    SecretNotFoundError,
    InvalidKeyError,
    load_pdf_bytes,
    PdfSource
)
# secret → "TATOU"+secret → XOR with SHA-256(key), tiled → base64 → binary '0'/'1' string → wrapped in markers → written as invisible PDF text. read_secret() does the inverse
class InvisibleTextRenderer(WatermarkingMethod):
    name = "invisible-text-render"

    @staticmethod
    def get_usage() -> str:
        return "Embeds an encrypted secret as invisible binary text in the first page of the PDF."

    def _encrypt(self, secret: str, key: str) -> str:
        #SHA256 produces 32 byte keystream. XORED against data
        k = hashlib.sha256(key.encode('utf-8')).digest()
        #TATOU + Secret. Used by _decrypt to check if the input produces "TATOU", ie the right key was used
        data = ("TATOU" + secret).encode('utf-8')
        # k is XORED against data, and tiled if data is longer than k.
        xored = bytes(a ^ b for a, b in zip(data, k * (len(data) // len(k) + 1)))
        #convert to ascii string
        return base64.b64encode(xored).decode('utf-8')

    def _decrypt(self, payload: str, key: str) -> str:
        k = hashlib.sha256(key.encode('utf-8')).digest()
        try:
            # base64 decode to raw XOR
            data = base64.b64decode(payload)
            # XOR to reverse to original bytes
            xored = bytes(a ^ b for a, b in zip(data, k * (len(data) // len(k) + 1)))
            decrypted = xored.decode('utf-8')
            #Does not start with TATOU = wrong key
            if not decrypted.startswith("TATOU"):
                raise InvalidKeyError("Incorrect key provided: Magic string mismatch.")
            
            return decrypted[5:]
        except InvalidKeyError:
            raise
        except Exception as e:
            raise InvalidKeyError(f"Failed to decrypt payload. Key might be wrong or data corrupted. Error: {e}")
    #Encoded text which will be written into the PDF
    def _encode_zw(self, payload: str) -> str:
        binary = ''.join(format(ord(c), '08b') for c in payload)
        return f"TATOU_START:{binary}:TATOU_END"
    #Reverses _encode_zw
    def _decode_zw(self, zw_str: str) -> str:
        chars = []
        for i in range(0, len(zw_str), 8):
            byte = zw_str[i:i+8]
            chars.append(chr(int(byte, 2)))
        return ''.join(chars)

    def add_watermark(self, pdf: PdfSource, secret: str, key: str, position: str | None = None) -> bytes:
        #Normalize pdf into raw bytes. 
        #Pipeline: plain secret -> encrypted -> base64 string -> binary
        data = load_pdf_bytes(pdf)
        enc_payload = self._encrypt(secret, key)
        zw_payload = self._encode_zw(enc_payload)

        try:
            doc = fitz.open(stream=data, filetype="pdf")
            if doc.page_count == 0:
                raise ValueError("Cannot watermark an empty PDF.")
            #Watermark every page in the pdf
            for page in doc:
                page.insert_text(
                    (50, 50),
                    zw_payload,
                    fontname="helv",
                    fontsize=1,
                    render_mode=3
                )
            return doc.write()
        except Exception as e:
            raise ValueError(f"Failed to apply watermark: {e}")

    def is_watermark_applicable(self, pdf: PdfSource, position: str | None = None) -> bool:
        #Check if pdf opens and has a page to write on
        try:
            data = load_pdf_bytes(pdf)
            doc = fitz.open(stream=data, filetype="pdf")
            return doc.page_count > 0
        except Exception:
            return False

    def read_secret(self, pdf: PdfSource, key: str) -> str:
        data = load_pdf_bytes(pdf)
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")

        # Stop when finding a watermark
        found_binary = None
        for page in doc:
            text = page.get_text("text")
            match = re.search(r'TATOU_START:([01]+):TATOU_END', text)
            if match:
                found_binary = match.group(1)
                break

        if not found_binary:
            raise SecretNotFoundError("No invisible text watermark found in this document.")

        payload = self._decode_zw(found_binary)
        return self._decrypt(payload, key)