# client-cli

## 新增需求

### 需求: CLI 入口点
系统 SHALL 提供命令行界面，安装后可通过 `idaipy` 命令访问。

### 需求: CLI 子命令
CLI SHALL 支持以下子命令:
- `ping` - 健康检查
- `status` - 服务器状态和文件信息
- `log` - 查看结构化日志，支持 `--lines` 和 `--json` 选项
- `run` - 执行脚本文件
- `run-project` - 执行项目目录

### 需求: CLI 全局标志
CLI SHALL 支持:
- `--port PORT` - 指定服务器端口 (默认: 7123)
- `--timeout SECONDS` - 执行超时时间
- `--verbose` - 显示完整错误堆栈

### 需求: 独立模块执行
CLI 模块 SHALL 可通过 `python -m idaipy.cli` 执行，用于开发环境无需安装。
