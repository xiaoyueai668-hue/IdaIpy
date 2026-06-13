# example-fix

## 新增需求

### 需求: 示例代码使用正确导入路径
`example/` 目录下的所有 Python 文件 SHALL 使用 `from idaipy import ...` 而非 `from idaipy_client import ...`。

#### 场景: 运行示例代码
- **WHEN** 用户运行 `python example/basic_info.py`
- **THEN** 导入 `idaipy` 成功，无 ModuleNotFoundError
