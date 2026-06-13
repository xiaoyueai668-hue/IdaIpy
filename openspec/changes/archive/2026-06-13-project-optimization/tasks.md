## 1. 版本号统一

- [x] 1.1 更新 `client/pyproject.toml` 版本为 0.2.0
- [x] 1.2 修改 `client/src/idaipy/__init__.py` 从 pyproject.toml 读取版本

## 2. 修复示例代码导入

- [x] 2.1 检查 `example/basic_info.py` 并修复导入
- [x] 2.2 检查 `example/my_analysis/main.py` 并修复导入
- [x] 2.3 检查 `example/my_analysis/helpers.py` 并修复导入 (无 idaipy_client 导入)
- [x] 2.4 检查 `example/mrs_scan.py` 并修复导入 (无 idaipy_client 导入)
- [x] 2.5 检查 `example/ida_samples.py` 并修复导入 (无 idaipy_client 导入)

## 3. 添加类型注解

- [x] 3.1 为 `client/src/idaipy/client.py` 添加返回类型注解
- [x] 3.2 为 `server/plugin/service.py` 添加返回类型注解

## 4. 添加 CI 配置

- [x] 4.1 创建 `.github/workflows/test.yml`
- [x] 4.2 配置 pytest 运行单元测试

## 5. 添加单元测试

- [x] 5.1 创建 `tests/unit/__init__.py`
- [x] 5.2 创建 `tests/unit/test_result.py` 测试 Result 类
- [x] 5.3 创建 `tests/unit/test_client.py` 测试客户端连接
- [x] 5.4 创建 `tests/unit/test_service.py` 测试任务管理

## 6. CLI 添加 --version

- [x] 6.1 修改 `client/src/idaipy/cli.py` 添加 --version 参数

## 7. 优化任务清理

- [x] 7.1 修改 `server/plugin/service.py` 添加后台清理线程

## 8. 客户端支持环境变量

- [x] 8.1 修改 `client/src/idaipy/client.py` 支持 IDAIPY_HOST
- [x] 8.2 修改 `client/src/idaipy/client.py` 支持 IDAIPY_PORT
- [x] 8.3 修改 `client/src/idaipy/client.py` 支持 IDAIPY_TIMEOUT
