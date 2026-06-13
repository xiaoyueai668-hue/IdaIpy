"""ExecutionEngine — 线程安全的代码执行引擎。

仅支持同步执行，通过 ExecMode 选择锁级别:
  MAIN_WRITE — IDA 主线程写锁
  MAIN_READ  — IDA 主线程读锁
"""

from __future__ import annotations

import io
import sys
import threading
import traceback
from enum import Enum
from typing import Any, Dict


class ExecMode(Enum):
    MAIN_WRITE = "main_write"
    MAIN_READ = "main_read"


def _is_main_thread() -> bool:
    try:
        import idaapi
        return idaapi.is_main_thread()
    except (ImportError, AttributeError):
        return True


def _run_sync(fn, mode: ExecMode, timeout: float) -> None:
    if _is_main_thread():
        fn()
        return

    import idaapi
    event = threading.Event()

    def _wrapper():
        try:
            fn()
        finally:
            event.set()

    flag = idaapi.MFF_WRITE if mode == ExecMode.MAIN_WRITE else idaapi.MFF_READ
    idaapi.execute_sync(_wrapper, flag)
    if not event.wait(timeout=timeout):
        raise TimeoutError(f"Timed out after {timeout}s")


def _get_workspace() -> str:
    try:
        from . import service
        return service._workspace_dir or ""
    except Exception:
        return ""


def _capture_exec(code: str, filename: str) -> Dict[str, Any]:
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = cap_out = io.StringIO()
    sys.stderr = cap_err = io.StringIO()
    try:
        env: dict = {
            "__name__": "__main__",
            "WORKSPACE": _get_workspace(),
        }
        exec(compile(code, filename, "exec"), env)
        return {
            "status": "ok",
            "stdout": cap_out.getvalue(),
            "stderr": cap_err.getvalue(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
            "stdout": cap_out.getvalue(),
            "stderr": cap_err.getvalue(),
        }
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class ExecutionEngine:

    @staticmethod
    def exec_code(code: str, filename: str = "<remote>",
                  timeout: float = 300,
                  mode: ExecMode = ExecMode.MAIN_READ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        def _run():
            result.update(_capture_exec(code, filename))

        _run_sync(_run, mode, timeout)
        return result
