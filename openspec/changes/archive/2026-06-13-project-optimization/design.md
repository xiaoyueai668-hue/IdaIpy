## 背景

项目存在多个优化问题影响可用性、稳定性和可维护性，需要系统性地修复。

## 目标 / 非目标

**目标:**
- 统一版本号到 0.2.0
- 修复所有示例代码的导入路径
- 添加类型注解提高代码质量
- 添加 CI 配置实现自动化测试
- 添加单元测试覆盖核心组件
- 提升 CLI 用户体验
- 优化服务端资源管理
- 增强客户端配置灵活性

**非目标:**
- 不修改核心业务逻辑
- 不添加新功能（仅优化现有功能）
- 不改变 API 接口

## 决策

### 1. 版本号统一

**决策:** 在 `pyproject.toml` 中定义版本，`__init__.py` 从中读取

```toml
# pyproject.toml
[project]
version = "0.2.0"
```

```python
# __init__.py
from importlib.metadata import version
__version__ = version("idaipy")
```

**理由:** 单一数据源，避免不一致。

### 2. 示例代码修复

**决策:** 批量替换 `idaipy_client` → `idaipy`

```bash
find example/ -name "*.py" -exec sed -i '' 's/idaipy_client/idaipy/g' {} \;
```

### 3. 类型注解

**决策:** 使用 Python 3.9+ 内置类型注解，不使用 typing 扩展

```python
def add_path(self, path: str) -> None:
    ...

def _exec_code(self, code: str, mode: str = "main_read") -> Result:
    ...
```

### 4. CI 配置

**决策:** GitHub Actions workflow，触发条件：push/PR to main

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: python -m pytest tests/unit/
```

### 5. 单元测试

**决策:** 使用 `pytest`，测试文件放在 `tests/unit/`

```
tests/
├── unit/           # 新增
│   ├── test_result.py
│   ├── test_client.py
│   └── test_service.py
├── test_plugin.py  # 现有集成测试
└── ...
```

**理由:** 集成测试需要 IDA，不适合 CI。

### 6. CLI --version

**决策:** 使用 argparse 内置 version 参数

```python
parser.add_argument(
    "--version", "-V",
    action="version",
    version=f"%(prog)s {__version__}"
)
```

### 7. 任务清理优化

**决策:** 添加定时清理线程，不依赖任务创建

```python
import threading
import time

class IDAService:
    def __init__(self):
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup,
            daemon=True
        )
        self._cleanup_thread.start()

    def _periodic_cleanup(self):
        while True:
            time.sleep(300)  # 每 5 分钟
            self._cleanup_old_tasks()
```

### 8. 客户端环境变量

**决策:** 支持以下环境变量：

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `IDAIPY_HOST` | 服务器地址 | `127.0.0.1` |
| `IDAIPY_PORT` | 服务器端口 | `7123` |
| `IDAIPY_TIMEOUT` | 默认超时(秒) | `300` |

```python
class IdaIpyClient:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        timeout: int | None = None,
        ...
    ):
        self.host = host or os.environ.get("IDAIPY_HOST", "127.0.0.1")
        self.port = port or int(os.environ.get("IDAIPY_PORT", "7123"))
        self.timeout = timeout or int(os.environ.get("IDAIPY_TIMEOUT", "300"))
```

## 风险 / 权衡

- [风险] 版本号变更可能影响依赖方
  → **缓解:** 在 changelog 中明确说明

- [风险] 添加后台线程可能增加资源消耗
  → **缓解:** 使用 daemon 线程，不阻止进程退出

## 待解决问题

无
