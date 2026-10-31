"""app/normalise.py – Stub: canonicalise phone/upi/url/sender_id and validation. (T1)"""


def normalise(identifier_type: str, value: str) -> str:
    """Return canonical form of the identifier, or raise ValueError for invalid input."""
    raise NotImplementedError("T1")


def is_valid(identifier_type: str, value: str) -> bool:
    """Return True if value is a syntactically valid identifier of the given type."""
    raise NotImplementedError("T1")
