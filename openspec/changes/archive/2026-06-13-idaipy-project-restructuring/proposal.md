## Why

当前 IdaIpy 项目结构混乱：文档散落在根目录和子目录中（`README.md`、`client/README.md`、`doc/DESIGN.md`、`CLAUDE.md`、`PROGRESS.md`、`TROUBLESHOOTING.md`），且仅有中文版本。项目结构也不够清晰，build/、__pycache__/ 等干扰目录影响可读性。需要重新设计项目结构和文档组织，并实现中英文双语支持。

## What Changes

### 项目结构重组
- 将散落的文档统一到 `docs/` 目录下
- 移除 `client/build/` 等构建产物目录（已过时，由 pyproject.toml 管理）
- 清理 `__pycache__` 和 `.egg-info` 目录
- 统一文档格式和命名规范

### 文档目录结构（重组后）
```
idaipy/
├── docs/
│   ├── README.md          # 项目总览（中文）
│   ├── README-en.md       # 项目总览（英文）
│   ├── PROGRESS.md        # 开发进度（中文）
│   ├── TROUBLESHOOTING.md # 故障排查（中文）
│   └── design/
│       ├── DESIGN.md      # 架构设计（中文）
│       └── DESIGN-en.md   # 架构设计（英文）
├── client/
│   ├── README.md          # 客户端文档（中文）
│   └── README-en.md       # 客户端文档（英文）
├── server/                 # 服务端源码（无变化）
├── scripts/                # 脚本（无变化）
├── example/                # 示例（无变化）
└── CLAUDE.md              # Claude Code 上下文（根目录）
```

### 文档双语化
- 所有文档均提供中文原版和英文翻译版
- 英文版以 `-en.md` 后缀命名（如 `README-en.md`）
- README 入口文件默认中文，英文版为 `README-en.md`

### 其他清理
- 移除 `client/build/` 目录（过时构建产物）
- 移除 `client/idaipy_client.egg-info/` 目录（过时包信息）
- 更新 `.gitignore` 忽略规则

## Capabilities

### New Capabilities

- `project-restructuring`: 项目目录结构重组、文档统一整理
- `i18n-docs`: 文档中英文双语支持

## Impact

- 文件系统重组（文件移动）
- `.gitignore` 更新
- CLAUDE.md 可能需要更新路径引用
