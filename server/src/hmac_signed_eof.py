from __future__ import annotations
import hmac
import hashlib
import json

from watermarking_method import (
    WatermarkingMethod,
    PdfSource,
    load_pdf_bytes,
    is_pdf_bytes,
    SecretNotFoundError,
    InvalidKeyError
)

_MARKER = b"%%WATERMARK-HMAC-SIGNED%%"

class HMACsignedwatermark(WatermarkingMethod):
    name="HMAC-Signed"
    @staticmethod
    def get_usage() -> str:
        return ("Embeds an HMAC-SHA256-signed secret after the PDF's final %%EOF. "
            "`key` is used as the HMAC key. `position` is ignored.")
    def is_watermark_applicable(self, pdf:PdfSource, position:str |None=None) -> bool:
        data=load_pdf_bytes(pdf)
        return is_pdf_bytes(data)
    


    def add_watermark(self, pdf:PdfSource, secret, key:str, position:str |None=None) -> bytes:
        data=load_pdf_bytes(pdf)
        payload={"secret":secret}
        payload_byte=json.dumps(payload,sort_keys=True).encode()
        sig = hmac.new(key.encode(), payload_byte, hashlib.sha256).hexdigest()
        blob = payload_byte + b"." + sig.encode()
        encoded = _MARKER + b":" + blob + b":" + _MARKER
        return data + b"\n" + encoded 


    def read_secret(self, pdf: PdfSource, key: str) -> str:
        data = load_pdf_bytes(pdf)
        start = data.find(_MARKER)          # ← find, not rfind — grabs the FIRST (opening) marker
        if start == -1:
            raise SecretNotFoundError("Watermark not found")
        body = data[start + len(_MARKER) + 1:]
        end = body.find(_MARKER)            # ← find here too — first marker WITHIN body is the closing one
        if end == -1:
            raise SecretNotFoundError("Malformed watermark: closing marker not found")
        blob = body[:end - 1]
        payload_bytes, sig = blob.rsplit(b".", 1)
        expected_sig = hmac.new(key.encode(), payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, sig.decode()):
            raise InvalidKeyError("Invalid signature - wrong key or tampered watermark")
        payload = json.loads(payload_bytes)
        return payload["secret"]   

