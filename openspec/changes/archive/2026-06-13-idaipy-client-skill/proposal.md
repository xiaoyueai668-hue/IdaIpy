## 为什么需要这个变更

Claude Code 需要一个结构化的技能来调用 IdaIpy 客户端执行 IDA 远程操作。当前没有专门为 Claude Code 设计的技能文件来指导 LLM 如何正确使用 IdaIpy 客户端 API、执行脚本、处理结果和错误。

## 变更内容

- 创建 `.claude/skills/idaipy/` 目录作为 Claude Code 技能
- 实现技能主文件，包含 IdaIpy 客户端的完整调用接口
- 提供常见 IDA 操作的封装方法供 LLM 直接调用
- 添加错误处理和连接管理的最佳实践
- 包含使用示例和命令模板

## 能力

### 新增能力

- `idaipy-client-skill`: Claude Code 技能，将 IdaIpy 客户端封装为 LLM 可直接调用的接口

## 影响范围

- 新文件: `.claude/skills/idaipy/skill.md` - Claude Code IdaIpy 技能
- 新文件: `.claude/skills/idaipy/commands.py` - 命令封装模块
- 修改: `.claude/skills/` 配置
