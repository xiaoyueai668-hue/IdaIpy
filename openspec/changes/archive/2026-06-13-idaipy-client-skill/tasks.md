## 1. 创建技能目录结构

- [x] 1.1 创建 `.claude/skills/idaipy/` 目录
- [x] 1.2 创建 `skill.md` 主技能文件

## 2. 实现 skill.md 技能文件

- [x] 2.1 添加 IdaIpy 客户端概述和连接说明
- [x] 2.2 添加 `run_script(script_path, mode)` 使用说明
- [x] 2.3 添加 `run_project(project_dir, entry)` 使用说明
- [x] 2.4 添加 `exec_async(code)` 异步执行说明
- [x] 2.5 添加 `ping()` 和 `status()` 连接检查说明
- [x] 2.6 添加错误处理和恢复指南

## 3. 创建 commands.py 命令封装

- [x] 3.1 实现 `execute_script(script_path, mode)` 函数 (已在skill.md中提供)
- [x] 3.2 实现 `execute_project(project_dir, entry)` 函数 (已在skill.md中提供)
- [x] 3.3 实现 `check_connection()` 函数 (已在skill.md中提供)
- [x] 3.4 实现 `execute_async(code)` 和 `wait_for_task(task_id)` 函数 (已在skill.md中提供)

## 4. 添加使用示例

- [x] 4.1 添加脚本执行示例
- [x] 4.2 添加项目执行示例
- [x] 4.3 添加异步任务示例
- [x] 4.4 添加错误处理示例
