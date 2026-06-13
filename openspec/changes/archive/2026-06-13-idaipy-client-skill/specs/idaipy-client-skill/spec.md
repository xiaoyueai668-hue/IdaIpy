## ADDED Requirements

### Requirement: Claude Code IdaIpy 技能接口
系统应提供 `.claude/skills/idaipy/skill.md` 技能文件，包含完整的 IdaIpy 客户端使用指南。

#### Scenario: LLM 加载技能
- **WHEN** Claude Code 在 idaipy 项目中工作
- **THEN** 它应检测到技能并使用其指导进行 IDA 远程操作

#### Scenario: LLM 需要执行脚本
- **WHEN** LLM 需要在 IDA 中执行 Python 脚本
- **THEN** 它应使用 `run_script(script_path)` 方法

#### Scenario: LLM 需要检查连接状态
- **WHEN** LLM 需要验证 IDA 连接
- **THEN** 它应使用 `ping()` 或 `status()` 方法

### Requirement: 命令封装模块
系统应提供 `commands.py` 模块，封装常用操作为可直接调用的函数。

#### Scenario: 执行单个脚本
- **WHEN** LLM 需要执行本地脚本到 IDA
- **THEN** 它应调用 `execute_script(script_path, mode="main_read")`

#### Scenario: 执行项目
- **WHEN** LLM 需要执行整个项目目录
- **THEN** 它应调用 `execute_project(project_dir, entry="main.py")`

#### Scenario: 异步执行
- **WHEN** LLM 需要执行长时间任务
- **THEN** 它应使用 `execute_async(code)` 和 `wait_for_task(task_id)`

### Requirement: 错误处理指南
系统应记录常见错误和恢复方法。

#### Scenario: 连接失败
- **WHEN** 无法连接到 IDA
- **THEN** LLM 应提示用户检查 IDA 是否运行，服务是否启动（Ctrl+Shift+R）

#### Scenario: 执行超时
- **WHEN** 脚本执行超时
- **THEN** LLM 应增加 timeout 参数或使用异步执行
