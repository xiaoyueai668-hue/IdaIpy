"""IDAService — RPyC Service exposed by the IDA plugin.

仅暴露三个核心方法:
  exec_code       — 执行代码字符串
  set_workspace   — 设置 workspace 目录
  push_modules    — 接收客户端推送的文件
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile
import threading
import time
import traceback
import uuid
from typing import Any, Callable, Dict, List, Optional

import rpyc

from . import config, log, dbg, log_json
from .executor import ExecMode, ExecutionEngine

_module_dir: Optional[str] = None
_workspace_dir: Optional[str] = None

# ── Async task tracking ─────────────────────────────────────────────────────

_tasks: Dict[str, Dict[str, Any]] = {}
_task_counter = 0
_tasks_lock = threading.Lock()

# Cleanup completed tasks older than 1 hour
_TASK_TTL_SECONDS = 3600


def _cleanup_old_tasks() -> None:
    """Remove completed tasks older than _TASK_TTL_SECONDS."""
    now = time.time()
    with _tasks_lock:
        to_remove = [
            tid for tid, t in _tasks.items()
            if t.get("status") in ("done", "cancelled")
            and (now - t.get("done_at", now)) > _TASK_TTL_SECONDS
        ]
        for tid in to_remove:
            del _tasks[tid]

# Token authentication (set via IDAIPY_TOKEN env var)
_token = os.environ.get("IDAIPY_TOKEN", "")


def _get_peer(conn) -> str:
    try:
        return str(conn._channel.stream.sock.getpeername())
    except Exception:
        return "unknown"


def _check_token(token: Optional[str], conn) -> bool:
    """Validate token. Returns True if valid or auth is disabled."""
    if not _token:
        return True
    if token == _token:
        log_json("auth_success", peer=_get_peer(conn))
        return True
    log_json("auth_failure", peer=_get_peer(conn))
    return False


def _parse_mode(mode: str) -> ExecMode:
    try:
        return ExecMode(mode)
    except ValueError:
        return ExecMode.MAIN_READ


class IDAService(rpyc.Service):
    ALIASES = ["IDAIPY"]

    def __init__(self):
        super().__init__()
        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup,
            daemon=True
        )
        self._cleanup_thread.start()

    @staticmethod
    def _periodic_cleanup() -> None:
        """Periodically cleanup old tasks every 5 minutes."""
        while True:
            time.sleep(300)  # 5 minutes
            _cleanup_old_tasks()

    def on_connect(self, conn):
        # Store conn for use in exposed methods (needed since allow_setattr=False)
        self._conn = conn
        # Note: allow_setattr/delattr are controlled by plugin.py server config.
        # Here we only set connection-specific options.
        conn._config.update({
            "allow_all_attrs": True,
            "allow_public_attrs": True,
            "import_custom_exceptions": True,
            # allow_pickle and allow_setattr/delattr come from plugin.py
        })
        peer = _get_peer(conn)
        log_json("connect", peer=peer)

    def on_disconnect(self, conn):
        peer = _get_peer(conn)
        log_json("disconnect", peer=peer)

    # ── 代码执行 ─────────────────────────────────

    def exposed_exec_code(self, code: str,
                          mode: str = "main_read",
                          token: Optional[str] = None) -> Dict[str, Any]:
        if not _check_token(token, self._conn):
            raise PermissionError("Invalid or missing token")
        m = _parse_mode(mode)
        dbg(f"exec_code mode={m.value} len={len(code)}")
        start = time.monotonic()
        try:
            result = ExecutionEngine.exec_code(code, mode=m)
            duration_ms = int((time.monotonic() - start) * 1000)
            log_json("exec", mode=mode, code_len=len(code),
                     duration_ms=duration_ms,
                     status=result.get("status", "unknown"))
            return result
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            tb = traceback.format_exc()
            log_json(
                "error",
                error_type=type(exc).__name__,
                error_message=str(exc),
                traceback=tb,
                mode=mode,
                code_len=len(code),
                duration_ms=duration_ms,
            )
            raise

    # ── workspace ────────────────────────────────

    def exposed_set_workspace(self, path: str) -> str:
        global _workspace_dir
        # Empty path means clear workspace
        if path == "":
            if _workspace_dir and _workspace_dir in sys.path:
                sys.path.remove(_workspace_dir)
            _workspace_dir = None
            log("Workspace cleared")
            return "Workspace cleared"

        if not os.path.isdir(path):
            raise ValueError(f"Directory does not exist: {path}")

        if _workspace_dir and _workspace_dir in sys.path:
            sys.path.remove(_workspace_dir)

        _workspace_dir = os.path.abspath(path)
        if _workspace_dir not in sys.path:
            sys.path.insert(0, _workspace_dir)

        msg = f"Workspace set to: {_workspace_dir}"
        log(msg)
        return msg

    def exposed_get_workspace(self) -> str:
        return _workspace_dir or ""

    # ── 文件推送 ─────────────────────────────────

    def exposed_push_modules(self, file_map: Dict[str, str]) -> str:
        global _module_dir

        if _module_dir and os.path.isdir(_module_dir):
            self._cleanup_modules()

        _module_dir = tempfile.mkdtemp(prefix="idaipy_modules_")

        count = 0
        for rel_path, content in file_map.items():
            abs_path = os.path.join(_module_dir, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            count += 1

        if _module_dir not in sys.path:
            sys.path.insert(0, _module_dir)

        msg = f"Pushed {count} files to {_module_dir}"
        log(msg)
        return msg

    # ── 异步任务 ────────────────────────────────

    def exposed_exec_async(self, code: str,
                          mode: str = "main_read",
                          token: Optional[str] = None) -> str:
        """Queue a code execution task and return a task_id."""
        if not _check_token(token, self._conn):
            raise PermissionError("Invalid or missing token")
        m = _parse_mode(mode)
        task_id = str(uuid.uuid4())[:8]

        with _tasks_lock:
            _tasks[task_id] = {
                "status": "pending",
                "code": code,
                "mode": m.value,
                "result": None,
                "created_at": time.time(),
                "done_at": None,
            }

        # Run the task in a background thread
        def _run():
            with _tasks_lock:
                _tasks[task_id]["status"] = "running"
            try:
                result = ExecutionEngine.exec_code(code, mode=m)
            except Exception as exc:
                result = {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                    "stdout": "",
                    "stderr": "",
                }
            with _tasks_lock:
                _tasks[task_id]["status"] = "done"
                _tasks[task_id]["result"] = result
                _tasks[task_id]["done_at"] = time.time()
            _cleanup_old_tasks()

        threading.Thread(target=_run, daemon=True).start()
        return task_id

    def exposed_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of an async task."""
        with _tasks_lock:
            task = _tasks.get(task_id)
            if task is None:
                return {"status": "not_found", "task_id": task_id}
            return {
                "status": task["status"],
                "result": task.get("result"),
                "created_at": task.get("created_at"),
            }

    def exposed_cancel_task(self, task_id: str) -> bool:
        """Mark a task as cancelled (if still pending/running)."""
        with _tasks_lock:
            task = _tasks.get(task_id)
            if task is None:
                return False
            if task["status"] in ("pending", "running"):
                task["status"] = "cancelled"
                task["done_at"] = time.time()
                return True
            return False

    def exposed_exec_batch(self, items: List,
                          chunk_size: int = 10,
                          yield_ms: int = 100,
                          token: Optional[str] = None) -> str:
        """Queue a batch execution and return a task_id.

        Items are processed in chunks with yield_ms delay between chunks.
        """
        if not _check_token(token, self._conn):
            raise PermissionError("Invalid or missing token")
        task_id = str(uuid.uuid4())[:8]

        with _tasks_lock:
            _tasks[task_id] = {
                "status": "pending",
                "items": items,
                "chunk_size": chunk_size,
                "yield_ms": yield_ms,
                "result": None,
                "created_at": time.time(),
                "done_at": None,
            }

        def _run():
            results = []
            with _tasks_lock:
                _tasks[task_id]["status"] = "running"
            try:
                for i in range(0, len(items), chunk_size):
                    with _tasks_lock:
                        if _tasks[task_id]["status"] == "cancelled":
                            break
                    chunk = items[i:i + chunk_size]
                    # Execute each item in the chunk
                    for item in chunk:
                        code = f"_idaipy_batch_item = {item!r}"
                        r = ExecutionEngine.exec_code(code, mode=ExecMode.MAIN_READ)
                        results.append(r)
                    if yield_ms > 0:
                        time.sleep(yield_ms / 1000.0)
            except Exception as exc:
                results.append({
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                })
            with _tasks_lock:
                _tasks[task_id]["status"] = "done"
                _tasks[task_id]["result"] = results
                _tasks[task_id]["done_at"] = time.time()

        threading.Thread(target=_run, daemon=True).start()
        return task_id

    def exposed_list_tasks(self) -> List[Dict[str, Any]]:
        """List all async tasks."""
        with _tasks_lock:
            return [
                {
                    "task_id": tid,
                    "status": t["status"],
                    "created_at": t.get("created_at"),
                    "done_at": t.get("done_at"),
                }
                for tid, t in _tasks.items()
            ]

    def exposed_shutdown(self, token: Optional[str] = None) -> str:
        """Gracefully shutdown the server."""
        if not _check_token(token, self._conn):
            raise PermissionError("Invalid or missing token")
        log_json("shutdown")
        # Trigger shutdown via callback
        if _shutdown_callback:
            _shutdown_callback()
        return "shutdown requested"

    # ── MBA Handler 热更新 ─────────────────────────────

    def exposed_reload_mba_handler(self, name: str,
                                   token: Optional[str] = None) -> Dict[str, Any]:
        """热更新指定的 MBA handler。

        Args:
            name: handler 名称（不含 .py），如 "deflatten"
            token: 认证令牌

        Returns:
            Dict: {"status": "ok", "handler": name, "rule_count": n}
        """
        if not _check_token(token, self._conn):
            raise PermissionError("Invalid or missing token")
        return _reload_mba_handler_impl(name)

    def exposed_list_mba_handlers(self) -> List[Dict[str, Any]]:
        """列出所有已加载的 MBA handlers 及其状态。"""
        return _list_mba_handlers()

    def exposed_get_mba_handler_status(self, name: str) -> Dict[str, Any]:
        """获取指定 MBA handler 的状态。"""
        return _get_mba_handler_status(name)

    # ── 内部 ─────────────────────────────────────

    def _cleanup_modules(self):
        global _module_dir
        if _module_dir and os.path.isdir(_module_dir):
            if _module_dir in sys.path:
                sys.path.remove(_module_dir)
            try:
                shutil.rmtree(_module_dir)
            except Exception as exc:
                log(f"Cleanup failed: {exc}")
            _module_dir = None


_shutdown_callback: Optional[Callable] = None


def _request_shutdown():
    if _shutdown_callback:
        _shutdown_callback()


# ── MBA Handler 热更新实现 ────────────────────────────────────────────────────

_mba_handlers: Dict[str, Dict[str, Any]] = {}  # name -> {module, rules, mba_manager_ref}


def _get_mba_manager():
    """获取 ida_mba 的 MbaOptimizerManager 实例。"""
    try:
        # ida_mba 通过 set_manager() 把实例放到这里
        from .ida_mba import get_manager
        return get_manager()
    except ImportError:
        return None


def _reload_mba_handler_impl(name: str) -> Dict[str, Any]:
    """MBA handler 热更新实现。"""
    handlers_dir = os.path.expanduser("~/.idaipy/handlers")
    module_path = os.path.join(handlers_dir, f"{name}.py")

    if not os.path.exists(module_path):
        return {"status": "error", "message": f"Handler not found: {name}.py"}

    # 1. 清理 sys.modules 缓存
    module_key = f"mba_handlers.{name}"
    if module_key in sys.modules:
        del sys.modules[module_key]

    # 2. 重新加载模块
    spec = importlib.util.spec_from_file_location(module_key, module_path)
    if not spec or not spec.loader:
        return {"status": "error", "message": f"Failed to load spec for {name}"}

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_key] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        del sys.modules[module_key]
        return {"status": "error", "message": f"Execution error: {exc}"}

    # 3. 获取 manager 并注册规则
    manager = _get_mba_manager()
    rule_count = 0
    rules = []

    if manager is None:
        # ida_mba 未加载，缓存规则但不注册
        log(f"MBA manager not available, caching rules for {name}")
    else:
        # 获取规则类型（延迟导入，因为依赖 ida_hexrays）
        try:
            from .ida_mba.mba_optimizer import InstructionRule, BlockRule
        except ImportError:
            log(f"mba_optimizer not available (ida_hexrays?)")
            return {"status": "error", "message": "mba_optimizer not available"}

        if hasattr(module, 'RULE'):
            rule = module.RULE()
            rules.append(rule)
            rule_count = 1
            if isinstance(rule, InstructionRule):
                manager.add_ins_rule(rule)
            elif isinstance(rule, BlockRule):
                manager.add_blk_rule(rule)
        elif hasattr(module, 'HANDLERS'):
            for rule_name, rule in module.HANDLERS:
                rules.append(rule)
                rule_count += 1
                if isinstance(rule, InstructionRule):
                    manager.add_ins_rule(rule)
                elif isinstance(rule, BlockRule):
                    manager.add_blk_rule(rule)

    # 4. 追踪已加载的 handler
    _mba_handlers[name] = {
        "module": module,
        "rules": rules,
        "module_key": module_key,
    }

    msg = f"Reloaded handler '{name}' with {rule_count} rule(s)"
    log(msg)
    return {"status": "ok", "handler": name, "rule_count": rule_count}


def _list_mba_handlers() -> List[Dict[str, Any]]:
    """列出所有已加载的 MBA handlers。"""
    result = []
    handlers_dir = os.path.expanduser("~/.idaipy/handlers")

    if not os.path.exists(handlers_dir):
        return result

    for filename in os.listdir(handlers_dir):
        if not filename.endswith('.py') or filename.startswith('__'):
            continue
        name = filename[:-3]
        info = _get_mba_handler_status(name)
        result.append(info)

    return result


def _get_mba_handler_status(name: str) -> Dict[str, Any]:
    """获取指定 MBA handler 的状态。"""
    handlers_dir = os.path.expanduser("~/.idaipy/handlers")
    module_path = os.path.join(handlers_dir, f"{name}.py")

    if not os.path.exists(module_path):
        return {"name": name, "status": "not_found"}

    is_loaded = name in _mba_handlers
    module_key = f"mba_handlers.{name}"
    in_sys_modules = module_key in sys.modules

    rule_count = 0
    if is_loaded:
        rule_count = len(_mba_handlers[name].get("rules", []))

    return {
        "name": name,
        "status": "loaded" if is_loaded else "registered",
        "in_sys_modules": in_sys_modules,
        "rule_count": rule_count,
    }
