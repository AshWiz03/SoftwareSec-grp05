import io
from src.validation import (
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

#Validation email input (For create-user)
def test_validate_email_valid():
    assert validate_email("mikael@testing.com") is None

def test_validate_email_missing_at():
    assert validate_email("userexample.com") is not None

def test_validate_email_empty():
    assert validate_email("") is not None

#Validation signup 
def test_validate_signup_all_valid():
    errors = validate_signup(
        email="user@example.com",
        login="testuser123",
        password="ValidPassword123",
    )
    assert errors == {}

def test_validate_signup_all_invalid():
    errors = validate_signup(email="bad", login="x", password="short")
    assert "email" in errors
    assert "login" in errors
    assert "password" in errors


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