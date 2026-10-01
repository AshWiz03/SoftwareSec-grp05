from __future__ import annotations
import base64
import hashlib

import re
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
    name="HMAC-Text-Render"
    @staticmethod
    def get_usage() -> str:
        return ("Embeds a Fernet-encrypted, authenticated secret as invisible text "
            "inside every page of the PDF at multiple positions with rotating fonts. "
            "`key` derives the encryption key. `position` is ignored.")
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
        token = f.encrypt(secret.encode()).decode()
        zw_payload = _encode_binary(token)
        try:
            doc = fitz.open(stream=data, filetype="pdf")
            if doc.page_count == 0:
                raise ValueError("Cannot watermark an empty PDF.")

            for page in doc:
                for i, pos in enumerate(_POSITIONS):
                    page.insert_text(
                        pos,
                        zw_payload,
                        fontname=_FONTS[i % len(_FONTS)],  # rotate fonts per position
                        fontsize=1,
                        render_mode=3  # invisible — does not render visually
                    )

            return doc.write()

        except Exception as e:
            raise ValueError(f"Failed to apply watermark: {e}")

    
    def read_secret(self, pdf: PdfSource, key: str) -> str:
        data = load_pdf_bytes(pdf)

        # ── Step 1: Extract binary-encoded token from invisible text ──────────
        # Scans every page looking for our markers.
        # Stops at the first match — all positions contain identical content
        # so finding one is sufficient.
        token = None
        try:
            doc = fitz.open(stream=data, filetype="pdf")
            pattern = re.compile(
                re.escape(_START_MARKER) + r'([01]+)' + re.escape(_END_MARKER)
            )
            for page in doc:
                text = page.get_text("text")
                match = pattern.search(text)
                if match:
                    token = _decode_binary(match.group(1))
                    break
        except Exception:
            pass

        if token is None:
            raise SecretNotFoundError(
                "Watermark not found — PDF may not be watermarked, "
                "or the watermark was removed."
            )

        # ── Step 2: Decrypt and verify with Fernet ────────────────────────────
        # InvalidToken fires on EITHER wrong key OR any tampering.
        # This gives us both authentication and confidentiality in one call.
        # KEPT from original method — no changes needed here.
        fernet_key = _derive_fernet_key(key)
        f = Fernet(fernet_key)
        try:
            secret_bytes = f.decrypt(token.encode())
        except InvalidToken:
            raise InvalidKeyError(
                "Invalid signature - wrong key or tampered watermark"
            )

        return secret_bytes.decode()