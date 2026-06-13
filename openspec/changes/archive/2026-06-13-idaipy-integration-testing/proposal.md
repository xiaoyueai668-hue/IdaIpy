## 为什么需要这个变更

通过实际使用 idaipy 包的方式进行集成测试，确保客户端功能完整可用。当前测试需要 IDA 运行且服务启动，缺少直接在 Python 环境中使用 idaipy 包进行功能验证的集成测试脚本。

## 变更内容

- 创建集成测试脚本，使用 idaipy 包连接 IDA 服务并执行测试
- 测试客户端各项功能：连接、执行脚本、异步任务、workspace 等
- 验证错误处理和边界情况
- 提供测试报告输出

## 能力

### 新增能力

- `idaipy-integration-testing`: 集成测试脚本，通过实际使用 idaipy 包测试所有功能

## 影响范围

- 新文件: `tests/integration/test_client_integration.py` - 集成测试脚本
- 新文件: `tests/integration/__init__.py` - 测试包初始化
