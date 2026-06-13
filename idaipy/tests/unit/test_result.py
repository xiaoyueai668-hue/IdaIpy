"""Unit tests for Result dataclass."""

import pytest
from idaipy.result import Result


class TestResult:
    """Test Result dataclass."""

    def test_ok_status(self):
        """Result with status='ok' should have ok=True."""
        r = Result(status="ok", stdout="test output")
        assert r.ok is True
        assert r.status == "ok"

    def test_error_status(self):
        """Result with status='error' should have ok=False."""
        r = Result(status="error", error_type="RuntimeError", error_message="test error")
        assert r.ok is False
        assert r.status == "error"

    def test_raise_if_error_raises(self):
        """raise_if_error should raise RuntimeError on error status."""
        r = Result(status="error", error_type="RuntimeError", error_message="test error")
        with pytest.raises(RuntimeError) as exc_info:
            r.raise_if_error()
        assert "RuntimeError" in str(exc_info.value)
        assert "test error" in str(exc_info.value)

    def test_raise_if_error_no_raise_on_ok(self):
        """raise_if_error should not raise on ok status."""
        r = Result(status="ok", stdout="test")
        r.raise_if_error()  # Should not raise

    def test_get_method(self):
        """get() should return attribute value or default."""
        r = Result(status="ok", stdout="test")
        assert r.get("status") == "ok"
        assert r.get("stdout") == "test"
        assert r.get("nonexistent", "default") == "default"

    def test_from_dict_ok(self):
        """from_dict should create Result from dict with ok status."""
        d = {"status": "ok", "stdout": "output"}
        r = Result.from_dict(d)
        assert r.ok is True
        assert r.stdout == "output"
        assert r.status == "ok"

    def test_from_dict_error(self):
        """from_dict should create Result from dict with error status."""
        d = {
            "status": "error",
            "error_type": "ValueError",
            "error_message": "invalid value",
            "traceback": "Traceback..."
        }
        r = Result.from_dict(d)
        assert r.ok is False
        assert r.error_type == "ValueError"
        assert r.error_message == "invalid value"
        assert r.traceback == "Traceback..."

    def test_from_dict_missing_fields(self):
        """from_dict should use defaults for missing fields."""
        d = {}
        r = Result.from_dict(d)
        assert r.status == "error"
        assert r.stdout == ""
        assert r.error_type == ""

    def test_backward_compatibility_get(self):
        """get() allows dict-like access for backward compatibility."""
        r = Result(status="ok", stdout="output")
        # Dict-style access
        assert r.get("status") == "ok"
        assert r.get("stdout") == "output"
