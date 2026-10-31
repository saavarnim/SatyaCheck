"""tests/test_wording.py – Ensure prohibited words (scammer, fraud, etc.) don't appear in user-facing code/APIs per docs/06-privacy.md."""
import re
from pathlib import Path
import pytest

PROHIBITED_WORDS = ["scammer", "fraudster", "criminal", "culprit"]


def test_no_prohibited_words_in_app_code():
    """Ensure no user-facing Python files in app/ contain prohibited words."""
    app_dir = Path(__file__).resolve().parent.parent / "app"
    prohibited_pattern = re.compile(r"\b(" + "|".join(PROHIBITED_WORDS) + r")\b", re.IGNORECASE)

    violations = []
    for py_file in app_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        # Remove comments before checking
        lines = [line.split("#")[0] for line in content.splitlines()]
        clean_code = "\n".join(lines)
        matches = prohibited_pattern.findall(clean_code)
        if matches:
            violations.append(f"{py_file.name}: found {set(matches)}")

    assert not violations, f"Prohibited words found in app code: {violations}"


def test_no_prohibited_words_in_api_responses(client):
    """Ensure API responses do not contain prohibited words."""
    # Check health
    resp = client.get("/health")
    assert resp.status_code == 200
    for word in PROHIBITED_WORDS:
        assert word not in resp.text.lower()

    # Check lookup
    resp = client.get("/lookup?type=phone&value=%2B919876543210")
    assert resp.status_code == 200
    for word in PROHIBITED_WORDS:
        assert word not in resp.text.lower()
