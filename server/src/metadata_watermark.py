import base64
import hashlib

import fitz  # PyMuPDF
from watermarking_method import (
    WatermarkingMethod,
    SecretNotFoundError,
    InvalidKeyError,
    load_pdf_bytes,
    PdfSource,
)

MARKER_PREFIX = "TATOU_META::"


class MetadataWatermark(WatermarkingMethod):
    name = "metadata-secret"

    @staticmethod
    def get_usage() -> str:
        return (
            "Hides an encrypted secret inside the PDF's 'keywords' metadata "
            "field. `position` is ignored."
        )

    def _keystream(self, key: str, length: int) -> bytes:
        k = hashlib.sha256(key.encode("utf-8")).digest()
        return (k * (length // len(k) + 1))[:length]

    def _encrypt(self, secret: str, key: str) -> str:
        data = secret.encode("utf-8")
        xored = bytes(a ^ b for a, b in zip(
            data, self._keystream(key, len(data))))
        return base64.urlsafe_b64encode(xored).decode("ascii")

    def _decrypt(self, payload: str, key: str) -> str:
        try:
            data = base64.urlsafe_b64decode(payload.encode("ascii"))
        except Exception as e:
            raise InvalidKeyError(f"Corrupted payload: {e}")
        xored = bytes(a ^ b for a, b in zip(
            data, self._keystream(key, len(data))))
        try:
            return xored.decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidKeyError(
                "Incorrect key: decrypted data is not valid text.")

    def add_watermark(self, pdf: PdfSource, secret: str, key: str, position: str | None = None) -> bytes:
        data = load_pdf_bytes(pdf)
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")

        encrypted = self._encrypt(secret, key)
        payload = f"{MARKER_PREFIX}{encrypted}"

        metadata = doc.metadata or {}
        metadata["keywords"] = payload
        doc.set_metadata(metadata)

        return doc.write()

    def is_watermark_applicable(self, pdf: PdfSource, position: str | None = None) -> bool:
        try:
            data = load_pdf_bytes(pdf)
            fitz.open(stream=data, filetype="pdf")
            return True
        except Exception:
            return False

    def read_secret(self, pdf: PdfSource, key: str) -> str:
        data = load_pdf_bytes(pdf)
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")

        keywords = (doc.metadata or {}).get("keywords", "")
        if not keywords.startswith(MARKER_PREFIX):
            raise SecretNotFoundError(
                "No metadata watermark found in this document.")

        encrypted = keywords[len(MARKER_PREFIX):]
        return self._decrypt(encrypted, key)
