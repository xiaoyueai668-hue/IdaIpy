# IdaIpy 插件框架

## 1. 插件架构

```mermaid
flowchart TB
    subgraph IDA["IDA Pro"]
        IdaIpyPlugin["IdaIpyPlugin<br/>plugin_t"]

        subgraph RPyC_Service["IDAService"]
            ExecCode["exposed_exec_code()"]
            Async["exposed_exec_async()"]
            Batch["exposed_exec_batch()"]
            Workspace["set_workspace()"]
            Shutdown["exposed_shutdown()"]
        end

        subgraph Execution["执行引擎"]
            ExecEngine["ExecutionEngine"]
            MainThread["idaapi.execute_sync()"]
        end

        IdaIpyPlugin --> RPyC_Service
        RPyC_Service --> ExecEngine
        ExecEngine --> MainThread
    end

    subgraph Client["客户端"]
        IdaIpyClient["IdaIpyClient"]
        Result["Result 类型"]
    end

    IdaIpyClient --> |RPyC| ExecCode
    IdaIpyClient --> Result
```

---

## 2. 插件初始化流程

```mermaid
sequenceDiagram
    participant IDA as IDA 启动
    participant Plugin as IdaIpyPlugin
    participant Service as IDAService
    participant RPyC as RPyC Server

    IDA->>Plugin: 加载插件
    Plugin->>Plugin: init()
    Plugin->>Service: 注册 _shutdown_callback
    Plugin->>Plugin: Ctrl+Shift+R 触发 run()

    Note over Plugin: 首次按热键启动服务器

    Plugin->>RPyC: ThreadedServer.start()
    RPyC-->>Plugin: 服务器运行中

    Note over Plugin: 再次按热键停止服务器

    Plugin->>Service: _shutdown_callback()
    Service->>RPyC: server.close()
```

---

## 3. 代码执行流程

```mermaid
sequenceDiagram
    participant Client as IdaIpyClient
    participant RPyC as RPyC Connection
    participant Service as IDAService
    participant Engine as ExecutionEngine
    participant IDA as IDA Main Thread

    Client->>RPyC: exec_code(code, mode)
    RPyC->>Service: exposed_exec_code()
    Service->>Engine: exec_code(code, mode)

    alt 主线程
        Engine->>Engine: 直接执行
    else 非主线程
        Engine->>IDA: execute_sync(fn, MFF_READ/MFF_WRITE)
        IDA-->>Engine: 执行完成
    end

    Engine-->>Service: Result dict
    Service-->>RPyC: Result
    RPyC-->>Client: Result
```

---

## 4. 安全机制

```mermaid
flowchart TB
    subgraph Security["安全机制"]
        direction TB
        Localhost["HOST = 127.0.0.1<br/>仅本地监听"]
        Token["IDAIPY_TOKEN<br/>Token 认证"]
        Pickle["IDAIPY_ALLOW_PICKLE<br/>禁用 pickle"]
        Timeout["TIMEOUT = 300s<br/>请求超时"]
    end
```

---

## 5. 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | 仅本地监听 |
| `PORT` | `7123` | 默认端口 |
| `TIMEOUT` | `300` | 5 分钟超时 |
| `DEBUG` | `False` | 调试日志 |

### 环境变量

| 变量 | 用途 |
|------|------|
| `IDAIPY_TOKEN` | Token 认证 |
| `IDAIPY_LOG_DIR` | 日志目录 `~/.idaipy` |
| `IDAIPY_ALLOW_PICKLE` | 启用 pickle（安全风险） |
