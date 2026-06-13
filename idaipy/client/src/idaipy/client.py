"""IdaIpyClient — 连接 IDA 远程服务，执行本地脚本/项目。

仅两种执行方式:
  run_script(path)          — 读取本地 .py 文件，远程执行
  run_project(dir, entry)   — 设置项目目录，执行入口脚本
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import rpyc

from .result import Result

_IGNORE_DIRS = {"__pycache__", ".git", ".idea", ".venv", "node_modules"}
_TAG = "[IdaIpy]"
_debug = False


def set_debug(on: bool = True) -> None:
    global _debug
    _debug = on


def _dbg(msg: str) -> None:
    if _debug:
        print(f"{_TAG} [DBG] {msg}")


class IdaIpyClient:
    """连接 IDA 远程服务，执行本地 Python 脚本。

    单文件::

        with IdaIpyClient(workspace="/path/to/src") as c:
            r = c.run_script("example/gather_info.py")
            r.raise_if_error()
            print(r.stdout)

    项目::

        with IdaIpyClient() as c:
            r = c.run_project("example/my_project", entry="run.py")
    """

    def __init__(self, host: str | None = None, port: int | None = None,
                 timeout: int | None = None,
                 workspace: str | None = None,
                 debug: bool = False,
                 retry: int = 3,
                 auto_push: bool = True):
        self.host = host or os.environ.get("IDAIPY_HOST", "127.0.0.1")
        self.port = port or int(os.environ.get("IDAIPY_PORT", "7123"))
        self.timeout = timeout or int(os.environ.get("IDAIPY_TIMEOUT", "600"))
        self.workspace = workspace
        self._retry = retry
        self._auto_push = auto_push
        self._conn: Optional[rpyc.Connection] = None
        if debug:
            set_debug(True)

    # ── 连接 ─────────────────────────────────────

    def is_connected(self) -> bool:
        """Check if the connection is active and not closed."""
        if self._conn is None:
            return False
        try:
            # Check if the connection's underlying socket is still open
            self._conn.ping()
            return True
        except Exception:
            return False

    def ping(self) -> Dict[str, Any]:
        """Call conn.root.ping() and return a structured dict."""
        try:
            return {"status": "ok", "pong": self._conn.root.ping()}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> Dict[str, Any]:
        """Call conn.root.get_status() and return a structured dict.

        Returns a dict with 'status' set to 'running' plus server info.
        """
        try:
            data = self._conn.root.get_status()
            result = {"status": "running"}
            if isinstance(data, dict):
                result.update(data)
            return result
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _connect_with_retry(self, retries: int = 3,
                            base_delay: float = 1.0) -> None:
        """Attempt to connect with exponential backoff.

        Args:
            retries: Number of retry attempts (default 3)
            base_delay: Initial delay in seconds (default 1.0)
                      Delays: 1s, 2s, 4s for 3 retries
        """
        last_exc = None
        for attempt in range(retries):
            try:
                self._conn = rpyc.connect(
                    self.host, self.port,
                    config={
                        "allow_all_attrs": True,
                        "allow_public_attrs": True,
                        "sync_request_timeout": self.timeout,
                    },
                )
                return
            except Exception as exc:
                last_exc = exc
                if attempt < retries - 1:
                    delay = base_delay * (2 ** attempt)
                    _dbg(f"Connection attempt {attempt + 1} failed: {exc}, "
                         f"retrying in {delay}s...")
                    time.sleep(delay)
        raise ConnectionError(
            f"Failed to connect to {self.host}:{self.port} after {retries} "
            f"attempts: {last_exc}"
        )

    def connect(self) -> "IdaIpyClient":
        _dbg(f"connecting {self.host}:{self.port}")
        self._connect_with_retry(retries=self._retry)
        if self.workspace:
            self.set_workspace(self.workspace)
        return self

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def __enter__(self) -> "IdaIpyClient":
        return self.connect()

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def reconnect(self) -> "IdaIpyClient":
        """Close existing connection and reconnect."""
        self.close()
        return self.connect()

    # ── 环境 ─────────────────────────────────────

    def set_workspace(self, path: Optional[str] = None) -> str:
        """设置服务端 workspace（加入 sys.path）。"""
        ws = path or self.workspace
        if not ws:
            raise ValueError("No workspace path provided")
        return str(self._conn.root.set_workspace(ws))

    def get_workspace(self) -> str:
        """Get the current workspace path."""
        return str(self._conn.root.get_workspace())

    def clear_workspace(self) -> str:
        """Clear the workspace (remove from sys.path)."""
        # Implementation: call set_workspace with empty or just reset
        return str(self._conn.root.set_workspace(""))

    def add_path(self, path: str) -> str:
        """追加目录到远程 sys.path（不替换 workspace）。"""
        r = self._exec_code(
            f"import sys, os\n"
            f"p = os.path.abspath({path!r})\n"
            f"if p not in sys.path: sys.path.insert(0, p)\n"
            f"print(p)",
        )
        return r.stdout.strip()

    # ── 执行 ─────────────────────────────────────

    def run_script(self, script_path: str,
                   mode: str = "main_read") -> Result:
        """读取本地 .py 文件，远程执行。

        Returns:
            Result dataclass with status, stdout, stderr, error_type,
            error_message, traceback.
        """
        with open(os.path.abspath(script_path), "r", encoding="utf-8") as f:
            code = f.read()
        return self._exec_code(code, mode=mode)

    def run_script_json(self, script_path: str,
                        mode: str = "main_read") -> Any:
        """执行本地脚本，解析最后一行 stdout 为 JSON 返回。"""
        r = self.run_script(script_path, mode=mode)
        r.raise_if_error()
        stdout = r.stdout.strip()
        if not stdout:
            return None
        return json.loads(stdout.rsplit("\n", 1)[-1])

    def run_project(self, project_dir: str,
                    entry: str = "main.py",
                    mode: str = "main_read",
                    use_workspace: bool = True) -> Result:
        """设置项目目录并执行入口脚本。

        workspace 模式 (默认): 将目录加入 sys.path
        push 模式: 读取所有 .py 推送到服务端

        自动清理项目内同名模块缓存，避免跨项目导入冲突。

        Returns:
            Result dataclass.
        """
        project_dir = os.path.abspath(project_dir)

        mod_names = []
        for fname in os.listdir(project_dir):
            if fname.endswith(".py") and fname != entry:
                mod_names.append(fname[:-3])
        if mod_names:
            cleanup = "import sys\n" + "\n".join(
                f"sys.modules.pop({n!r}, None)" for n in mod_names
            )
            self._exec_code(cleanup)

        if use_workspace:
            self.set_workspace(project_dir)
        else:
            self._push_modules(project_dir)

        with open(os.path.join(project_dir, entry), "r", encoding="utf-8") as f:
            code = f.read()
        return self._exec_code(code, mode=mode)

    # ── 内部 ─────────────────────────────────────

    def _exec_code(self, code: str,
                   mode: str = "main_read") -> Result:
        _dbg(f"exec mode={mode} len={len(code)}")
        return Result.from_dict(self._conn.root.exec_code(code, mode))

    def _push_modules(self, src_dir: str) -> str:
        file_map: Dict[str, str] = {}
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, src_dir)
                with open(abs_path, "r", encoding="utf-8") as fh:
                    file_map[rel_path] = fh.read()
        return str(self._conn.root.push_modules(file_map))

    # ── 异步任务 ─────────────────────────────────

    def exec_async(self, code: str,
                   mode: str = "main_read") -> str:
        """Execute code asynchronously, returning a task_id.

        Use task_status(task_id) to poll for results.
        """
        return self._conn.root.exec_async(code, mode)

    def task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of an async task.

        Returns:
            dict with 'status' ('pending'|'running'|'done'|'cancelled'),
            'result' (Result dict when done), etc.
        """
        return dict(self._conn.root.task_status(task_id))

    def wait_task(self, task_id: str,
                  timeout: Optional[float] = None,
                  poll_interval: float = 0.25) -> Dict[str, Any]:
        """Poll task_status until complete or timeout.

        Args:
            task_id: Task ID from exec_async
            timeout: Maximum seconds to wait (None = no limit)
            poll_interval: Seconds between polls (default 0.25)

        Returns:
            Dict with 'state' ('done'/'cancelled'/'error') and 'result' (Result dict).
            For backward compatibility with existing tests.
        """
        import time
        start = time.monotonic()
        while True:
            status = self.task_status(task_id)
            state = status.get("status", "unknown")
            if state == "done":
                return {
                    "state": "done",
                    "result": status.get("result", {}),
                }
            elif state == "cancelled":
                return {
                    "state": "cancelled",
                    "result": {
                        "status": "error",
                        "error_type": "CancelledError",
                        "error_message": f"Task {task_id} was cancelled",
                    },
                }
            elif state not in ("pending", "running", "unknown"):
                return {
                    "state": "error",
                    "result": {
                        "status": "error",
                        "error_type": "UnknownStateError",
                        "error_message": f"Unexpected task state: {state}",
                    },
                }
            if timeout is not None and (time.monotonic() - start) >= timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
            time.sleep(poll_interval)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running async task.

        Returns:
            True if cancellation was successful.
        """
        return bool(self._conn.root.cancel_task(task_id))

    def exec_batch(self, items: list,
                   chunk_size: int = 10,
                   yield_ms: int = 100) -> str:
        """Execute a batch of items asynchronously.

        Args:
            items: List of items to process
            chunk_size: Number of items per chunk
            yield_ms: Milliseconds to wait between chunks

        Returns:
            task_id for tracking the batch
        """
        return self._conn.root.exec_batch(items, chunk_size, yield_ms)

    def list_tasks(self) -> list:
        """List all async tasks on the server.

        Returns:
            List of task info dicts.
        """
        return list(self._conn.root.list_tasks())
