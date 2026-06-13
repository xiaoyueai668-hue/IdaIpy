## 1. 创建新目录结构

- [x] 1.1 创建 `tools/` 目录
- [x] 1.2 创建 `tests/` 目录
- [x] 1.3 创建 `client/src/` 目录结构
- [x] 1.4 创建 `client/docs/` 目录
- [x] 1.5 创建 `server/plugin/` 目录
- [x] 1.6 创建 `server/plugin/server/` 目录（服务端核心代码）
- [x] 1.7 创建 `server/docs/` 目录
- [x] 1.8 创建 `docs/design/` 目录
- [x] 1.9 创建 `docs/client/` 目录
- [x] 1.10 创建 `docs/server/` 目录

## 2. 移动客户端源码到 src 布局（包名 idaipy）

- [x] 2.1 创建 `client/src/idaipy/` 目录
- [x] 2.2 移动 `client/idaipy_client/*.py` 到 `client/src/idaipy/`
- [x] 2.3 更新 `client/src/idaipy/__init__.py` 导出 `IdaIpyClient`, `Result`
- [x] 2.4 更新 `client/pyproject.toml` 使用 `src/` 布局，包名改为 `idaipy`，入口点 `idaipy=idaipy.cli:main`
- [x] 2.5 更新源码中所有 `idaipy_client` 导入为 `idaipy`
- [x] 2.6 删除旧的 `client/idaipy_client/` 目录

## 3. 移动服务端插件到 server/plugin/server/

- [x] 3.1 移动 `server/idaipy_server/*.py` 到 `server/plugin/server/`
- [x] 3.2 移动 `server/idaipy_plugin.py` 到 `server/plugin/plugin.py`
- [x] 3.3 更新服务端源码中的相对导入
- [x] 3.4 删除旧的 `server/idaipy_server/` 和 `server/idaipy_plugin.py`

## 4. 移动工具脚本到 tools/（只移非 IDA 执行脚本）

- [x] 4.1 移动 `scripts/restart_ida.py` 到 `tools/`
- [x] 4.2 移动 `scripts/search_ball_selectors.py` 到 `tools/`
- [x] 4.3 不移动 `mrs_scan.py`（是示例脚本，将移到 example/）

## 5. 移动示例脚本

- [x] 5.1 移动 `scripts/mrs_scan.py` 到 `example/mrs_scan.py`
- [x] 5.2 移动 `scripts/ida_samples.py` 到 `example/ida_samples.py`

## 6. 移动测试脚本到 tests/

- [x] 6.1 移动 `scripts/test_plugin.py` 到 `tests/`
- [x] 6.2 移动 `scripts/test_module.py` 到 `tests/`
- [x] 6.3 移动 `scripts/test_modules/` 到 `tests/`
- [x] 6.4 移动 `example/test_basic.py` 到 `tests/`
- [x] 6.5 移动 `example/test_my_analysis.py` 到 `tests/`
- [x] 6.6 更新移动后测试文件中的文件引用

## 7. 整合文档

- [x] 7.1 移动 `docs/PROGRESS.md` 到 `docs/design/PROGRESS.md`
- [x] 7.2 移动 `docs/TROUBLESHOOTING-en.md` 到 `docs/server/TROUBLESHOOTING-en.md`
- [x] 7.3 移动 `docs/README-en.md` 到 `docs/server/README-en.md`
- [x] 7.4 从客户端 README 内容创建 `docs/client/README.md` 和 `docs/client/README-en.md`
- [x] 7.5 创建 `docs/server/README.md` 作为服务端概览
- [x] 7.6 更新 `docs/README.md` 作为导航索引
- [x] 7.7 删除冗余文档文件（如 `docs/README-en.md` 根目录残留）

## 8. 整理 scripts 目录

- [x] 8.1 scripts/ 只保留 `scripts/install_plugin.py`
- [x] 8.2 更新 `scripts/install_plugin.py` 引用新的服务端路径 `server/plugin/`
- [x] 8.3 删除空目录

## 9. 更新客户端文档

- [x] 9.1 更新 `client/README.md` 记录三种使用模式（`from idaipy import ...`）
- [x] 9.2 创建 `client/docs/README.md` (中文)
- [x] 9.3 创建 `client/docs/README-en.md` (英文)

## 10. 更新 CLAUDE.md

- [x] 10.1 更新 `idaipy/CLAUDE.md` 中的路径以反映新结构
- [x] 10.2 将服务端路径引用从 `server/idaipy_server/` 更新为 `server/plugin/`
- [x] 10.3 将包名从 `idaipy_client` 更新为 `idaipy`

## 11. 清理示例目录

- [x] 11.1 删除 `example/` 下已被移走的测试文件引用
- [x] 11.2 确认 `example/` 只保留真正的示例脚本

## 12. 验证和测试

- [x] 12.1 验证 `pip install -e client/` 仍然有效
- [x] 12.2 验证 `idaipy` CLI 命令正常工作
- [x] 12.3 验证 `python -m idaipy.cli` 开发模式正常工作
- [x] 12.4 验证 `from idaipy import IdaIpyClient` 正常工作
- [x] 12.5 验证测试脚本从 `tests/` 目录运行正常
- [x] 12.6 验证 `scripts/install_plugin.py` 在新服务端路径下正常工作
