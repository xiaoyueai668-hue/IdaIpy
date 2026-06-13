# unit-tests

## 新增需求

### 需求: Result 测试
`tests/unit/test_result.py` SHALL 测试 Result 数据类的所有方法。

#### 场景: Result.ok 返回正确值
- **WHEN** 创建 `Result(status="ok", stdout="test")`
- **THEN** `result.ok` 返回 `True`

### 需求: 连接重试测试
`tests/unit/test_client.py` SHALL 测试连接重试逻辑。

### 需求: 服务端任务管理测试
`tests/unit/test_service.py` SHALL 测试任务队列管理。

#### 场景: 任务状态查询
- **WHEN** 查询任务状态
- **THEN** 返回正确状态 (pending/running/done/cancelled)
