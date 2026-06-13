# IdaIpy 客户端

通过 RPyC 远程调用 IDA Pro API 的 Python 客户端。

## 三种使用模式

### 模式一：独立 CLI

安装后使用 `idaipy` 命令：

```bash
idaipy ping
idaipy status
idaipy run script.py
idaipy run-project my_project
```

### 模式二：Pip 包

```bash
pip install idaipy
```

```python
from idaipy import IdaIpyClient

with IdaIpyClient() as ida:
    r = ida.run_script("script.py")
    r.raise_if_error()
    print(r.stdout)
```

### 模式三：开发模式直接导入

```python
import sys
sys.path.insert(0, "/path/to/idaipy/client/src")
from idaipy import IdaIpyClient
```

## 安装

```bash
# 从源码安装（推荐开发模式）
cd idaipy/client
pip install -e .
```

## 依赖

- Python >= 3.9
- rpyc >= 6.0
