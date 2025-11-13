import hashlib


def hash_password(password: str) -> str:
    """Return SHA256 hash for the provided password."""
    return hashlib.sha256(password.encode()).hexdigest()
