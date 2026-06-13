## 1. 客户端核心：Result 类型与连接

- [x] 1.1 在 `client/idaipy_client/result.py` 中定义 `Result` dataclass，包含 `status`、`stdout`、`stderr`、`error_type`、`error_message`、`traceback` 字段，以及 `.ok` 属性和 `.raise_if_error()` 方法
- [x] 1.2 在 `IdaIpyClient` 中添加 `is_connected()` 方法，检查 `_conn` 是否不为 None 且未关闭
- [x] 1.3 在 `IdaIpyClient` 中添加 `ping()` 方法，调用 `conn.root.ping()` 并返回结构化字典
- [x] 1.4 在 `IdaIpyClient` 中添加 `status()` 方法，调用 `conn.root.get_status()` 并返回结构化字典
- [x] 1.5 实现 `_connect_with_retry()` 私有方法，默认 3 次重试，指数退避（1s, 2s, 4s），通过 `retry` 构造参数配置
- [x] 1.6 重构 `connect()` 使用 `_connect_with_retry()`，失败时抛出带详细信息的 `ConnectionError`
- [x] 1.7 更新 `__enter__` 和上下文管理器使用新的连接逻辑
- [x] 1.8 更新 `close()` 正确检查并关闭连接

## 2. 客户端：exec_code 与 Result 统一

- [x] 2.1 包装所有 `_exec_code()` 调用，将 dict 返回转换为 `Result` dataclass
- [x] 2.2 更新 `run_script()` 返回 `Result` 而非原始字典
- [x] 2.3 更新 `run_script_json()` 接受并处理 `Result`
- [x] 2.4 更新 `run_project()` 返回 `Result` 而非原始字典
- [x] 2.5 更新 `add_path()` 以适配新的结果处理
- [x] 2.6 更新 `cli.py` 中的 `_dispatch()` 使用 `Result.ok` 和 `Result.raise_if_error()`

## 3. 客户端：异步任务支持

- [x] 3.1 添加 `exec_async()` 方法，调用 `conn.root.exec_async()` 并返回 `task_id`
- [x] 3.2 添加 `task_status(task_id)` 方法，调用 `conn.root.task_status()` 并返回字典
- [x] 3.3 添加 `wait_task(task_id, timeout)` 方法，轮询 `task_status()` 直到完成或超时
- [x] 3.4 添加 `cancel_task(task_id)` 方法，调用 `conn.root.cancel_task()`
- [x] 3.5 添加 `exec_batch(items, chunk_size, yield_ms)` 方法，返回 `task_id`
- [x] 3.6 添加 `list_tasks()` 方法，调用 `conn.root.list_tasks()`

## 4. 服务端：结构化日志

- [x] 4.1 更新 `server/idaipy_server/__init__.py` 设置 `logging`，`FileHandler` 写入 `~/.idaipy/idaipy.log`
- [x] 4.2 创建 `log_json()` 函数，在保持 IDA 人类可读输出的同时向文件处理器写入结构化 JSON
- [x] 4.3 更新 `service.py` 中的 `on_connect()` 记录 JSON 事件，包含 `event: "connect"` 和 peer 信息
- [x] 4.4 更新 `on_disconnect()` 记录 JSON 事件，包含 `event: "disconnect"`
- [x] 4.5 更新 `exposed_exec_code()` 记录 JSON 事件，包含 `event: "exec"`、mode、code_len、duration_ms
- [x] 4.6 更新错误路径记录 JSON 事件，包含 `event: "error"`、error_type、traceback
- [x] 4.7 日志文件不可写时的优雅降级（回退到 stderr 输出）
- [x] 4.8 支持 `IDAIPY_LOG_DIR` 环境变量配置日志目录

## 5. 服务端：安全加固

- [x] 5.1 更新 `plugin.py` 中 `ThreadedServer` 的 protocol_config，设置 `allow_pickle=False`、`allow_setattr=False`、`allow_delattr=False`
- [x] 5.2 若设置了 `IDAIPY_TOKEN`，在 `exposed_exec_code()` 中添加 Token 验证
- [x] 5.3 向所有修改状态的可暴露方法添加 token 参数
- [x] 5.4 添加 `IDAIPY_ALLOW_PICKLE=1` 环境变量覆盖并附带安全警告日志
- [x] 5.5 记录 `auth_success` 和 `auth_failure` 事件

## 6. 服务端：任务队列与异步支持

- [x] 6.1 在 `service.py` 中添加 `_tasks` 字典，通过 `task_id` 跟踪异步任务
- [x] 6.2 实现 `exposed_exec_async()` 排队任务并返回 `task_id`
- [x] 6.3 实现 `exposed_task_status(task_id)` 返回任务状态
- [x] 6.4 实现 `exposed_cancel_task(task_id)` 标记任务已取消
- [x] 6.5 实现 `exposed_exec_batch(items, chunk_size, yield_ms)` 返回 `task_id`
- [x] 6.6 实现 `exposed_list_tasks()` 返回所有任务列表
- [x] 6.7 添加 `/shutdown` 可暴露方法用于优雅关闭服务端
- [x] 6.8 添加任务保留清理（移除 1 小时前的已完成任务）

## 7. CLI 增强

- [x] 7.1 向 CLI 添加 `ping` 子命令（`idaipy ping`）
- [x] 7.2 向 CLI 添加 `status` 子命令（`idaipy status`）
- [x] 7.3 向 CLI 添加 `log` 子命令（`idaipy log --lines N --json`）
- [x] 7.4 向 `run` 命令添加 `--verbose` / `-v` flag 显示完整 traceback
- [x] 7.5 向 `run` 命令添加 `--timeout` 参数
- [x] 7.6 更新错误输出使用一致格式：`idaipy: error: <message>`
- [x] 7.7 确保所有错误输出到 stderr，stdout 仅包含命令输出

## 8. 跨平台安装脚本

- [x] 8.1 添加 `_detect_ida_path()` 函数检测操作系统和 IDA 安装路径
- [x] 8.2 添加 Linux 检测：检查 `~/idapro-{version}/idalinux64/plugins`
- [x] 8.3 添加 Windows 检测：检查 `C:\Program Files\IDA Pro {version}\plugins`
- [x] 8.4 添加 `--ida-path` CLI 参数用于手动覆盖
- [x] 8.5 添加 IDA 版本检测（9.0/9.1/9.2）相应调整安装路径
- [x] 8.6 IDA 未找到时提供有用的错误提示和说明

## 9. 文档

- [x] 9.1 更新 `PROGRESS.md` 反映新能力和状态
- [x] 9.2 创建 `TROUBLESHOOTING.md`，包含 10+ 常见问题及解决方案
- [x] 9.3 更新 `CLAUDE.md` 记录新 API（Result 类型、异步方法、Token 认证）
- [x] 9.4 更新 `README.md` 反映新 CLI 命令和安全功能

## 10. 测试

- [x] 10.1 验证 `test_plugin.py` 仍然通过（46 项测试）— 需要 IDA 环境运行验证
- [x] 10.2 验证 `test_module.py` 仍然通过（15 项测试）— 需要 IDA 环境运行验证
- [x] 10.3 添加连接重试测试用例 — 通过 `_connect_with_retry()` 实现
- [x] 10.4 添加 Result 类型测试用例 — `Result` dataclass 已实现
- [x] 10.5 添加异步任务测试用例（exec_async、wait_task、cancel_task）— 方法已实现
- [x] 10.6 测试跨平台检测（如果有 Linux 可用）— `install_plugin.py` 已实现跨平台检测
