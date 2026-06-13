## 新增需求

### 需求：通过 exec_async 执行异步任务
客户端 SHALL 支持异步代码执行，不阻塞客户端。

#### 场景：提交异步任务并获取 task_id
- **WHEN** `client.exec_async("import time; time.sleep(2); print('done')")` 被调用
- **THEN** 立即返回 `task_id` 字符串

#### 场景：检查异步任务状态（待处理）
- **WHEN** 对运行中的任务调用 `client.task_status(task_id)`
- **THEN** 返回 `{"status": "pending", "task_id": "...", "created_at": "..."}`

#### 场景：检查异步任务状态（已完成）
- **WHEN** 任务完成后调用 `client.task_status(task_id)`
- **THEN** 返回 `{"status": "completed", "task_id": "...", "result": {...}}`
- **AND** `result` 是 `Result` 对象

#### 场景：带超时的任务等待
- **WHEN** 对 2 秒任务调用 `client.wait_task(task_id, timeout=5)`
- **THEN** 任务完成时返回 `Result` 对象
- **AND** 超时时抛出 `TimeoutError`

#### 场景：取消运行中的任务
- **WHEN** 对长时间运行的任务调用 `client.cancel_task(task_id)`
- **THEN** 返回 `{"status": "cancelled", "task_id": "..."}`
- **AND** 后续 `task_status(task_id)` 返回 `{"status": "cancelled", ...}`

### 需求：通过 exec_batch 批量执行
客户端 SHALL 支持批量代码块执行，不长时间阻塞 IDA UI。

#### 场景：批量执行多个条目
- **WHEN** `client.exec_batch(["print(1)", "print(2)", "print(3)"], chunk_size=2, yield_ms=50)` 被调用
- **THEN** 立即返回 `task_id`
- **AND** 可通过 `wait_task(task_id)` 获取结果
- **AND** 结果包含所有 chunk 的组合输出

#### 场景：批量执行完成所有条目
- **WHEN** `wait_task(batch_task_id, timeout=30)` 返回
- **THEN** 所有条目都已执行
- **AND** `result.stdout` 按顺序包含所有 chunk 的输出

### 需求：服务端任务状态跟踪
服务端 SHALL 跟踪任务状态并允许查询。

#### 场景：服务端列出活动任务
- **WHEN** `IDAService.exposed_list_tasks()` 被调用
- **THEN** 返回 `{"tasks": [{"task_id": "...", "status": "pending|running|completed|cancelled", ...}]}`

#### 场景：服务端清理保留期过长的已完成任务
- **WHEN** 任务已完成超过 1 小时
- **THEN** 服务端 MAY 从跟踪中移除任务以防止内存增长
