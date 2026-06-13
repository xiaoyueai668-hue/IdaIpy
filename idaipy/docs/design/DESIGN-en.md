# IDA Remote Script Execution System Design Document (RPyC Solution)

## 1. Goals

Build an **RPyC**-based IDA remote execution system that supports remote execution of entire projects (with module dependencies).

- **Server (IDA Plugin)**: Runs RPyC Service inside IDA, exposing IDA API and project modules
- **Client (Local Tool)**: Accesses IDA-side modules transparently via RPyC, operating like local calls

### Core Requirements

| Requirement | Solution |
|-------------|----------|
| Entire project modules can be remotely imported | `conn.modules["defuse"]`, automatic dependency resolution |
| Cross-module imports work | Server `sys.path` includes `src/` |
| Complex objects can be returned | RPyC netref remote object proxy |
| Hot reload after code changes | `reload_module()` / `reload_all()` |
| IDA API main thread safety | `execute_sync` wrapper |

---

## 2. Architecture

```mermaid
flowchart LR
    subgraph Client[Client]
        CLI[CLI<br/>idaipy ping<br/>idaipy run]
        ClientLib[IdaIpyClient<br/>.connect()<br/>.modules[]<br/>.exec_code()]
    end

    subgraph Server[IDA Pro]
        IDAService[IDAService<br/>exposed_exec_code()<br/>exposed_ping()<br/>...]
        ExecEngine[ExecutionEngine<br/>execute_sync<br/>stdout/stderr capture]
        ModulePath[sys.path → src/]
    end

    Client -->|RPyC| Server
    ClientLib -->|RPyC| IDAService
    IDAService --> ExecEngine
    IDAService --> ModulePath
```

---

## 3. Server Design

### 3.1 Module Structure

```text
src/
└── server/
    ├── __init__.py
    ├── plugin.py           # IDA plugin entry (PLUGIN_ENTRY)
    ├── service.py          # IDAService (RPyC Service)
    ├── executor.py        # Main thread safe execution engine
    └── config.py          # Configuration
```

### 3.2 Configuration

```python
# config.py
HOST = "127.0.0.1"
PORT = 7123
WORKSPACE = ""   # Auto-detect or manually configure at startup
TIMEOUT = 300    # Default timeout 5 minutes
```

### 3.3 RPyC Service

```python
import rpyc
import sys
import os
import importlib
import time

class IDAService(rpyc.Service):
    """RPyC Service: IDA remote execution interface"""

    ALIASES = ["IDAIPY"]

    def __init__(self):
        super().__init__()
        self._start_time = time.time()
        self._exec_count = 0

    # ── Connection Lifecycle ────────────────────────────

    def on_connect(self, conn):
        conn._config.update({
            "allow_all_attrs": True,
            "allow_public_attrs": True,
            "allow_setattr": True,
            "allow_delattr": True,
            "import_custom_exceptions": True,
            "allow_pickle": True,
        })
        print(f"[IdaIpy] Client connected from {conn._channel.stream.sock.getpeername()}")

    def on_disconnect(self, conn):
        print("[IdaIpy] Client disconnected")

    # ── Code Execution ────────────────────────────────

    def exposed_exec_code(self, code: str) -> dict:
        """Execute code snippet on IDA main thread, return stdout/stderr"""
        self._exec_count += 1
        return ExecutionEngine.exec_code(code)

    def exposed_exec_file(self, path: str) -> dict:
        """Execute script file on IDA main thread"""
        self._exec_count += 1
        return ExecutionEngine.exec_file(path)

    def exposed_exec_on_main(self, func, *args, **kwargs):
        """Execute arbitrary function on IDA main thread"""
        return ExecutionEngine.exec_func(func, *args, **kwargs)

    # ── Module Management ─────────────────────────────

    def exposed_reload_module(self, module_name: str) -> str:
        """Reload specified module"""
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            importlib.reload(mod)
            return f"Reloaded: {module_name}"
        else:
            importlib.import_module(module_name)
            return f"Imported: {module_name}"

    def exposed_reload_all(self) -> str:
        """Reload all project modules (core, defuse, deobf, scanner, micro, plugin)"""
        prefixes = ("core.", "defuse.", "deobf.", "scanner.", "micro.", "plugin.")
        project_modules = sorted(
            name for name in list(sys.modules.keys())
            if any(name.startswith(p) for p in prefixes) or name in prefixes
        )
        reloaded = []
        failed = []
        for name in project_modules:
            try:
                importlib.reload(sys.modules[name])
                reloaded.append(name)
            except Exception as e:
                failed.append(f"{name}: {e}")

        msg = f"Reloaded {len(reloaded)} modules"
        if failed:
            msg += f", {len(failed)} failed: {failed}"
        print(f"[IdaIpy] {msg}")
        return msg

    def exposed_unload_module(self, module_name: str) -> str:
        """Unload module from sys.modules"""
        removed = []
        for name in list(sys.modules.keys()):
            if name == module_name or name.startswith(module_name + "."):
                del sys.modules[name]
                removed.append(name)
        msg = f"Unloaded {len(removed)} modules: {removed}"
        print(f"[IdaIpy] {msg}")
        return msg

    def exposed_list_modules(self) -> list:
        """List all loaded project modules"""
        prefixes = ("core", "defuse", "deobf", "scanner", "micro", "plugin")
        return sorted(
            name for name in sys.modules
            if any(name == p or name.startswith(p + ".") for p in prefixes)
        )

    # ── Info Query ───────────────────────────────────

    def exposed_ping(self) -> dict:
        import idaapi
        return {
            "status": "ok",
            "ida_version": idaapi.get_kernel_version(),
            "python_version": sys.version.split()[0],
            "port": config.PORT,
        }

    def exposed_get_status(self) -> dict:
        """Get detailed server status"""
        import idaapi
        import idc
        uptime = int(time.time() - self._start_time)
        return {
            "status": "running",
            "uptime_seconds": uptime,
            "exec_count": self._exec_count,
            "ida_version": idaapi.get_kernel_version(),
            "python_version": sys.version,
            "input_file": idc.get_input_file_path(),
            "workspace": self.exposed_get_workspace(),
            "loaded_modules": len(self.exposed_list_modules()),
            "sys_path": [p for p in sys.path if "src" in p],
        }

    def exposed_get_workspace(self) -> str:
        """Get current project src/ path"""
        for p in sys.path:
            if p.endswith("/src") or p.endswith("\\src"):
                return p
        return ""

    def exposed_set_workspace(self, workspace_path: str) -> str:
        """Set project path (add src/ to sys.path)"""
        src_path = os.path.join(workspace_path, "src")
        if not os.path.isdir(src_path):
            return f"Error: {src_path} does not exist"
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        return f"Workspace set: {src_path}"

    # ── Server Control ────────────────────────────────

    def exposed_shutdown(self) -> str:
        """Shutdown RPyC server"""
        print("[IdaIpy] Shutdown requested by client")
        import threading
        threading.Timer(0.5, _shutdown_server).start()
        return "Shutting down..."
```

### 3.4 Execution Engine

```python
import sys
import io
import threading
import traceback

class ExecutionEngine:
    """Thread-safe IDA execution engine"""

    @staticmethod
    def exec_code(code: str, filename: str = "<remote>") -> dict:
        """Execute code on IDA main thread"""
        import idaapi
        result = {}
        event = threading.Event()

        def _run():
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = cap_out = io.StringIO()
            sys.stderr = cap_err = io.StringIO()
            try:
                env = {"__name__": "__main__"}
                exec(compile(code, filename, "exec"), env)
                result.update({
                    "status": "ok",
                    "stdout": cap_out.getvalue(),
                    "stderr": cap_err.getvalue(),
                })
            except Exception as e:
                result.update({
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                    "stdout": cap_out.getvalue(),
                    "stderr": cap_err.getvalue(),
                })
            finally:
                sys.stdout, sys.stderr = old_out, old_err
                event.set()

        idaapi.execute_sync(_run, idaapi.MFF_WRITE)
        event.wait(timeout=300)
        return result

    @staticmethod
    def exec_file(path: str) -> dict:
        """Execute file on IDA main thread"""
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        return ExecutionEngine.exec_code(code, filename=path)

    @staticmethod
    def exec_func(func, *args, **kwargs):
        """Execute function on IDA main thread"""
        import idaapi
        result = {"value": None, "error": None}
        event = threading.Event()

        def _run():
            try:
                result["value"] = func(*args, **kwargs)
            except Exception as e:
                result["error"] = str(e)
            finally:
                event.set()

        idaapi.execute_sync(_run, idaapi.MFF_WRITE)
        event.wait(timeout=300)

        if result["error"]:
            raise RuntimeError(result["error"])
        return result["value"]
```

### 3.5 IDA Plugin Entry

```python
import idaapi
import threading
import sys
import os
import rpyc
from rpyc.utils.server import ThreadedServer
from server.service import IDAService
from server import config

_server_instance = None

class IdaIpyPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_KEEP
    wanted_name = "IdaIpy Server"
    wanted_hotkey = "Ctrl-Shift-R"
    comment = "RPyC remote execution server"

    def init(self):
        print("[IdaIpy] Plugin loaded, Ctrl+Shift+R to start/stop server")
        return idaapi.PLUGIN_KEEP

    def run(self, args):
        global _server_instance
        if _server_instance and _server_instance.is_running():
            _server_instance.stop()
        else:
            _server_instance = RPyCServer()
            _server_instance.start()

    def term(self):
        global _server_instance
        if _server_instance:
            _server_instance.stop()

class RPyCServer:
    def __init__(self):
        self._server = None
        self._thread = None
        self._running = False

    def is_running(self):
        return self._running

    def start(self):
        # Set project path
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        workspace = os.path.dirname(os.path.dirname(plugin_dir))
        src_path = os.path.join(workspace, "src")
        if os.path.isdir(src_path) and src_path not in sys.path:
            sys.path.insert(0, src_path)
            print(f"[IdaIpy] Added to sys.path: {src_path}")

        self._server = ThreadedServer(
            IDAService,
            hostname=config.HOST,
            port=config.PORT,
            protocol_config={
                "allow_all_attrs": True,
                "allow_public_attrs": True,
                "allow_pickle": True,
                "sync_request_timeout": config.TIMEOUT,
            },
        )
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True
        print(f"[IdaIpy] RPyC server started on {config.HOST}:{config.PORT}")

    def _run(self):
        try:
            self._server.start()
        except Exception as e:
            print(f"[IdaIpy] Server error: {e}")
        finally:
            self._running = False

    def stop(self):
        if self._server:
            self._server.close()
            self._running = False
            print("[IdaIpy] Server stopped")

def _shutdown_server():
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None

def PLUGIN_ENTRY():
    return IdaIpyPlugin()
```

---

## 4. Client Design

### 4.1 Module Structure

```text
src/
└── client/
    ├── __init__.py
    ├── idaipy_client.py    # RPyC client wrapper
    └── cli.py              # Command-line tool
```

### 4.2 Client API

```python
import rpyc

class IdaIpyClient:
    """RPyC client for remote IDA interaction."""

    def __init__(self, host="127.0.0.1", port=7123):
        self.host = host
        self.port = port
        self._conn = None

    # ── Connection Management ─────────────────────────

    def connect(self) -> 'IdaIpyClient':
        """Establish connection"""
        self._conn = rpyc.connect(
            self.host, self.port,
            config={
                "allow_all_attrs": True,
                "allow_public_attrs": True,
                "sync_request_timeout": 300,
            },
        )
        return self

    def close(self):
        """Close connection"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def is_connected(self) -> bool:
        """Check connection status"""
        if not self._conn:
            return False
        try:
            self._conn.ping()
            return True
        except:
            return False

    def reconnect(self) -> 'IdaIpyClient':
        """Reconnect"""
        self.close()
        return self.connect()

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        self.close()

    # ── Remote Module Access ──────────────────────────

    @property
    def modules(self):
        """Transparently access any Python module on IDA side"""
        return self._conn.modules

    @property
    def idc(self):
        return self._conn.modules["idc"]

    @property
    def idaapi(self):
        return self._conn.modules["idaapi"]

    @property
    def idautils(self):
        return self._conn.modules["idautils"]

    # ── Code Execution ───────────────────────────────

    def exec_code(self, code: str) -> dict:
        """Execute code snippet on IDA main thread"""
        return self._conn.root.exec_code(code)

    def exec_file(self, path: str) -> dict:
        """Execute script file on IDA main thread"""
        return self._conn.root.exec_file(path)

    def exec_on_main(self, func, *args, **kwargs):
        """Execute function on IDA main thread"""
        return self._conn.root.exec_on_main(func, *args, **kwargs)

    # ── Module Management ─────────────────────────────

    def reload(self, module_name: str) -> str:
        """Reload specified module"""
        return self._conn.root.reload_module(module_name)

    def reload_all(self) -> str:
        """Reload all project modules"""
        return self._conn.root.reload_all()

    def unload(self, module_name: str) -> str:
        """Unload specified module (remove from sys.modules)"""
        return self._conn.root.unload_module(module_name)

    def list_modules(self) -> list:
        """List loaded project modules"""
        return list(self._conn.root.list_modules())

    # ── Workspace Management ──────────────────────────

    def set_workspace(self, path: str) -> str:
        """Set project path"""
        return self._conn.root.set_workspace(path)

    def get_workspace(self) -> str:
        """Get current project path"""
        return self._conn.root.get_workspace()

    # ── Info Query ───────────────────────────────────

    def ping(self) -> dict:
        """Health check"""
        return dict(self._conn.root.ping())

    def status(self) -> dict:
        """Detailed status"""
        return dict(self._conn.root.get_status())

    # ── Server Control ───────────────────────────────

    def shutdown_server(self) -> str:
        """Remotely shutdown server"""
        try:
            return self._conn.root.shutdown()
        except EOFError:
            return "Server shut down"
```

### 4.3 Usage Examples

```python
from client import IdaIpyClient

# ── Basic Usage ─────────────────────────────────────

with IdaIpyClient() as ida:
    # Health check
    print(ida.ping())
    # {'status': 'ok', 'ida_version': '8.3', ...}

    # Transparent IDA API calls
    cursor = ida.idc.here()
    print(f"Cursor at: {hex(cursor)}")

    func_ea = ida.idc.get_func_attr(cursor, ida.idc.FUNCATTR_START)
    func_name = ida.idc.get_func_name(func_ea)
    print(f"Function: {func_name} at {hex(func_ea)}")

# ── Using Project Modules ────────────────────────────

with IdaIpyClient() as ida:
    # Def-Use analysis
    defuse = ida.modules["defuse"]
    analyzer = defuse.DefUseAnalyzer()
    result = analyzer.analyze(0x12340)

    # Print chains
    result.print_chains()

    # Find dead code
    dead = result.find_dead_defs()
    for dp in dead:
        print(f"Dead: {dp.variable} @ 0x{dp.ea:X}")

    # Backward trace
    tree = result.trace_backward(0x12380, defuse.RegVar(8))
    result.print_tree(tree)

# ── Deobfuscation Workflow ──────────────────────────

with IdaIpyClient() as ida:
    # Scan
    scanner = ida.modules["scanner.bad_jmp_report"]
    scanner.scan_b_instructions()

    # Fix indirect jumps
    fix = ida.modules["deobf.douyin.fix_indirect"]
    fix.fix_all_indirect_brs()

    # Rebuild functions
    core = ida.modules["core.reanalyze"]
    core.rebuild_all_functions()

# ── Batch Operations (Performance) ─────────────────

with IdaIpyClient() as ida:
    # Many small ops: use exec_code to batch
    r = ida.exec_code("""
import idautils, idc
functions = []
for ea in idautils.Functions():
    name = idc.get_func_name(ea)
    size = idc.get_func_attr(ea, idc.FUNCATTR_END) - ea
    functions.append((hex(ea), name, size))
print(f"Total: {len(functions)} functions")
    """)
    print(r["stdout"])

# ── Module Hot Reload ───────────────────────────────

with IdaIpyClient() as ida:
    # After modifying fix_indirect.py
    ida.reload("deobf.douyin.fix_indirect")

    # Or reload all
    ida.reload_all()

    # Unload module (will reload on next import)
    ida.unload("deobf.douyin")

    # List loaded modules
    for m in ida.list_modules():
        print(m)
```

### 4.4 CLI Tool

```bash
# Health check
$ idaipy ping
OK: IDA 8.3, Python 3.11.5, Port 7123

# Detailed status
$ idaipy status
Running, uptime: 3600s, exec_count: 42
File: /path/to/libfoo.so
Workspace: /Users/me/IdaIpy/src
Loaded modules: 15

# Execute script file
$ idaipy exec src/deobf/douyin/fix_indirect.py
Fixed 15 indirect branches

# Execute code snippet
$ idaipy exec -c "import idc; print(hex(idc.here()))"
0x12345

# Reload module
$ idaipy reload deobf.douyin.fix_indirect
Reloaded: deobf.douyin.fix_indirect

# Reload all
$ idaipy reload-all
Reloaded 15 modules

# Unload module
$ idaipy unload deobf.douyin
Unloaded 3 modules: ['deobf.douyin', 'deobf.douyin.fix_indirect', ...]

# List modules
$ idaipy modules
core.arm64
core.analysis
core.memory
core.patch
core.reanalyze
defuse
defuse.variable
...

# Shutdown server
$ idaipy shutdown
Server shut down
```

---

## 5. Interface Summary

### 5.1 Server Interfaces (IDAService)

| Interface | Parameters | Returns | Description |
|-----------|-------------|---------|-------------|
| `exposed_exec_code` | code: str | dict | Execute code on main thread, return stdout/stderr |
| `exposed_exec_file` | path: str | dict | Execute file on main thread |
| `exposed_exec_on_main` | func, *args | any | Execute function on main thread |
| `exposed_reload_module` | module_name: str | str | Reload specified module |
| `exposed_reload_all` | — | str | Reload all project modules |
| `exposed_unload_module` | module_name: str | str | Unload module and submodules |
| `exposed_list_modules` | — | list | List loaded project modules |
| `exposed_ping` | — | dict | Health check |
| `exposed_get_status` | — | dict | Detailed status |
| `exposed_set_workspace` | path: str | str | Set project path |
| `exposed_get_workspace` | — | str | Get project path |
| `exposed_shutdown` | — | str | Shutdown server |

### 5.2 Client Interfaces (IdaIpyClient)

| Interface | Description |
|-----------|-------------|
| `connect()` | Establish connection |
| `close()` | Close connection |
| `is_connected()` | Check connection status |
| `reconnect()` | Reconnect |
| `modules` | Remote module proxy (`conn.modules`) |
| `idc` / `idaapi` / `idautils` | IDA API shortcuts |
| `exec_code(code)` | Execute code snippet |
| `exec_file(path)` | Execute script file |
| `exec_on_main(func, ...)` | Execute function on main thread |
| `reload(name)` | Reload module |
| `reload_all()` | Reload all |
| `unload(name)` | Unload module |
| `list_modules()` | List modules |
| `set_workspace(path)` | Set project path |
| `get_workspace()` | Get project path |
| `ping()` | Health check |
| `status()` | Detailed status |
| `shutdown_server()` | Shutdown server |

---

## 6. RPyC Usage Notes

### 6.1 Thread Safety

RPyC requests are processed in background threads. IDA APIs **must** be called on the main thread:

```python
# ❌ Direct IDA API call in RPyC thread may crash
def exposed_bad():
    return idc.here()  # May not be on main thread

# ✅ Use execute_sync to switch to main thread
def exposed_good():
    return ExecutionEngine.exec_func(idc.here)
```

**Exception**: Accessing `conn.modules["idc"]` via netref, RPyC automatically executes on server thread. Usually safe for read-only queries, but writes (patching, creating functions) must use `exec_on_main`.

### 6.2 Object Lifecycle

```python
# RPyC netref objects become invalid after connection closes
with IdaIpyClient() as ida:
    result = ida.modules["defuse"].DefUseAnalyzer().analyze(0x1234)
    # result is a netref proxy, usable while connection is alive

# After connection closes, result is invalid!
# If you need to persist data, copy it to local objects within the connection
```

### 6.3 Performance Optimization

```python
# ❌ Slow: each attribute access is a network round-trip
for ea in ida.idautils.Functions():    # Each ea is one network request
    name = ida.idc.get_func_name(ea)   # Another network request

# ✅ Fast: batch operations on server
r = ida.exec_code("""
import idautils, idc
result = [(ea, idc.get_func_name(ea)) for ea in idautils.Functions()]
print(len(result))
""")

# ✅ Fast: use project module to do everything in one RPC
defuse = ida.modules["defuse"]
result = defuse.DefUseAnalyzer().analyze(func_ea)  # Single RPC
```

### 6.4 Security

- Default listens only on `127.0.0.1`, accessible only from localhost
- `allow_all_attrs=True` allows accessing any attribute — **trusted environments only**
- For remote access, add TLS + token authentication

---

## 7. Dependencies

| Location | Dependency | Installation |
|----------|------------|--------------|
| Server (IDA) | `rpyc` | `pip install rpyc` in IDA's Python |
| Client | `rpyc` | `pip install rpyc` |

RPyC is pure Python with no C extensions, compatible with Python 3.6+.
