## 为什么需要这个变更

当前项目文档中使用 ASCII 艺术图表来展示架构和目录结构，这些图表难以维护、阅读体验差，且无法在 GitHub/GitLab 等平台上直接渲染。使用 Mermaid 格式可以提供更好的可维护性和跨平台兼容性。

## 变更内容

1. **将所有 ASCII 架构图转换为 Mermaid flowchart**
   - `idaipy/CLAUDE.md` 中的客户端-服务端架构图
   - `idaipy/docs/README.md` 中的项目架构图

2. **将所有 ASCII 目录树转换为 Mermaid directory 格式或使用代码块展示**
   - `idaipy/CLAUDE.md` 中的项目结构图
   - `idaipy/docs/README.md` 中的目录结构
   - `idaipy/docs/design/DESIGN.md` 和 `DESIGN-en.md` 中的架构图

3. **确保 Mermaid 图表在 GitHub/GitLab/VSCode 中正常渲染**

## 能力

### 新增能力

- `diagram-migration`: 将项目文档中的 ASCII 图表迁移到 Mermaid 格式

### 修改的能力

- 无 — 仅是文档格式变更，不影响功能

## 影响

- 更新的文件:
  - `idaipy/CLAUDE.md`
  - `idaipy/docs/README.md`
  - `idaipy/docs/design/DESIGN.md`
  - `idaipy/docs/design/DESIGN-en.md`
- 无功能变更，仅文档格式调整
