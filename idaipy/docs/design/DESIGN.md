# IDA 远程脚本执行系统设计文档（RPyC 方案）

## 1. 目标

构建基于 **RPyC** 的 IDA 远程执行系统，满足整个工程（含模块依赖）的远程执行需求。

- **服务器端（IDA 插件）**：在 IDA 内运行 RPyC Service，暴露 IDA API 和项目模块
- **客户端（本地工具）**：通过 RPyC 透明访问 IDA 端模块，像本地调用一样操作

### 核心需求

| 需求 | 解决方式 |
|------|---------|
| 整个工程模块可远程 import | `conn.modules["defuse"]`，依赖自动解析 |
| 跨模块 import 正常工作 | 服务端 `sys.path` 包含 `src/` |
| 复杂对象可回传 | RPyC netref 远程对象代理 |
| 修改代码后热重载 | `reload_module()` / `reload_all()` |
| IDA API 主线程安全 | `execute_sync` 包装 |

---

## 2. 架构

```mermaid
flowchart LR
    subgraph Client[客户端]
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

## 3. 服务器端设计

### 3.1 模块结构

```text
src/
└── server/
    ├── __init__.py
    ├── plugin.py           # IDA 插件入口 (PLUGIN_ENTRY)
    ├── service.py          # IDAService (RPyC Service)
    ├── executor.py         # 主线程安全执行引擎
    └── config.py           # 配置
```

### 3.2 配置

```python
# config.py
HOST = "127.0.0.1"
PORT = 7123
WORKSPACE = ""   # 启动时自动检测或手动配置
TIMEOUT = 300    # 默认超时 5 分钟
```

### 3.3 RPyC Service

```python
import rpyc
import sys
import os
import importlib
import time

class IDAService(rpyc.Service):
    """RPyC Service：IDA 远程执行接口"""
    
    ALIASES = ["IDAIPY"]
    
    def __init__(self):
        super().__init__()
        self._start_time = time.time()
        self._exec_count = 0
    
    # ── 连接生命周期 ──────────────────────────────
    
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
    
    # ── 代码执行 ──────────────────────────────────
    
    def exposed_exec_code(self, code: str) -> dict:
        """在 IDA 主线程执行代码片段，返回 stdout/stderr"""
        self._exec_count += 1
        return ExecutionEngine.exec_code(code)
    
    def exposed_exec_file(self, path: str) -> dict:
        """在 IDA 主线程执行脚本文件"""
        self._exec_count += 1
        return ExecutionEngine.exec_file(path)
    
    def exposed_exec_on_main(self, func, *args, **kwargs):
        """在 IDA 主线程执行任意函数"""
        return ExecutionEngine.exec_func(func, *args, **kwargs)
    
    # ── 模块管理 ──────────────────────────────────
    
    def exposed_reload_module(self, module_name: str) -> str:
        """重载指定模块"""
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            importlib.reload(mod)
            return f"Reloaded: {module_name}"
        else:
            importlib.import_module(module_name)
            return f"Imported: {module_name}"
    
    def exposed_reload_all(self) -> str:
        """重载所有项目模块（core, defuse, deobf, scanner, micro, plugin）"""
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
        """从 sys.modules 中卸载模块"""
        removed = []
        for name in list(sys.modules.keys()):
            if name == module_name or name.startswith(module_name + "."):
                del sys.modules[name]
                removed.append(name)
        msg = f"Unloaded {len(removed)} modules: {removed}"
        print(f"[IdaIpy] {msg}")
        return msg
    
    def exposed_list_modules(self) -> list:
        """列出所有已加载的项目模块"""
        prefixes = ("core", "defuse", "deobf", "scanner", "micro", "plugin")
        return sorted(
            name for name in sys.modules
            if any(name == p or name.startswith(p + ".") for p in prefixes)
        )
    
    # ── 信息查询 ──────────────────────────────────
    
    def exposed_ping(self) -> dict:
        import idaapi
        return {
            "status": "ok",
            "ida_version": idaapi.get_kernel_version(),
            "python_version": sys.version.split()[0],
            "port": config.PORT,
        }
    
    def exposed_get_status(self) -> dict:
        """获取服务器详细状态"""
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
        """获取当前工程 src/ 路径"""
        for p in sys.path:
            if p.endswith("/src") or p.endswith("\\src"):
                return p
        return ""
    
    def exposed_set_workspace(self, workspace_path: str) -> str:
        """设置工程路径（添加 src/ 到 sys.path）"""
        src_path = os.path.join(workspace_path, "src")
        if not os.path.isdir(src_path):
            return f"Error: {src_path} does not exist"
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        return f"Workspace set: {src_path}"
    
    # ── 服务器控制 ──────────────────────────────────
    
    def exposed_shutdown(self) -> str:
        """关闭 RPyC 服务器"""
        print("[IdaIpy] Shutdown requested by client")
        import threading
        threading.Timer(0.5, _shutdown_server).start()
        return "Shutting down..."
```

### 3.4 执行引擎

```python
import sys
import io
import threading
import traceback

class ExecutionEngine:
    """线程安全的 IDA 执行引擎"""
    
    @staticmethod
    def exec_code(code: str, filename: str = "<remote>") -> dict:
        """在 IDA 主线程执行代码"""
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
        """在 IDA 主线程执行文件"""
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        return ExecutionEngine.exec_code(code, filename=path)
    
    @staticmethod
    def exec_func(func, *args, **kwargs):
        """在 IDA 主线程执行函数"""
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

### 3.5 IDA 插件入口

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
        # 设置工程路径
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

## 4. 客户端设计

### 4.1 模块结构

```text
src/
└── client/
    ├── __init__.py
    ├── idaipy_client.py    # RPyC 客户端封装
    └── cli.py              # 命令行工具
```

### 4.2 客户端 API

```python
import rpyc

class IdaIpyClient:
    """RPyC client for remote IDA interaction."""
    
    def __init__(self, host="127.0.0.1", port=7123):
        self.host = host
        self.port = port
        self._conn = None
    
    # ── 连接管理 ──────────────────────────────────
    
    def connect(self) -> 'IdaIpyClient':
        """建立连接"""
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
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._conn:
            return False
        try:
            self._conn.ping()
            return True
        except:
            return False
    
    def reconnect(self) -> 'IdaIpyClient':
        """重连"""
        self.close()
        return self.connect()
    
    def __enter__(self):
        return self.connect()
    
    def __exit__(self, *args):
        self.close()
    
    # ── 远程模块访问 ──────────────────────────────
    
    @property
    def modules(self):
        """透明访问 IDA 端的任意 Python 模块"""
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
    
    # ── 代码执行 ──────────────────────────────────
    
    def exec_code(self, code: str) -> dict:
        """在 IDA 主线程执行代码片段"""
        return self._conn.root.exec_code(code)
    
    def exec_file(self, path: str) -> dict:
        """在 IDA 主线程执行脚本文件"""
        return self._conn.root.exec_file(path)
    
    def exec_on_main(self, func, *args, **kwargs):
        """在 IDA 主线程执行函数"""
        return self._conn.root.exec_on_main(func, *args, **kwargs)
    
    # ── 模块管理 ──────────────────────────────────
    
    def reload(self, module_name: str) -> str:
        """重载指定模块"""
        return self._conn.root.reload_module(module_name)
    
    def reload_all(self) -> str:
        """重载所有项目模块"""
        return self._conn.root.reload_all()
    
    def unload(self, module_name: str) -> str:
        """卸载指定模块（从 sys.modules 移除）"""
        return self._conn.root.unload_module(module_name)
    
    def list_modules(self) -> list:
        """列出已加载的项目模块"""
        return list(self._conn.root.list_modules())
    
    # ── 工作区管理 ──────────────────────────────────
    
    def set_workspace(self, path: str) -> str:
        """设置工程路径"""
        return self._conn.root.set_workspace(path)
    
    def get_workspace(self) -> str:
        """获取当前工程路径"""
        return self._conn.root.get_workspace()
    
    # ── 信息查询 ──────────────────────────────────
    
    def ping(self) -> dict:
        """健康检查"""
        return dict(self._conn.root.ping())
    
    def status(self) -> dict:
        """详细状态"""
        return dict(self._conn.root.get_status())
    
    # ── 服务器控制 ──────────────────────────────────
    
    def shutdown_server(self) -> str:
        """远程关闭服务器"""
        try:
            return self._conn.root.shutdown()
        except EOFError:
            return "Server shut down"
```

### 4.3 使用示例

```python
from client import IdaIpyClient

# ── 基本使用 ──────────────────────────────────────

with IdaIpyClient() as ida:
    # 健康检查
    print(ida.ping())
    # {'status': 'ok', 'ida_version': '8.3', ...}
    
    # IDA API 透明调用
    cursor = ida.idc.here()
    print(f"Cursor at: {hex(cursor)}")
    
    func_ea = ida.idc.get_func_attr(cursor, ida.idc.FUNCATTR_START)
    func_name = ida.idc.get_func_name(func_ea)
    print(f"Function: {func_name} at {hex(func_ea)}")

# ── 使用项目模块 ─────────────────────────────────

with IdaIpyClient() as ida:
    # Def-Use 分析
    defuse = ida.modules["defuse"]
    analyzer = defuse.DefUseAnalyzer()
    result = analyzer.analyze(0x12340)
    
    # 打印链
    result.print_chains()
    
    # 查找死代码
    dead = result.find_dead_defs()
    for dp in dead:
        print(f"Dead: {dp.variable} @ 0x{dp.ea:X}")
    
    # 向后追踪
    tree = result.trace_backward(0x12380, defuse.RegVar(8))
    result.print_tree(tree)

# ── 反混淆工作流 ─────────────────────────────────

with IdaIpyClient() as ida:
    # 扫描
    scanner = ida.modules["scanner.bad_jmp_report"]
    scanner.scan_b_instructions()
    
    # 修复间接跳转
    fix = ida.modules["deobf.douyin.fix_indirect"]
    fix.fix_all_indirect_brs()
    
    # 重建函数
    core = ida.modules["core.reanalyze"]
    core.rebuild_all_functions()

# ── 批量操作（性能优化） ────────────────────────

with IdaIpyClient() as ida:
    # 大量小操作用 exec_code 一次完成
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

# ── 模块热重载 ───────────────────────────────────

with IdaIpyClient() as ida:
    # 修改了 fix_indirect.py 后
    ida.reload("deobf.douyin.fix_indirect")
    
    # 或者重载所有
    ida.reload_all()
    
    # 卸载模块（下次 import 时重新加载）
    ida.unload("deobf.douyin")
    
    # 查看已加载模块
    for m in ida.list_modules():
        print(m)
```

### 4.4 CLI 工具

```bash
# 健康检查
$ idaipy ping
OK: IDA 8.3, Python 3.11.5, Port 7123

# 详细状态
$ idaipy status
Running, uptime: 3600s, exec_count: 42
File: /path/to/libfoo.so
Workspace: /Users/me/IdaIpy/src
Loaded modules: 15

# 执行脚本文件
$ idaipy exec src/deobf/douyin/fix_indirect.py
Fixed 15 indirect branches

# 执行代码片段
$ idaipy exec -c "import idc; print(hex(idc.here()))"
0x12345

# 重载模块
$ idaipy reload deobf.douyin.fix_indirect
Reloaded: deobf.douyin.fix_indirect

# 重载所有
$ idaipy reload-all
Reloaded 15 modules

# 卸载模块
$ idaipy unload deobf.douyin
Unloaded 3 modules: ['deobf.douyin', 'deobf.douyin.fix_indirect', ...]

# 列出模块
$ idaipy modules
core.arm64
core.analysis
core.memory
core.patch
core.reanalyze
defuse
defuse.variable
...

# 关闭服务器
$ idaipy shutdown
Server shut down
```

---

## 5. 接口总览

### 5.1 服务器端接口（IDAService）

| 接口 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `exposed_exec_code` | code: str | dict | 主线程执行代码，返回 stdout/stderr |
| `exposed_exec_file` | path: str | dict | 主线程执行文件 |
| `exposed_exec_on_main` | func, *args | any | 主线程执行函数 |
| `exposed_reload_module` | module_name: str | str | 重载指定模块 |
| `exposed_reload_all` | — | str | 重载所有项目模块 |
| `exposed_unload_module` | module_name: str | str | 卸载模块及子模块 |
| `exposed_list_modules` | — | list | 列出已加载项目模块 |
| `exposed_ping` | — | dict | 健康检查 |
| `exposed_get_status` | — | dict | 详细状态 |
| `exposed_set_workspace` | path: str | str | 设置工程路径 |
| `exposed_get_workspace` | — | str | 获取工程路径 |
| `exposed_shutdown` | — | str | 关闭服务器 |

### 5.2 客户端接口（IdaIpyClient）

| 接口 | 说明 |
|------|------|
| `connect()` | 建立连接 |
| `close()` | 关闭连接 |
| `is_connected()` | 检查连接状态 |
| `reconnect()` | 重连 |
| `modules` | 远程模块代理（`conn.modules`） |
| `idc` / `idaapi` / `idautils` | IDA API 快捷访问 |
| `exec_code(code)` | 执行代码片段 |
| `exec_file(path)` | 执行脚本文件 |
| `exec_on_main(func, ...)` | 主线程执行函数 |
| `reload(name)` | 重载模块 |
| `reload_all()` | 重载所有 |
| `unload(name)` | 卸载模块 |
| `list_modules()` | 列出模块 |
| `set_workspace(path)` | 设置工程路径 |
| `get_workspace()` | 获取工程路径 |
| `ping()` | 健康检查 |
| `status()` | 详细状态 |
| `shutdown_server()` | 关闭服务器 |

---

## 6. RPyC 使用注意事项

### 6.1 线程安全

RPyC 请求在后台线程处理，IDA API **必须**在主线程调用：

```python
# ❌ 直接在 RPyC 线程中调用 IDA API 可能崩溃
def exposed_bad():
    return idc.here()  # 可能不在主线程

# ✅ 通过 execute_sync 切到主线程
def exposed_good():
    return ExecutionEngine.exec_func(idc.here)
```

**例外**：`conn.modules["idc"]` 通过 netref 访问时，RPyC 自动在服务端线程执行。对于只读查询通常安全，但写操作（patch、创建函数）必须用 `exec_on_main`。

### 6.2 对象生命周期

```python
# RPyC netref 对象在连接关闭后失效
with IdaIpyClient() as ida:
    result = ida.modules["defuse"].DefUseAnalyzer().analyze(0x1234)
    # result 是 netref 代理，连接存活时可用

# 连接关闭后 result 失效！
# 如果需要持久保存，在连接内将数据复制为本地对象
```

### 6.3 性能优化

```python
# ❌ 慢：每次属性访问都是网络往返
for ea in ida.idautils.Functions():    # 每个 ea 一次网络请求
    name = ida.idc.get_func_name(ea)   # 再一次网络请求

# ✅ 快：批量操作在服务端完成
r = ida.exec_code("""
import idautils, idc
result = [(ea, idc.get_func_name(ea)) for ea in idautils.Functions()]
print(len(result))
""")

# ✅ 快：使用项目模块一次性完成
defuse = ida.modules["defuse"]
result = defuse.DefUseAnalyzer().analyze(func_ea)  # 单次 RPC
```

### 6.4 安全性

- 默认仅监听 `127.0.0.1`，只能从本机访问
- `allow_all_attrs=True` 允许访问任意属性 — **仅限可信环境**
- 如需远程访问，应添加 TLS + token 认证

---

## 7. 依赖

| 位置 | 依赖 | 安装 |
|------|------|------|
| 服务器（IDA） | `rpyc` | IDA 的 Python 中 `pip install rpyc` |
| 客户端 | `rpyc` | `pip install rpyc` |

RPyC 是纯 Python，无 C 扩展，兼容 Python 3.6+。
