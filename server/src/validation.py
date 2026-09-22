# Signup validation rules for Tatou, server-side only.

 
from __future__ import annotations
 
import re
 
# Username 
 
USERNAME_MIN_LENGTH = 4
USERNAME_MAX_LENGTH = 32
 
# Allowlist, not blocklist. 
USERNAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{1,30}[A-Za-z0-9]$"
_USERNAME_CHARSET = re.compile(r"^[A-Za-z0-9_-]+$")
_USERNAME_FULL = re.compile(USERNAME_PATTERN)
 
RESERVED_USERNAMES = frozenset({
    "admin", "administrator", "root", "system", "sysadmin",
    "api", "www", "mail", "ftp", "support", "help", "security",
    "tatou", "plugins", "watermarks", "storage", "static",
    "me", "null", "undefined", "anonymous", "guest",
})
 
# Password
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 64
 
 
# Email 
 
EMAIL_MAX_LENGTH = 254  # RFC 5321 practical limit
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
 
 
# Field validators
# Each returns an error message, or none when the value is acceptable.
 
 
def validate_login(value: object) -> str | None:
    if not isinstance(value, str):
        return "Username must be text."
    if len(value) < USERNAME_MIN_LENGTH:
        return f"Username must be at least {USERNAME_MIN_LENGTH} characters."
    if len(value) > USERNAME_MAX_LENGTH:
        return f"Username must be at most {USERNAME_MAX_LENGTH} characters."
    if not _USERNAME_CHARSET.match(value):
        return "Username may only contain letters, numbers, hyphens and underscores."
    if not _USERNAME_FULL.match(value):
        return "Username must start and end with a letter or number."
    if value.lower() in RESERVED_USERNAMES:
        return "That username is reserved."
    return None
 
 
def validate_password(value: object) -> str | None:
    if not isinstance(value, str):
        return "Password must be text."
    # Length is counted first, before any other work touches the value.
    if len(value) < PASSWORD_MIN_LENGTH:
        return f"Password must be at least {PASSWORD_MIN_LENGTH} characters."
    if len(value) > PASSWORD_MAX_LENGTH:
        return f"Password must be at most {PASSWORD_MAX_LENGTH} characters."
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        return "Password may not contain control characters."
    return None

 
 
def validate_email(value: object) -> str | None:
    if not isinstance(value, str):
        return "Email must be text."
    if not value:
        return "Email is required."
    if len(value) > EMAIL_MAX_LENGTH:
        return f"Email must be at most {EMAIL_MAX_LENGTH} characters."
    if not _EMAIL.match(value):
        return "Enter a valid email address."
    return None
 
 
def validate_signup(*, email: object, login: object, password: object) -> dict[str, str]:
    errors: dict[str, str] = {}
    for field, message in (
        ("email", validate_email(email)),
        ("login", validate_login(login)),
        ("password", validate_password(password)),
    ):
        if message:
            errors[field] = message
    return errors


# Document upload (PDF)

UPLOAD_FILENAME_MAX_LENGTH = 200
DISPLAY_NAME_MAX_LENGTH = 200
PDF_MAGIC = b"%PDF-"

# Allowlist, not blocklist: only letters, digits, dot, underscore, hyphen,
# and must start/end alphanumeric.
_UPLOAD_FILENAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._\s-]*[A-Za-z0-9])?$")
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

def sanitize_filename(raw_name: object) -> str | None:
    #Return a filesystem- and shell-safe .pdf filename, or None if unsafe.
    
    if not isinstance(raw_name, str) or not raw_name:
        return None

    # Drop any path component / NUL bytes a client tried to sneak in.
    name = raw_name.replace("\\", "/").split("/")[-1].replace("\x00", "")

    if len(name) > UPLOAD_FILENAME_MAX_LENGTH:
        return None
    if not name.lower().endswith(".pdf"):
        return None
    if not _UPLOAD_FILENAME.match(name):
        return None

    return name

def sanitize_display_name(raw_name: object, fallback: str) -> str:
    #Strip control characters and cap length for a user-supplied display name.
    if not isinstance(raw_name, str) or not raw_name.strip():
        return fallback
    cleaned = "".join(c for c in raw_name.strip() if c.isprintable())
    return cleaned[:DISPLAY_NAME_MAX_LENGTH] or fallback


def is_pdf_file(fileobj) -> bool:
    #Check the actual bytes of an uploaded file, not its extension/mimetype.
    pos = fileobj.tell()
    header = fileobj.read(len(PDF_MAGIC))
    fileobj.seek(pos)
    return header == PDF_MAGIC

#CHECK FILESIZE, return true if lower than 50MB, else false
def is_valid_pdf_size(fileobj) -> bool:
    fileobj.seek(0, 2)
    size = fileobj.tell()
    fileobj.seek(0)     
    return size <= MAX_FILE_SIZE_BYTES