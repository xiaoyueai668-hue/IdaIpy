# diagram-migration

## 新增需求

### 需求: Mermaid 架构图
CLAUDE.md 中的客户端-服务端架构图 SHALL 使用 Mermaid flowchart 格式。

#### 场景: GitHub 渲染
- **WHEN** 在 GitHub 上查看 CLAUDE.md
- **THEN** 架构图正确渲染为 Mermaid flowchart

### 需求: Mermaid 项目结构图
docs/README.md 中的项目结构概览图 SHALL 使用 Mermaid flowchart 格式。

### 需求: 目录结构代码块
所有目录结构 SHALL 使用带语法高亮的代码块展示，而非 ASCII 树形图。

### 需求: 设计文档架构图
docs/design/DESIGN.md 和 DESIGN-en.md 中的架构图 SHALL 使用 Mermaid flowchart 格式。
