## Context

当前 IdaIpy 项目结构存在以下问题：

**问题 1：文档分散**
- `README.md` 在根目录
- `client/README.md` 在子目录
- `doc/DESIGN.md` 在子目录
- `CLAUDE.md` 在根目录
- `PROGRESS.md`、`TROUBLESHOOTING.md` 在根目录

没有统一的文档入口，用户难以找到所需内容。

**问题 2：过时构建产物**
- `client/build/` — 过时的 bdist.macosx 产物
- `client/idaipy_client.egg-info/` — 过时的 pip egg-info
- `__pycache__` 散落在各处

**问题 3：无英文文档**
- 所有文档仅有中文版本
- 国际用户难以使用

## Goals / Non-Goals

**Goals:**
- 将所有 Markdown 文档统一到 `docs/` 目录
- 实现文档中英文双语支持
- 清理过时构建产物
- 保持项目根目录整洁

**Non-Goals:**
- 不改变任何代码逻辑
- 不改变 `server/`、`client/idaipy_client/`、`scripts/` 的内部结构
- 不重写任何文档内容（仅整理格式和创建翻译）
- 不修改包管理配置（`pyproject.toml` 无需改动）

## Decisions

### Decision 1: 文档统一到 `docs/` 目录

**选择**：将所有 Markdown 文档移动到 `docs/` 子目录。

**理由**：
- 清晰的文档边界
- 与 `server/`、`client/`、`scripts/` 并列
- 用户只需进入 `docs/` 即可找到所有文档

**替代方案**：
- 保留在根目录（混乱，无统一入口）
- 移动到 `doc/`（已存在但只含 DESIGN.md，不够全面）

### Decision 2: `-en.md` 后缀命名英文版本

**选择**：英文版文档使用 `<name>-en.md` 后缀。

**理由**：
- 文件名即表示语言，清晰直观
- 便于程序处理（如 glob `*.md` 获取所有文档）
- 与中文版并列，便于对比

**替代方案**：
- `en/<name>.md`（增加嵌套层级）
- `README_EN.md`（大小写混用不够整洁）

### Decision 3: README 入口默认中文

**选择**：`docs/README.md` 为中文，`docs/README-en.md` 为英文。

**理由**：
- 项目原始语言为中文，中文版作为主入口合理
- 英文用户明确知道选择 `-en` 版本

### Decision 4: 清理过时构建产物

**选择**：删除 `client/build/`、`client/idaipy_client.egg-info/`。

**理由**：
- 这些是过时产物，现代 pip 安装不依赖它们
- `pyproject.toml` 已经是正确的包配置
- 删除后 `pip install -e client` 仍正常工作

## Risks / Trade-offs

**[Risk] Git 历史追踪中断** → 文件移动后 git 可能将移动识别为删除+新建。**缓解**：使用 `git mv` 而非直接移动，或在 commit message 注明 `git mv`。

**[Risk] 文档链接失效** → 移动文档后其他文件的相对/绝对链接可能失效。**缓解**：检查并更新所有内部文档链接。

**[Risk] 英文翻译质量** → 机器翻译或人工翻译可能不准确。**缓解**：翻译版作为参考，中文版为权威版本。

## Migration Plan

1. **准备阶段**：创建 `docs/` 目录结构
2. **移动阶段**：将文档移动到 `docs/`，创建英文翻译
3. **清理阶段**：删除过时构建产物
4. **更新阶段**：更新 CLAUDE.md 中的路径引用
5. **验证阶段**：确认所有文档可正常访问

## Open Questions

1. 是否需要为英文文档单独维护？还是仅作为参考？
2. `doc/DESIGN.md` 是否需要英文版？
