import hashlib
import os
import secrets
import string


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash using PBKDF2-SHA256."""
    if not hashed_password or "$" not in hashed_password:
        return False
    parts = hashed_password.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    iterations = int(parts[1])
    salt = parts[2]
    stored_hash = parts[3]
    computed = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return computed == stored_hash


def get_password_hash(password: str) -> str:
    """Hash a password using PBKDF2-SHA256."""
    salt = os.urandom(16).hex()
    iterations = 260000
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${pw_hash}"


def generate_password() -> str:
    """Generate a random password."""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(12))
