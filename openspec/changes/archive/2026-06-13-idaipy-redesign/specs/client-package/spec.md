# client-package

## 新增需求

### 需求: 包安装
客户端 SHALL 可通过 pip 安装 `pip install idaipy` 或开发模式 `pip install -e client/`。

### 需求: 包导入
包 SHALL 可导入为 `from idaipy import IdaIpyClient, Result`。

### 需求: 源码布局
包 SHALL 使用 `src/` 布局，`src/idaipy/` 包含所有 Python 模块。

### 需求: pyproject.toml
包 SHALL 有 `pyproject.toml`:
- 包名: `idaipy`
- Python 版本要求: `>=3.9`
- 依赖: `rpyc>=6.0`
- 入口点: `idaipy=idaipy.cli:main`

### 需求: 三种使用模式
客户端 SHALL 支持三种使用模式:

#### 场景: 模式一 - 独立 CLI
- **WHEN** 用户安装包后运行 `idaipy run script.py`
- **THEN** 脚本在远程 IDA 服务器执行

#### 场景: 模式二 - Pip 包导入
- **WHEN** 用户运行 `from idaipy import IdaIpyClient`
- **THEN** IdaIpyClient 类可用

#### 场景: 模式三 - 开发模式直接导入
- **WHEN** 用户通过 `sys.path.insert(0, "/path/to/client/src")` 插入路径并导入
- **THEN** IdaIpyClient 无需 pip 安装即可使用
