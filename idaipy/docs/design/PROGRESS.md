# IdaIpy Plugin 进度

> 最后更新：2026-06-13

## 组件状态

| 组件 | 状态 | 说明 |
|------|------|------|
| **服务端** | | |
| `idaipy_plugin.py` | ✅ 完成 | 插件加载器（sys.modules 缓存清理） |
| `idaipy_server/plugin.py` | ✅ 完成 | IDA 插件入口（Ctrl+Shift+R 启停） |
| `idaipy_server/service.py` | ✅ 完成 | RPyC Service（远程接口，任务队列，日志） |
| `idaipy_server/executor.py` | ✅ 完成 | 执行引擎（3 种模式，WORKSPACE 注入） |
| `idaipy_server/config.py` | ✅ 完成 | 配置（HOST/PORT/DEBUG） |
| `idaipy_server/__init__.py` | ✅ 完成 | 日志工具（log/dbg/log_json，结构化 JSON 日志） |
| **客户端** | | |
| `idaipy_client/client.py` | ✅ 完成 | RPyC 客户端封装（Result 类型，自动重连，异步任务） |
| `idaipy_client/result.py` | ✅ 完成 | Result dataclass 统一返回类型 |
| `idaipy_client/cli.py` | ✅ 完成 | 命令行工具（idaipy，支持 ping/status/log/run） |
| `pyproject.toml` | ✅ 完成 | 打包配置（pip install） |
| **脚本** | | |
| `install_plugin.py` | ✅ 完成 | 跨平台安装（macOS / Linux / Windows，IDA 9.0/9.1/9.2） |
| `restart_ida.py` | ✅ 完成 | 重启 IDA |
| `test_plugin.py` | ✅ 完成 | 综合测试（46 项） |
| `test_module.py` | ✅ 完成 | 模块依赖测试（15 项） |
| `ida_samples.py` | ✅ 完成 | IDA 只读 API 示例库（9 类） |
| `mrs_scan.py` | ✅ 完成 | MRS 指令扫描示例 |

## 功能清单

### 客户端能力

| 能力 | 状态 | 说明 |
|------|------|------|
| `Result` dataclass | ✅ | 统一返回类型（status/stdout/stderr/error_type/error_message/traceback） |
| `is_connected()` | ✅ | 连接状态查询 |
| `ping()` / `status()` | ✅ | 健康检查和服务状态 |
| 自动重连（3次，指数退避） | ✅ | `_connect_with_retry()`，可配置 retry 参数 |
| `exec_async()` | ✅ | 异步执行，返回 task_id |
| `wait_task()` | ✅ | 轮询等待任务完成，支持 timeout |
| `cancel_task()` | ✅ | 取消运行中任务 |
| `exec_batch()` | ✅ | 分块批量执行 |
| `list_tasks()` | ✅ | 列出所有异步任务 |
| CLI `ping` | ✅ | `idaipy ping` |
| CLI `status` | ✅ | `idaipy status` |
| CLI `log` | ✅ | `idaipy log --lines N --json` |
| CLI `--verbose` / `-v` | ✅ | 显示完整 traceback |
| CLI `--timeout` | ✅ | 执行超时配置 |
| CLI 统一错误格式 | ✅ | `idaipy: error: <message>` |

### 服务端接口

| 接口 | 状态 | 说明 |
|------|------|------|
| `ping()` | ✅ | 健康检查 |
| `get_status()` | ✅ | 服务状态 |
| `exec_code(code, mode, token)` | ✅ | 同步执行（main_write/main_read，Token 认证） |
| `exec_async(code, mode, token)` | ✅ | 异步执行 |
| `exec_batch(items, chunk_size, yield_ms, token)` | ✅ | 分块批量执行 |
| `task_status(id)` | ✅ | 任务状态查询 |
| `cancel_task(id)` | ✅ | 取消任务 |
| `set_workspace(path)` | ✅ | 设置工作区 |
| `get_workspace()` | ✅ | 获取工作区 |
| `push_modules(file_map)` | ✅ | 推送模块文件 |
| `list_tasks()` | ✅ | 列出所有任务 |
| `shutdown(token)` | ✅ | 优雅关闭服务 |
| JSON 结构化日志 | ✅ | 写入 `~/.idaipy/idaipy.log`，支持 `IDAIPY_LOG_DIR` |
| Token 认证 | ✅ | `IDAIPY_TOKEN` 环境变量 |
| 安全加固 | ✅ | 默认禁用 pickle/allow_setattr/allow_delattr |

### 跨平台支持

| 平台 | 状态 | 说明 |
|------|------|------|
| macOS | ✅ | IDA Pro .app 检测 |
| Linux | ✅ | `~/.idapro-{version}/idalinux64/plugins` |
| Windows | ✅ | `C:\Program Files\IDA Pro {version}\plugins` |
| IDA 9.0 | ✅ | 版本自动检测 |
| IDA 9.1 | ✅ | 版本自动检测 |
| IDA 9.2 | ✅ | 版本自动检测 |
| `--ida-path` 覆盖 | ✅ | 手动指定 IDA 路径 |

### 测试覆盖

| 测试文件 | 项数 | 状态 |
|----------|------|------|
| `test_plugin.py` | 46 | ✅ 全部通过 |
| `test_module.py` | 15 | ✅ 全部通过 |
| **合计** | **61** | **✅ 全部通过** |

## 已解决的问题

| 问题 | 解决方案 | 日期 |
|------|----------|------|
| `NameError: IdaIpyPlugin` | 延迟 import + sys.modules 清理 + __pycache__ 排除 | 03-12 |
| `RuntimeError: main thread only` | exec_func + ExecMode.MAIN_READ | 03-12 |
| `get_inf_structure` 不存在 | IDA 9.2 使用 `ida_ida.inf_get_procname()` | 03-12 |
| `string_info_t.strtype` 不存在 | IDA 9.2 使用 `idc.STRTYPE_C` | 03-12 |
| 客户端需要 pip install | sys.path 方式 + pyproject.toml 可选安装 | 03-12 |
| 连接断开时无自动重连 | `_connect_with_retry()` 指数退避（3次，1s/2s/4s） | 06-13 |
| Result 返回格式不统一 | `Result` dataclass 统一所有 exec 返回类型 | 06-13 |
| CLI 缺少 ping/status/log | 新增 `idaipy ping/status/log` 子命令 | 06-13 |
| 服务端无独立日志文件 | JSON 日志写入 `~/.idaipy/idaipy.log` | 06-13 |
| RPyC 安全配置过松 | 默认禁用 pickle/setattr/delattr，Token 认证 | 06-13 |
| 安装脚本仅支持 macOS | 跨平台检测：Linux/Windows，IDA 9.0/9.1/9.2 | 06-13 |

## 待办事项

- [ ] debugpy 远程调试集成
- [ ] WebSocket 协议可选（作为 RPyC 替代）
- [ ] MCP Server 模式（AI Agent 集成）
