## 新增需求

### 需求：RPyC 安全配置加固
服务端 SHALL 使用最小攻击面的强化 RPyC 配置。

#### 场景：默认禁用 Pickle
- **WHEN** IDA 服务启动
- **THEN** `allow_pickle` 在 protocol_config 中为 `False`
- **AND** `allow_setattr` 为 `False`
- **AND** `allow_delattr` 为 `False`

#### 场景：明确启用 Pickle（用于可信网络）
- **WHEN** 设置了 `IDAIPY_ALLOW_PICKLE=1` 环境变量
- **THEN** 服务端启用 `allow_pickle` 并记录警告日志

### 需求：基于 Token 的身份验证
服务端 SHALL 支持通过环境变量的可选 Token 身份验证。

#### 场景：未设置 Token，无需验证
- **WHEN** 环境变量中未设置 `IDAIPY_TOKEN`
- **THEN** 服务端接受连接时无需 Token 验证

#### 场景：设置了 Token，客户端必须提供
- **WHEN** 服务端设置了 `IDAIPY_TOKEN=secret123`
- **AND** 客户端使用 `IdaIpyClient(token="secret123")` 连接
- **THEN** 连接成功
- **AND** 服务端记录 `event: "auth_success"`

#### 场景：设置了 Token 但客户端提供了错误的 Token
- **WHEN** 服务端设置了 `IDAIPY_TOKEN=secret123`
- **AND** 客户端使用 `IdaIpyClient(token="wrong")` 连接
- **THEN** 服务端抛出 `PermissionError`
- **AND** 服务端记录 `event: "auth_failure", reason: "invalid_token"`
- **AND** 客户端收到 `ConnectionError`，消息为 "Authentication failed"

#### 场景：Token 在 exec_code 时也需要
- **WHEN** 需要 Token 且调用 `exec_code` 时未提供有效 Token
- **THEN** 服务端拒绝调用并抛出 `PermissionError`

### 需求：服务端默认仅绑定 localhost
服务端 SHALL 默认绑定到 127.0.0.1 以保证安全。

#### 场景：默认主机是 localhost
- **WHEN** 服务端以默认配置启动
- **THEN** 仅绑定到 `127.0.0.1`
- **AND** 远程连接被拒绝

#### 场景：显式主机绑定
- **WHEN** 显式设置 `config.HOST = "0.0.0.0"`
- **THEN** 服务端绑定到所有接口
- **AND** 记录有关安全风险的警告
