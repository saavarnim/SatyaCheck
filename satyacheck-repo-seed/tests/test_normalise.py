"""tests/test_normalise.py – Tests for app/normalise.py and app/redact.py."""
import pytest
from app.normalise import normalise, is_valid, InvalidIdentifier
from app.redact import redact


# ════════════════════════════════════════════════════════════════════════
# PHONE
# ════════════════════════════════════════════════════════════════════════

class TestPhoneValid:
    def test_plain_10(self):
        assert normalise("phone", "9876543210") == "+919876543210"

    def test_with_91_prefix(self):
        assert normalise("phone", "919876543210") == "+919876543210"

    def test_with_plus91(self):
        assert normalise("phone", "+919876543210") == "+919876543210"

    def test_with_zero_prefix(self):
        assert normalise("phone", "09876543210") == "+919876543210"

    def test_spaces_and_dashes(self):
        assert normalise("phone", "+91 98765 43210") == "+919876543210"

    def test_dashes(self):
        assert normalise("phone", "98765-43210") == "+919876543210"

    def test_landline_plus91(self):
        assert normalise("phone", "+91 80 4100 2233") == "+918041002233"

    def test_all_four_formats_same_result(self):
        expected = "+919876543210"
        assert normalise("phone", "+91 98765 43210") == expected
        assert normalise("phone", "09876543210") == expected
        assert normalise("phone", "98765-43210") == expected
        assert normalise("phone", "919876543210") == expected

    def test_toll_free_1800(self):
        assert normalise("phone", "1800 1600") == "18001600"

    def test_toll_free_1800_longer(self):
        assert normalise("phone", "1800161920") == "1800161920"

    def test_toll_free_1860(self):
        assert normalise("phone", "1860 419 5555") == "18604195555"

    def test_short_code_1930(self):
        assert normalise("phone", "1930") == "1930"

    def test_short_code_1909(self):
        assert normalise("phone", "1909") == "1909"


class TestPhoneInvalid:
    def test_too_short(self):
        with pytest.raises(InvalidIdentifier):
            normalise("phone", "12345")

    def test_text(self):
        with pytest.raises(InvalidIdentifier):
            normalise("phone", "test")

    def test_all_zeros(self):
        with pytest.raises(InvalidIdentifier):
            normalise("phone", "0000000000")

    def test_all_same_digit(self):
        with pytest.raises(InvalidIdentifier):
            normalise("phone", "1111111111")

    def test_sequential_ascending(self):
        with pytest.raises(InvalidIdentifier):
            normalise("phone", "1234567890")

    def test_sequential_descending(self):
        # 0123456789 is a descending run; first digit 0 also invalid
        with pytest.raises(InvalidIdentifier):
            normalise("phone", "0123456789")

    def test_starts_with_1(self):
        # First digit must be 2-9 for mobile
        with pytest.raises(InvalidIdentifier):
            normalise("phone", "1234567891")

    def test_is_valid_false(self):
        assert is_valid("phone", "12345") is False

    def test_is_valid_true(self):
        assert is_valid("phone", "9876543211") is True


# ════════════════════════════════════════════════════════════════════════
# UPI
# ════════════════════════════════════════════════════════════════════════

class TestUpi:
    def test_lowercase(self):
        assert normalise("upi", "Ram@okaxis") == "ram@okaxis"

    def test_spaces_removed(self):
        assert normalise("upi", "ram @okaxis") == "ram@okaxis"

    def test_uppercase_normalised(self):
        assert normalise("upi", "RAM@OKAXIS") == "ram@okaxis"

    def test_valid_chars(self):
        assert normalise("upi", "user.name_123-x@ybl") == "user.name_123-x@ybl"

    def test_invalid_no_at(self):
        with pytest.raises(InvalidIdentifier):
            normalise("upi", "nooatsign")

    def test_invalid_double_at(self):
        with pytest.raises(InvalidIdentifier):
            normalise("upi", "a@b@c")

    def test_too_short_local(self):
        with pytest.raises(InvalidIdentifier):
            normalise("upi", "a@okaxis")

    def test_handle_starts_with_digit(self):
        with pytest.raises(InvalidIdentifier):
            normalise("upi", "user@1bank")


# ════════════════════════════════════════════════════════════════════════
# URL
# ════════════════════════════════════════════════════════════════════════

class TestUrl:
    def test_strips_www(self):
        assert normalise("url", "http://www.sbikyc.in/pay?utm=sms") == "https://sbikyc.in/pay"

    def test_forces_https(self):
        assert normalise("url", "http://sbikyc.in") == "https://sbikyc.in"

    def test_removes_query(self):
        assert normalise("url", "https://example.in/path?q=1") == "https://example.in/path"

    def test_removes_fragment(self):
        assert normalise("url", "https://example.in/path#section") == "https://example.in/path"

    def test_removes_trailing_slash(self):
        assert normalise("url", "https://example.in/") == "https://example.in"

    def test_adds_https_scheme(self):
        assert normalise("url", "sbikyc.in/pay") == "https://sbikyc.in/pay"

    def test_lowercase_host(self):
        assert normalise("url", "https://SbiKyc.IN/pay") == "https://sbikyc.in/pay"

    def test_no_dot_in_host(self):
        with pytest.raises(InvalidIdentifier):
            normalise("url", "https://localhost/path")

    def test_short_tld(self):
        with pytest.raises(InvalidIdentifier):
            normalise("url", "https://example.a/path")


# ════════════════════════════════════════════════════════════════════════
# SENDER_ID
# ════════════════════════════════════════════════════════════════════════

class TestSenderId:
    def test_8char_strips_first_2(self):
        assert normalise("sender_id", "VMHDFCBK") == "HDFCBK"

    def test_with_hyphen_prefix(self):
        assert normalise("sender_id", "AD-HDFCBK") == "HDFCBK"

    def test_already_6chars(self):
        assert normalise("sender_id", "HDFCBK") == "HDFCBK"

    def test_lowercase_uppercased(self):
        assert normalise("sender_id", "hdfcbk") == "HDFCBK"

    def test_invalid_too_short(self):
        with pytest.raises(InvalidIdentifier):
            normalise("sender_id", "HDFC")

    def test_invalid_special_chars(self):
        with pytest.raises(InvalidIdentifier):
            normalise("sender_id", "HDFC!!")


# ════════════════════════════════════════════════════════════════════════
# UNKNOWN TYPE
# ════════════════════════════════════════════════════════════════════════

class TestUnknownType:
    def test_raises(self):
        with pytest.raises(InvalidIdentifier):
            normalise("email", "user@example.com")

    def test_is_valid_false(self):
        assert is_valid("email", "user@example.com") is False


# ════════════════════════════════════════════════════════════════════════
# REDACT
# ════════════════════════════════════════════════════════════════════════

class TestRedact:
    def test_redacts_phone(self):
        result = redact("Call me at 9876543210 please")
        assert "9876543210" not in result
        assert "[redacted]" in result

    def test_redacts_email(self):
        result = redact("Send to foo@example.com for help")
        assert "foo@example.com" not in result
        assert "[redacted]" in result

    def test_redacts_phone_and_email(self):
        result = redact("Call 9876543211 or mail x@y.com now")
        assert "9876543211" not in result
        assert "x@y.com" not in result

    def test_caps_300_chars(self):
        note = "a" * 500
        assert len(redact(note)) == 300

    def test_empty_string(self):
        assert redact("") == ""

    def test_clean_note_unchanged(self):
        note = "The person asked for money transfer"
        assert redact(note) == note

    def test_redacts_url(self):
        result = redact("Visit https://fake.in/pay now")
        assert "https://fake.in/pay" not in result
        assert "[redacted]" in result

    def test_redacts_upi(self):
        result = redact("Send money to scam@upi123 via UPI")
        assert "scam@upi123" not in result
        assert "[redacted]" in result

    def test_redacts_10digit_run(self):
        result = redact("Account 1234567890 is suspicious")
        assert "1234567890" not in result
