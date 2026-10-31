"""app/licence.py – Licence validation logic stub. (T-B owns implementation.)"""
from app.config import LICENCE_PROTECTED_PREFIXES


def is_allowed(path: str) -> bool:
    """
    Return True if the request path is allowed given the current licence state.
    Stub always returns True; real implementation checks licence_state table. (T-B)
    """
    return True
