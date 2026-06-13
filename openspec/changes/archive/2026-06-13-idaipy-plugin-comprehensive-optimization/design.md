## 背景

idaipy-plugin 允许外部 Python 脚本通过 RPyC 连接运行中的 IDA Pro，调用其 API 进行逆向分析。当前架构：

```
Client (Python3) --RPyC--> IDA Pro Server (plugin)
     |                              |
 IdaIpyClient                  IDAService
   - connect()                  - exec_code()
   - run_script()              - set_workspace()
   - run_project()             - push_modules()
```

**现状问题**：
- 客户端连接断裂时无自动重连，`ConnectionRefusedError` 信息匮乏
- 客户端缺少 `ping()`/`status()`/`is_connected()` 方法
- `Result` 返回格式不统一（有时 dict 有时 None）
- CLI 命令残缺（ping/status/log 均无）
- 服务端日志输出到 IDA Output 窗口，无独立日志文件
- `allow_pickle=True` + `allow_setattr=True` 存在安全风险
- 安装脚本仅支持 macOS

## 目标 / 非目标

**目标：**
- 客户端连接可靠性：自动重连（3次，指数退避）、连接状态查询、ping/status 方法
- 统一返回类型：所有执行操作返回 `Result` dataclass
- 完整的异步任务客户端支持：wait_task/cancel_task/exec_async/exec_batch
- 增强 CLI：ping/status/log 命令，--verbose flag，--timeout 参数
- 结构化日志：服务端 JSON 日志 + 本地日志文件 `~/.idaipy/idaipy.log`
- 跨平台支持：Linux/Windows 安装脚本，IDA 版本自动检测
- 安全加固：默认禁用 pickle，移除危险 attrs，增加 Token 认证

**非目标：**
- 不改变 RPyC 协议本身（保持向后兼容）
- 不实现 WebSocket 替代方案（已在 PROGRESS.md 待办中）
- 不实现 debugpy 集成（已在 PROGRESS.md 待办中）
- 不支持 IDA 7.x（仅支持 IDA 9.x）

## 技术决策

### Decision 1: Result dataclass 统一返回类型

**选择**：引入 `Result` dataclass，所有 exec 操作返回此类型。

**理由**：当前 `exec_code` 返回 `{"status": "ok"|"error", ...}` dict，调用方需要大量 `if r.get("status") != "ok"` 判断，且错误时部分字段可能缺失。新设计：

```python
@dataclass
class Result:
    status: Literal["ok", "error"]
    stdout: str = ""
    stderr: str = ""
    error_type: str = ""
    error_message: str = ""
    traceback: str = ""

    @property
    def ok(self) -> bool: ...
    def raise_if_error(self) -> None: ...
```

**替代方案**：
- 保持 dict，强制 schema（缺点：调用方仍需手动判断）
- 返回 `tuple[status, stdout, stderr]`（缺点：丢失错误类型信息）

### Decision 2: 自动重连机制

**选择**：客户端内置重连逻辑，默认为 3 次重试，指数退避（1s, 2s, 4s）。

**理由**：IDA 可能因加载文件、分析任务等导致短暂无响应，当前直接抛 `ConnectionRefusedError` 让用户困惑。重连机制让常见临时断开自动恢复。

```python
def _connect_with_retry(self, retries=3, base_delay=1.0):
    for attempt in range(retries):
        try:
            self._conn = rpyc.connect(...)
            return
        except Exception as e:
            if attempt == retries - 1:
                raise ConnectionError(f"Failed after {retries} attempts: {e}")
            time.sleep(base_delay * (2 ** attempt))
```

### Decision 3: 日志架构

**选择**：服务端日志改为 JSON 格式写入文件 `~/.idaipy/idaipy.log`，同时保留 IDA Output 窗口的人类可读输出。

**理由**：
- 人类可读输出便于调试，日志文件便于自动化工具和故障排查
- JSON 格式便于日志收集、监控告警
- 日志路径可配置（环境变量 `IDAIPY_LOG_DIR`）

```python
import logging, json, os

LOG_DIR = os.path.expanduser("~/.idaipy")
os.makedirs(LOG_DIR, exist_ok=True)

_file_handler = logging.FileHandler(os.path.join(LOG_DIR, "idaipy.log"))
_file_handler.setFormatter(logging.Formatter('%(message)s'))

def log(msg: str, json_data: dict = None):
    print(f"[IdaIpy] {msg}")  # IDA Output
    if json_data:
        _logger.info(json.dumps({"msg": msg, **json_data}))
    else:
        _logger.info(msg)
```

### Decision 4: 安全配置

**选择**：收紧 RPyC 协议配置，禁用 `allow_pickle`、`allow_setattr`、`allow_delattr`，增加 Token 认证。

**理由**：
- `allow_pickle=True` 允许反序列化任意 pickled 对象，是 RCE 风险
- `allow_setattr`/`allow_delattr` 允许客户端修改服务端任意属性
- Token 认证通过环境变量 `IDAIPY_TOKEN` 设置

```python
# 服务端
_token = os.environ.get("IDAIPY_TOKEN")

class IDAService(rpyc.Service):
    def exposed_exec_code(self, code: str, mode: str = "main_read", token: str = None):
        if _token and token != _token:
            raise PermissionError("Invalid token")
        ...
```

### Decision 5: 跨平台安装路径检测

**选择**：安装脚本自动检测 OS 和 IDA 安装路径。

```python
def _detect_ida_path():
    if sys.platform == "darwin":
        return "/Applications/MDA.app"
    elif sys.platform.startswith("linux"):
        home = os.path.expanduser("~")
        for version in ["9.2", "9.1", "9.0"]:
            path = f"{home}/idapro-{version}"
            if os.path.isdir(path):
                return path
    elif sys.platform == "win32":
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        for version in ["9.2", "9.1", "9.0"]:
            path = f"{program_files}\\IDA Pro {version}"
            if os.path.isdir(path):
                return path
    raise RuntimeError("IDA Pro not found")
```

## 风险与权衡

**[Risk] Token 认证兼容性** → 客户端未升级时传递 token 会导致接口签名不匹配。**缓解**：Token 参数默认为 None，向后兼容；未设置 token 时服务端不验证。

**[Risk] 日志文件写入失败** → `~/.idaipy` 目录权限问题。**缓解**：写入失败时回退到仅 IDA Output 输出，不阻断主功能。

**[Risk] 指数退避重连可能卡住用户** → 3次重试最多 7s (1+2+4)。**缓解**：提供 `retry=False` 选项允许用户禁用自动重连。

**[Risk] JSON 日志可能暴露敏感分析数据** → 用户代码的 stdout 可能包含敏感信息。**缓解**：JSON 日志仅记录系统事件（连接/断开/exec 调用），不记录用户代码的 stdout 内容。

## 待解决问题

1. **RPyC 连接保活**：是否需要 heartbeat/keepalive 机制防止 NAT 超时？
2. **日志轮转**：日志文件无限增长，是否需要 logrotate 支持？
3. **异步任务队列上限**：是否限制同时存在的异步任务数量？
