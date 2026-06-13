## 背景

当前项目文档使用 ASCII 艺术图表，存在于以下文件：
- `CLAUDE.md` - 客户端-服务端架构图、项目目录结构图
- `docs/README.md` - 项目结构概览图
- `docs/design/DESIGN.md` 和 `DESIGN-en.md` - 架构设计图

## 目标 / 非目标

**目标:**
- 将所有 ASCII 架构图转换为 Mermaid flowchart
- 将所有 ASCII 树形目录结构转换为 Mermaid 目录格式或代码块展示
- 确保图表在 GitHub/GitLab/VSCode 中正常渲染

**非目标:**
- 不修改文档的文本内容
- 不添加新图表，仅转换现有图表
- 不改变文档结构

## 决策

### 1. 架构图转换为 Mermaid flowchart

**决策:** 使用 Mermaid flowchart 替换 ASCII 架构图

```mermaid
flowchart LR
    Client[Client<br/>Python] -->|RPyC| Server[IDA Pro<br/>Server]
    Server -->|Result| Client
```

**理由:** Mermaid flowchart 在 GitHub/GitLab/VSCode 中原生支持，渲染效果优于 ASCII。

### 2. 目录结构使用代码块展示

**决策:** 目录结构使用带语法高亮的代码块替代 ASCII 树

```text
idaipy/
├── client/
│   └── src/idaipy/
└── server/
    └── plugin/
```

**理由:** Mermaid 不支持目录树，而带语法高亮的代码块在所有平台上都能正确显示。

### 3. 使用 `flowchart LR` 而非 `flowchart TB`

**决策:** 架构图使用 LR (Left-Right) 布局

**理由:** 客户端-服务端架构天然适合水平布局，LR 布局更符合阅读习惯。

## 风险 / 权衡

- [风险] 部分 Markdown 查看器不支持 Mermaid
  → **缓解:** 选择主流平台（GitHub/GitLab/VSCode）广泛支持的格式

- [风险] ASCII 图转换为 Mermaid 可能略有差异
  → **缓解:** 保持图表语义一致，仅格式转换

## 待解决问题

无
