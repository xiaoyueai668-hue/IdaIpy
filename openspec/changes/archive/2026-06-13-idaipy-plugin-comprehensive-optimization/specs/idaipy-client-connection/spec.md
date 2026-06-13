## 新增需求

### 需求：IdaIpyClient 连接管理
客户端 SHALL 提供可靠的连接管理，包括自动重连、连接状态查询和健康检查方法。

#### 场景：成功连接
- **WHEN** `IdaIpyClient(host, port).connect()` 被调用且 IDA 服务正在运行
- **THEN** 连接建立，`is_connected()` 返回 `True`

#### 场景：连接被拒绝时给出有用错误信息
- **WHEN** `connect()` 被调用但 IDA 服务未运行
- **THEN** 抛出 `ConnectionError`，消息包含 "IDA server not running on {host}:{port}"

#### 场景：临时故障时自动重连
- **WHEN** 已连接但服务临时断开且 `retry=True`（默认）
- **THEN** 客户端最多重试 3 次，指数退避（1s, 2s, 4s）
- **AND** 所有重试失败后抛出 `ConnectionError` 并附带最后的底层错误

#### 场景：禁用重连时不重试
- **WHEN** `connect(retry=False)` 被调用且首次连接失败
- **THEN** 立即抛出 `ConnectionError`，不进行重试

#### 场景：连接状态查询
- **WHEN** `is_connected()` 被调用
- **THEN** 若 RPyC 连接存活则返回 `True`，否则返回 `False`

#### 场景：通过 ping 进行健康检查
- **WHEN** 已连接客户端调用 `client.ping()`
- **THEN** 返回 `{"status": "ok", "ida_version": "...", "python_version": "..."}`
- **AND** 未连接时抛出 `ConnectionError`

#### 场景：状态查询
- **WHEN** 已连接客户端调用 `client.status()`
- **THEN** 返回 `{"status": "running", "python_version": "...", "modules": [...], "workspace": "..."}`
- **AND** 未连接时抛出 `ConnectionError`

#### 场景：上下文管理器关闭连接
- **WHEN** `with IdaIpyClient() as client:` 代码块退出
- **THEN** 连接被关闭，`is_connected()` 返回 `False`
