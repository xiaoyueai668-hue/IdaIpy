## ADDED Requirements

### Requirement: 文档统一到 docs/ 目录

所有项目 Markdown 文档 SHALL 移动到 `docs/` 子目录，形成统一的文档入口。

#### Scenario: 文档目录结构正确
- **WHEN** 用户查看项目目录结构
- **THEN** `docs/` 目录包含：`README.md`、`README-en.md`、`PROGRESS.md`、`TROUBLESHOOTING.md` 和 `design/` 子目录

#### Scenario: 根目录无散落文档
- **WHEN** 用户查看项目根目录
- **THEN** 根目录不包含任何 `.md` 文件（除 `CLAUDE.md` 外）

### Requirement: 清理过时构建产物

过时构建产物目录 SHALL 从版本控制中移除。

#### Scenario: 构建产物已删除
- **WHEN** 用户检查源代码目录
- **THEN** `client/build/` 目录不存在
- **AND** `client/idaipy_client.egg-info/` 目录不存在

### Requirement: 服务端和客户端源码结构保持不变

服务端和客户端代码的内部目录结构 SHALL 保持不变。

#### Scenario: 服务端结构未变
- **WHEN** 用户检查 `server/` 目录
- **THEN** `server/` 包含 `idaipy_server/` 和 `idaipy_plugin.py`

#### Scenario: 客户端结构未变
- **WHEN** 用户检查 `client/idaipy_client/` 目录
- **THEN** 包含 `client.py`、`cli.py`、`result.py`、`__init__.py`

### Requirement: CLAUDE.md 路径引用更新

`CLAUDE.md` SHALL 更新其内部对文档路径的引用。

#### Scenario: CLAUDE.md 引用正确
- **WHEN** 其他工具读取 `CLAUDE.md`
- **THEN** 所有文档路径引用指向新的 `docs/` 位置
