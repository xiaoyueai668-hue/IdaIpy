## 新增需求

### 需求：统一返回类型的 Result 数据类
所有执行操作 SHALL 返回统一的 `Result` dataclass。

#### 场景：成功执行返回 ok Result
- **WHEN** `exec_code("print('hello')")` 成功
- **THEN** 返回 `Result(status="ok", stdout="hello\n", stderr="", error_type="", error_message="", traceback="")`

#### 场景：执行失败返回 error Result
- **WHEN** `exec_code("raise ValueError('test')")` 执行
- **THEN** 返回 `Result(status="error", stdout="", stderr="", error_type="ValueError", error_message="test", traceback="...")`
- **AND** `result.ok` 为 `False`
- **AND** `result.raise_if_error()` 抛出 `RuntimeError("ValueError: test")`

#### 场景：Result 可在布尔上下文中使用
- **WHEN** `Result` 被用于 `if result:` 或 `bool(result)`
- **THEN** 真值等于 `result.ok`

#### 场景：Result 保留捕获的 stdout/stderr
- **WHEN** `exec_code("import sys; print('out'); print('err', file=sys.stderr)")` 成功
- **THEN** `result.stdout` 为 `"out\n"`，`result.stderr` 为 `"err\n"`

### 需求：run_script 返回 Result
`run_script(path)` 方法 SHALL 返回 `Result` 对象。

#### 场景：成功执行脚本
- **WHEN** `run_script("my_script.py")` 被调用，脚本打印 "data"
- **THEN** 返回 `Result(status="ok", stdout="data\n", ...)`

#### 场景：脚本有语法错误
- **WHEN** `run_script("bad_script.py")` 被调用，脚本有语法错误
- **THEN** 返回 `Result(status="error", error_type="SyntaxError", ...)`

### 需求：run_project 返回 Result
`run_project(dir, entry)` 方法 SHALL 返回 `Result` 对象。

#### 场景：成功执行项目
- **WHEN** `run_project("my_project", entry="main.py")` 成功
- **THEN** 返回 `Result(status="ok", stdout=..., ...)`

#### 场景：入口文件不存在
- **WHEN** `run_project("my_project", entry="nonexistent.py")` 被调用
- **THEN** 返回 `Result(status="error", error_type="FileNotFoundError", ...)`
