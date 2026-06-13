# client-envvars

## 新增需求

### 需求: 客户端支持环境变量配置
客户端 SHALL 支持通过环境变量配置默认连接参数。

#### 场景: 使用环境变量配置
- **WHEN** 设置 `IDAIPY_HOST=192.168.1.100` 和 `IDAIPY_PORT=7124`
- **THEN** `IdaIpyClient()` 不传参数时使用环境变量中的值

### 需求: 环境变量优先级
显式参数 SHALL 覆盖环境变量。

#### 场景: 参数覆盖环境变量
- **WHEN** 设置 `IDAIPY_PORT=7124` 但调用 `IdaIpyClient(port=7123)`
- **THEN** 使用 `port=7123`
