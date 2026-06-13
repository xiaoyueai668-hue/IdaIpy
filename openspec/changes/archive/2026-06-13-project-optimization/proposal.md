## 为什么需要这个变更

项目存在多个优化问题影响可用性、稳定性和可维护性：

1. **版本号不一致** — `__init__.py` 声明 0.2.0，`pyproject.toml` 是 0.1.0
2. **示例代码导入错误** — `example/` 中仍用 `idaipy_client` 而非 `idaipy`
3. **缺少类型注解** — 关键方法缺少返回类型
4. **无 CI 配置** — 没有 GitHub Actions 自动化测试
5. **无单元测试** — 只有集成测试
6. **CLI 缺少 `--version`** — 无法查看版本号
7. **服务端任务清理不彻底** — 只在创建新任务时清理
8. **客户端不支持环境变量配置** — `HOST`、`PORT` 等只能代码配置

## 变更内容

### 高优先级

- [ ] **1. 统一版本号** — 同步 `pyproject.toml` 和 `__init__.py` 版本
- [ ] **2. 修复示例导入** — 将 `example/` 中 `idaipy_client` 改为 `idaipy`

### 中优先级

- [ ] **3. 添加类型注解** — 为 `client.py`、`service.py` 关键方法添加返回类型
- [ ] **4. 添加 CI 配置** — 创建 GitHub Actions workflow
- [ ] **5. 添加单元测试** — 为 Result、连接重试等添加单元测试

### 低优先级

- [ ] **6. CLI 添加 `--version`** — 添加 `-V/--version` 标志
- [ ] **7. 优化任务清理** — 添加后台定时清理机制
- [ ] **8. 客户端支持环境变量** — 支持 `IDAIPY_HOST`、`IDAIPY_PORT`、`IDAIPY_TIMEOUT`

## 能力

### 新增能力

- `ci-workflow`: GitHub Actions CI 配置
- `unit-tests`: 单元测试框架和测试用例

### 修改的能力

- `client-package`: 添加环境变量支持
- `client-cli`: 添加 `--version` 标志
- `version-sync`: 统一版本号

## 影响

- 更新的文件:
  - `client/pyproject.toml` — 版本号统一
  - `client/src/idaipy/__init__.py` — 版本号统一
  - `example/*.py` — 修复导入路径
  - `client/src/idaipy/client.py` — 添加类型注解、环境变量支持
  - `client/src/idaipy/cli.py` — 添加 `--version`
  - `server/plugin/service.py` — 添加类型注解、优化任务清理
  - `.github/workflows/` — 新增 CI 配置
- 新增文件:
  - `tests/unit/` — 单元测试目录
