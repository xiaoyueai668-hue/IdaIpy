"""Result dataclass — unified return type for all exec operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


@dataclass
class Result:
    """Unified return type for all exec operations.

    Attributes:
        status: "ok" or "error"
        stdout: captured standard output
        stderr: captured standard error
        error_type: exception class name (error only)
        error_message: exception message (error only)
        traceback: full traceback string (error only)

    Properties:
        ok: True if status is "ok"

    Methods:
        raise_if_error(): Raise RuntimeError if status is "error"
        get(key, default=None): Dict-like access for backward compatibility.
    """

    status: Literal["ok", "error"]
    stdout: str = ""
    stderr: str = ""
    error_type: str = ""
    error_message: str = ""
    traceback: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def raise_if_error(self) -> None:
        """Raise RuntimeError if the result indicates an error."""
        if not self.ok:
            msg = f"{self.error_type}: {self.error_message}"
            if self.traceback:
                msg += f"\n{self.traceback}"
            raise RuntimeError(msg)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for backward compatibility."""
        return getattr(self, key, default)

    @classmethod
    def from_dict(cls, d: dict) -> "Result":
        """Construct a Result from a dict (e.g., legacy exec_code return)."""
        return cls(
            status=d.get("status", "error"),
            stdout=d.get("stdout", ""),
            stderr=d.get("stderr", ""),
            error_type=d.get("error_type", ""),
            error_message=d.get("error_message", ""),
            traceback=d.get("traceback", ""),
        )
