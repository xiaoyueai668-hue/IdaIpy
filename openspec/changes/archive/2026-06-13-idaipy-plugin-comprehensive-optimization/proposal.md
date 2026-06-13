## 为什么需要这个变更

idaipy-plugin 的核心功能（RPyC 远程调用 IDA API）已经可用，但在实际使用中体验很差：连接管理脆弱（无自动重连、无连接状态查询）、错误处理粗糙（ConnectionRefusedError 没有上下文）、API 返回格式不统一（有时返回 dict 有时返回 None）、CLI 功能残缺（缺少 ping/status 等基础命令）、调试困难（无独立日志文件）、跨平台支持缺失（安装脚本仅支持 macOS）。这些问题使得插件"能用但不好用"，需要全面优化以提升可靠性与开发者体验。

## 变更内容

### 客户端重写
- 重构 `IdaIpyClient`，所有 RPyC 调用统一捕获异常，连接断开时抛出有上下文的 `ConnectionError`
- 增加 `is_connected()` 方法，实时查询连接状态
- 增加 `ping()` / `status()` 便捷方法，返回结构化状态
- 增加**自动重连**机制（默认 3 次重试，指数退避 1s/2s/4s）
- 增加 `wait_task()` / `cancel_task()` 支持异步任务管理
- `run_project()` 拆分清晰：先 `set_workspace` 再执行，无需手动 cleanup
- 返回值统一为 `Result` dataclass：`{status, stdout, stderr, error_type, error_message, traceback}`

### 错误处理与调试
- 所有异常统一捕获，日志写入独立文件 `~/.idaipy/idaipy.log`（可配置路径）
- 连接阶段打印更有用的错误信息（IDA 是否在运行、服务是否启动、端口是否被占用）
- 增加 `--verbose` / `-v` flag 显示完整 traceback
- 服务端增加结构化日志格式（JSON），便于日志收集工具解析

### CLI 增强
- 新增 `idaipy ping` — 健康检查
- 新增 `idaipy status` — 服务状态
- 新增 `idaipy log` — 查看本地日志文件
- `idaipy run` 增加 `--timeout` 参数
- 所有错误输出重定向到 stderr，stdout 仅保留命令输出

### 服务端健壮性
- `exec_async` / `exec_batch` 完善任务队列，支持任务取消
- 增加 `/shutdown` 优雅关闭接口
- 服务端崩溃时自动重启线程，不影响 IDA 本身
- IDA Output 窗口显示连接数、最后活动时间

### 跨平台支持
- 安装脚本支持 Linux（检测 `~/.idapro/`）和 Windows（检测 `C:\Program Files\IDA Pro`）
- 自动检测 IDA 版本（9.0/9.1/9.2）并适配
- 服务端配置 `HOST=127.0.0.1` 默认仅监听 localhost

### 安全加固
- 默认禁用 `allow_pickle`，改用 JSON 序列化
- 增加可选 Token 认证（环境变量 `IDAIPY_TOKEN`）
- RPyC 协议配置收紧（移除 `allow_setattr`/`allow_delattr`）

### 文档
- 更新 PROGRESS.md
- 增加 TROUBLESHOOTING.md（10+ 常见问题）
- 完善 CLAUDE.md 中的架构说明与 API 文档

## 能力清单

### 新增能力
- `idaipy-client-connection`: 可靠的连接管理与自动重连机制
- `idaipy-result-type`: 统一返回结构 `Result` dataclass
- `idaipy-async-tasks`: 异步任务管理与批量执行客户端支持
- `idaipy-structured-logging`: 服务端 JSON 结构化日志 + 本地日志文件
- `idaipy-cli-enhancements`: 增强 CLI（ping/status/log 命令，verbose flag）
- `idaipy-cross-platform`: Linux/Windows 支持与 IDA 版本自动检测
- `idaipy-security-hardening`: Token 认证与 RPyC 安全配置收紧

### 修改能力
（暂无现有能力的需求变更）

## 影响范围

- `client/idaipy_client/client.py` — 重写连接管理、Result 类型、async 支持
- `client/idaipy_client/cli.py` — 新增命令与 flag
- `server/idaipy_server/service.py` — JSON 日志、shutdown 接口、任务队列
- `server/idaipy_server/executor.py` — 任务取消支持
- `server/idaipy_server/plugin.py` — 状态指示
- `scripts/install_plugin.py` — 跨平台检测逻辑
- 新增 `TROUBLESHOOTING.md`
- `PROGRESS.md` — 更新
