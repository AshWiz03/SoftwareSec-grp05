from __future__ import annotations
import base64
import hashlib
import json
import fitz  
from cryptography.fernet import Fernet, InvalidToken

from watermarking_method import (
    WatermarkingMethod,
    PdfSource,
    load_pdf_bytes,
    is_pdf_bytes,
    SecretNotFoundError,
    InvalidKeyError
)

#  Markers
_START_MARKER = "TATOU_HMAC_START:"
_END_MARKER = ":TATOU_HMAC_END"

# Embedding positions
_POSITIONS = [(50, 50), (200, 400), (400, 700), (100, 300)]

# Font names 
_FONTS = ["helv", "tiro", "cour"]

def _encode_binary(payload: str) -> str:
    
    binary = ''.join(format(ord(c), '08b') for c in payload)
    return f"{_START_MARKER}{binary}{_END_MARKER}"


def _decode_binary(binary_str: str) -> str:
    
    chars = []
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)

def _derive_fernet_key(key: str) -> bytes:
    """Turn an arbitrary key string into a valid 32-byte urlsafe-base64 Fernet key."""
    digest = hashlib.sha256(key.encode()).digest()
    return base64.urlsafe_b64encode(digest)

class HMACsignedwatermark(WatermarkingMethod):
    name="HMAC-Signed"
    @staticmethod
    def get_usage() -> str:
        return ("Embeds an HMAC-SHA256-signed secret after the PDF's final %%EOF. "
            "`key` is used as the HMAC key. `position` is ignored.")
    def is_watermark_applicable(self, pdf: PdfSource, position: str | None = None) -> bool:
        """
        Requires a real PDF with at least one page.

        
        """
        try:
            data = load_pdf_bytes(pdf)
            doc = fitz.open(stream=data, filetype="pdf")
            return doc.page_count > 0
        except Exception:
            return False

    


    def add_watermark(self, pdf: PdfSource, secret, key: str, position: str | None = None) -> bytes:
        data = load_pdf_bytes(pdf)
        fernet_key = _derive_fernet_key(key)
        f = Fernet(fernet_key)

        payload = {"secret": secret}
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        token = f.encrypt(payload_bytes)  # encrypted + authenticated + randomized, all in one

        encoded = _MARKER + b":" + token + b":" + _MARKER
        return data + b"\n" + encoded
    
    def read_secret(self, pdf: PdfSource, key: str) -> str:
        data = load_pdf_bytes(pdf)
        start = data.find(_MARKER)
        if start == -1:
            raise SecretNotFoundError("Watermark not found")
        body = data[start + len(_MARKER) + 1:]
        end = body.find(_MARKER)
        if end == -1:
            raise SecretNotFoundError("Malformed watermark: closing marker not found")
        token = body[:end - 1]

        fernet_key = _derive_fernet_key(key)
        f = Fernet(fernet_key)
        try:
            payload_bytes = f.decrypt(token)
        except InvalidToken:
            raise InvalidKeyError("Invalid signature - wrong key or tampered watermark")

        payload = json.loads(payload_bytes)
        return payload["secret"]
