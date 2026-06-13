## 新增需求

### 需求：服务端结构化 JSON 日志
服务端 SHALL 向本地文件发送结构化 JSON 日志，同时保留人类可读的 IDA Output。

#### 场景：首次日志消息时创建日志文件
- **WHEN** 服务启动并发出第一条日志消息
- **THEN** 若可写则创建 `~/.idaipy/idaipy.log` 文件
- **AND** 消息以 JSON 格式写入：`{"ts": "ISO8601", "level": "INFO", "msg": "...", "context": {...}}`

#### 场景：记录连接事件
- **WHEN** 客户端连接或断开
- **THEN** 写入 JSON 日志条目，包含 `event: "connect|disconnect"` 和 `peer: "ip:port"`

#### 场景：记录执行事件
- **WHEN** `exec_code` 被调用
- **THEN** JSON 日志条目包含 `event: "exec", mode: "...", code_len: N, duration_ms: M`

#### 场景：记录错误事件及 traceback
- **WHEN** 执行抛出异常
- **THEN** JSON 日志条目包含 `event: "error", error_type: "...", traceback: "..."`

#### 场景：日志写入失败时优雅降级
- **WHEN** 日志文件无法写入（权限错误）
- **THEN** 日志继续输出到 IDA Output 窗口
- **AND** 不对调用代码抛出异常

### 需求：日志目录可配置
日志目录 SHALL 可通过环境变量配置。

#### 场景：自定义日志目录
- **WHEN** 设置了 `IDAIPY_LOG_DIR=/tmp/my_logs`
- **THEN** 日志文件创建在 `/tmp/my_logs/idaipy.log`

### 需求：调试模式增加详细程度
当 `DEBUG=True` 时，服务端 SHALL 记录所有 RPyC 请求和响应。

#### 场景：启用调试日志
- **WHEN** `config.DEBUG = True`
- **THEN** 每次 RPC 调用记录输入参数和返回值摘要
