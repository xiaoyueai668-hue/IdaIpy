# ci-workflow

## 新增需求

### 需求: GitHub Actions CI 配置
项目 SHALL 包含 `.github/workflows/test.yml` 用于自动化测试。

#### 场景: Push 时触发 CI
- **WHEN** 开发者 push 代码到 main 或创建 PR
- **THEN** CI 自动运行单元测试

### 需求: 单元测试通过
CI SHALL 确保所有单元测试通过后才能合并。

#### 场景: 测试失败阻止合并
- **WHEN** 单元测试失败
- **THEN** CI 显示失败状态，阻止合并
