# project-structure

## 新增需求

### 需求: 最小化 scripts 目录
`scripts/` 目录 SHALL 只包含 `install_plugin.py`，用于安装 IDA 服务端插件。

### 需求: 顶层目录
项目 SHALL 具有以下顶层结构:
- `scripts/` - 仅安装脚本 (install_plugin.py)
- `client/` - Python 客户端包
- `server/` - IDA 服务端插件
- `tools/` - 工具脚本（非 IDA 执行）
- `tests/` - 测试脚本
- `docs/` - 文档
- `example/` - 示例脚本

### 需求: 客户端结构
`client/` 目录 SHALL 包含:
- `src/idaipy/` - 源代码（导入名 `from idaipy import ...`）
- `docs/` - 客户端文档
- `pyproject.toml` - 包配置，包名 `idaipy`
- `README.md` - 客户端概览

### 需求: 服务端结构
`server/` 目录 SHALL 包含:
- `plugin/` - IDA 插件目录
  - `plugin.py` - IDA 插件入口
  - `server/` - 服务端核心代码
  - `docs/` - 服务端文档
- `README.md` - 服务端概览

### 需求: 工具脚本
工具脚本（非 IDA 远程执行的脚本）SHALL 移动到 `tools/`:
- `restart_ida.py`
- `search_ball_selectors.py`

### 需求: 示例脚本
示例脚本 SHALL 放在 `example/` 目录:
- `basic_info.py`
- `my_analysis/` - 示例分析项目
- `mrs_scan.py` - MRS 指令扫描示例
- `ida_samples.py` - IDA 样本脚本

### 需求: 测试脚本
测试脚本 SHALL 移动到 `tests/`:
- `test_plugin.py` - 46 个测试
- `test_module.py` - 15 个测试
- `test_modules/` - 测试辅助模块
- `test_basic.py` - 基本测试
- `test_my_analysis.py` - 分析项目测试

### 需求: 文档组织
`docs/` 目录 SHALL 包含:
- `README.md` / `README-en.md` - 概览和导航
- `design/` - 设计文档
- `client/` - 客户端文档
- `server/` - 服务端文档 (包括 TROUBLESHOOTING)
