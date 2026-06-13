# version-sync

## 新增需求

### 需求: 统一版本号
`pyproject.toml` 和 `__init__.py` SHALL 使用相同的版本号。

#### 场景: 版本号同步
- **WHEN** 发布新版本时更新 `pyproject.toml` 的 version 字段
- **THEN** `from idaipy import __version__` 返回相同的版本号
