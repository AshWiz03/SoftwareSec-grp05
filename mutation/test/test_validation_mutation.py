import io
import pytest
from validation import (
    validate_login,
    validate_password,
    validate_email,
    validate_signup,
    sanitize_filename,
    sanitize_display_name,
    is_pdf_file,
    is_valid_pdf_size,
)

#Validation login input (For create-user)
def test_validate_login_valid():
    assert validate_login("Mikael123") is None

def test_validate_login_too_short():
    assert validate_login("opa") is not None

def test_validate_login_reserved():
    assert validate_login("admin") is not None


#Validation password input (For create-user)
def test_validate_password_valid():
    assert validate_password("Mikaelpwd123") is None

def test_validate_password_too_short():
    assert validate_password("lko") is not None

CONTROL_MSG = "Password may not contain control characters." #Should hit the correct condition
@pytest.mark.parametrize("char", ["\x00", "\t", "\n", "\r", "\x1f", "\x7f"])
def test_validate_password_reject_ascii_control(char):
    assert validate_password("TestPassword" + char) == CONTROL_MSG

@pytest.mark.parametrize("char", ["\x80", "\x85", "\x9f"])
def test_validate_password_rejects_c1_control_chars(char):
    assert validate_password("TestPassword" + char) == CONTROL_MSG
#latin 1 punctuation and symbols
@pytest.mark.parametrize("char", [" ", "~", "å", "ä", "ö", "£", "§", "©"])
def test_validate_password_allows_printable_chars(char):
    assert validate_password("TestPassword" + char) is None

#Validation email input (For create-user)
def test_validate_email_valid():
    assert validate_email("mikael@testing.com") is None

def test_validate_email_missing_at():
    assert validate_email("userexample.com") is not None

def test_validate_email_empty():
    assert validate_email("") is not None

#Validation signup 
USERNAME_MIN_LENGTH = 4
USERNAME_MAX_LENGTH = 32

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 64

def test_validate_signup_all_valid():
    errors = validate_signup(
        email="user@example.com",
        login="testuser123",
        password="ValidPassword123",
    )
    assert errors == {}

def test_validate_signup_all_invalid():
    errors = validate_signup(email="bad", login="x", password="short")
    assert errors["email"] == "Enter a valid email address."
    assert errors["login"] == f"Username must be at least {USERNAME_MIN_LENGTH} characters."
    assert errors["password"] == f"Password must be at least {PASSWORD_MIN_LENGTH} characters."


#Validation sanitize filename
def test_sanitize_filename_valid():
    assert sanitize_filename("testdocument.pdf") == "testdocument.pdf"

def test_sanitize_filename_invalid_filetype():
    assert sanitize_filename("testdocument.sh") is None

def test_sanitize_filename_invalid_char():
    assert sanitize_filename("../../run.sh") is None

#Validation sanitize display name
def test_sanitize_display_name_valid():
    fallback = "untitled"
    assert sanitize_display_name("testdocument", fallback) == "testdocument"

def test_sanitize_display_name_blank_uses_fallback():
    fallback = "untitled"
    assert sanitize_display_name("   ", fallback) == "untitled"

# Test is_pdf_file
def test_is_pdf_file_true():
    f = io.BytesIO(b"%PDF-1.4\n...")
    assert is_pdf_file(f) is True

def test_is_pdf_file_false():
    f = io.BytesIO(b"not a pdf")
    assert is_pdf_file(f) is False

#Test is_valid_pdf_size
def test_is_valid_pdf_size_small_file():
    f = io.BytesIO(b"x" * 1000)
    assert is_valid_pdf_size(f) is True

def test_is_valid_pdf_size_oversized():
    f = io.BytesIO(b"x" * (51 * 1024 * 1024))
    assert is_valid_pdf_size(f) is False