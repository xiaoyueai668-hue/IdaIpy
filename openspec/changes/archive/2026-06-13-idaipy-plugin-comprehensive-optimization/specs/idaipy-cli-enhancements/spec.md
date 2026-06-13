## 新增需求

### 需求：增强 CLI，提供 ping、status 和 log 命令
`idaipy` CLI SHALL 提供额外的健康检查和故障排除命令。

#### 场景：idaipy ping 报告服务器健康状态
- **WHEN** 用户运行 `idaipy ping`
- **THEN** 若服务器可达则打印服务器版本信息并退出 0
- **AND** 若服务器不可达则打印错误并退出 1

#### 场景：idaipy status 报告详细状态
- **WHEN** 用户运行 `idaipy status`
- **THEN** 打印 Python 版本、已加载模块、workspace、活动任务数

#### 场景：idaipy log 显示最近日志条目
- **WHEN** 用户运行 `idaipy log` 或 `idaipy log --lines 50`
- **THEN** 从 `~/.idaipy/idaipy.log` 打印最后 N 行
- **AND** 支持 `--json` flag 输出原始 JSON 行

### 需求：详细错误输出
CLI SHALL 提供 `--verbose` / `-v` flag 以显示详细错误信息。

#### 场景：verbose flag 显示 traceback
- **WHEN** 用户运行 `idaipy run script.py --verbose`
- **AND** 脚本执行失败
- **THEN** 完整 traceback 打印到 stderr

#### 场景：无 verbose flag 显示简短错误
- **WHEN** 用户运行 `idaipy run script.py`
- **AND** 脚本执行失败
- **THEN** 仅打印 `ERROR [ErrorType]: message` 到 stderr

### 需求：run 命令超时参数
`idaipy run` 命令 SHALL 接受 `--timeout` 参数。

#### 场景：长时间运行脚本的自定义超时
- **WHEN** 用户运行 `idaipy run script.py --timeout 60`
- **THEN** 此次执行的客户端超时设置为 60 秒

### 需求：一致的错误输出格式
所有 CLI 错误 SHALL 输出到 stderr 并遵循一致格式。

#### 场景：任何命令的连接错误
- **WHEN** 用户运行任何 `idaipy` 命令但服务器不可达
- **THEN** `idaipy: error: cannot connect to 127.0.0.1:7123` 打印到 stderr
- **AND** 退出码为 1
