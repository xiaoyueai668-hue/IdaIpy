## 为什么需要这个变更

当前项目结构是自然演进的，职责分离不清晰。`scripts/` 目录混合了安装脚本、测试脚本和工具脚本。客户端的三种使用模式没有明确区分。服务端缺少规范的 workspace/cache 目录设计。这使得项目难以维护、使用和扩展。

## 变更内容

1. **Scripts 目录清理**: 只保留安装脚本
   - `scripts/install_plugin.py` — 唯一保留的脚本
   - 测试脚本移动到 `tests/` 目录
   - 工具脚本 (ida_samples.py, mrs_scan.py, search_ball_selectors.py) 移动到 `tools/`
   - `restart_ida.py` 移动到 `tools/` 或移除

2. **客户端打包结构重整**: 明确三种使用模式
   - **模式一 - 独立 CLI**: `python -m idaipy.cli` 或安装后的 `idaipy` 命令
   - **模式二 - Pip 包**: `pip install idaipy`，通过 `from idaipy import IdaIpyClient` 使用
   - **模式三 - 直接导入**: 开发模式下 `sys.path.insert(0, "/path/to/client/src")`

3. **服务端工作区设计**: 添加规范的目录结构
   - `~/.idaipy/cache/` — 执行缓存，临时文件
   - `~/.idaipy/workspaces/` — 用户工作区
   - `~/.idaipy/logs/` — 结构化日志
   - `~/.idaipy/config/` — 服务端配置

4. **文档重组**:
   - 客户端文档集中在 `client/docs/`
   - 服务端文档集中在 `server/docs/`
   - 顶层 `docs/` 作为索引和概述

5. **入口点整理**: 简化用户运行客户端的方式

## 能力

### 新增能力

- `client-cli`: IdaIpy 独立命令行接口
- `client-package`: idaipy-client Python 包分发结构
- `server-workspace`: 服务端工作区和缓存目录管理
- `project-structure`: 清晰的项目顶层组织结构

### 修改的能力

- 无 — 这是纯粹的结构重组

## 影响

- 目录结构变更: `scripts/` 只保留 `install_plugin.py`，新增 `tools/`、`tests/`
- 服务端目录: `~/.idaipy/` 获得规范的子目录
- 客户端安装: `pip install -e client/` 仍然有效，结构更清晰
- 文档: 移动到 `client/docs/` 和 `server/docs/`
