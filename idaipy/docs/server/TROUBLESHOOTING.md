# IdaIpy 故障排查

> 最后更新：2026-06-13

## 目录

1. [连接问题](#1-连接问题)
2. [执行问题](#2-执行问题)
3. [安装问题](#3-安装问题)
4. [安全问题](#4-安全问题)
5. [日志问题](#5-日志问题)

---

## 1. 连接问题

### Q: `ConnectionRefusedError: [Errno 61] Connection refused`

**原因**: IDA 服务未启动或端口被占用。

**排查步骤**:
1. 确认 IDA 中按下了 **Ctrl+Shift+R** 启动服务
2. 检查 IDA Output 窗口是否显示 `[IdaIpy] RPyC server listening on 127.0.0.1:7123`
3. 确认端口未被其他程序占用：
   ```bash
   lsof -i :7123  # macOS/Linux
   netstat -ano | findstr :7123  # Windows
   ```

**解决方案**:
- 重启 IDA 并确保先打开一个文件，再按 Ctrl+Shift+R
- 使用 `--port` 指定其他端口：`idaipy run script.py --port 7124`

---

### Q: 连接成功但调用超时 `TimeoutError`

**原因**: 代码执行时间超过默认超时（600s）。

**解决方案**:
- 使用 `--timeout` 参数增加超时：`idaipy run script.py --timeout 1200`
- 客户端创建时指定：`IdaIpyClient(timeout=1200)`
- 使用异步执行避免长时间阻塞：
  ```python
  tid = ida.exec_async("import time; time.sleep(300)")
  result = ida.wait_task(tid, timeout=600)
  ```

---

### Q: 断开连接后自动重连失败

**原因**: IDA 服务不可用或网络问题。

**排查步骤**:
1. 确认 IDA 仍在运行且服务已启动
2. 测试手动连接：`idaipy ping`

**解决方案**:
- 重启 IDA 服务（Ctrl+Shift+R 停止，再 Ctrl+Shift+R 启动）
- 检查是否有防火墙阻止本地连接

---

## 2. 执行问题

### Q: `RuntimeError: Function can be called from the main thread only`

**原因**: IDA 9.x API 必须在主线程执行。

**解决方案**:
- 使用 `mode="main_read"`（推荐，读取操作）
- 使用 `mode="main_write"`（写入操作，需要写锁）
- 不使用任何 mode（默认 background，但无法调用 IDA API）

```python
# ✅ 正确
r = ida.run_script("script.py", mode="main_read")

# ❌ 错误（会报 main thread only）
r = ida.run_script("script.py")  # 默认 background 模式
```

---

### Q: `Result.error: PermissionError: Invalid or missing token`

**原因**: 服务端设置了 `IDAIPY_TOKEN` 环境变量，但客户端未传递 token。

**解决方案**:
- 如果不需要 Token 认证：移除服务端的 `IDAIPY_TOKEN` 环境变量
- 如果需要 Token 认证：客户端需要支持 token 参数（当前 CLI 暂不支持 token 传递，请升级客户端）

---

### Q: 异步任务 `wait_task` 超时

**原因**: 任务执行时间超过指定的 timeout。

**解决方案**:
```python
# 增加超时时间
result = ida.wait_task(task_id, timeout=3600)  # 1小时

# 不设置超时（无限等待）
result = ida.wait_task(task_id, timeout=None)

# 检查任务状态
status = ida.task_status(task_id)
print(status)
```

---

### Q: `ModuleNotFoundError` 在远程脚本中

**原因**: 服务端找不到你 import 的模块。

**解决方案**:
1. 使用 **Workspace 模式**（推荐）：
   ```python
   with IdaIpyClient(workspace="/path/to/your/project") as ida:
       r = ida.run_script("script.py")  # script.py 中可以 import 你项目的模块
   ```
2. 使用 **Push 模式**：
   ```python
   r = ida.run_project("path/to/project", entry="main.py", use_workspace=False)
   ```
3. 使用 **add_path** 手动添加路径：
   ```python
   ida.add_path("/path/to/modules")
   ```

---

## 3. 安装问题

### Q: `RuntimeError: IDA Pro not found`

**原因**: 安装脚本无法自动检测 IDA 安装路径。

**解决方案**:
1. 使用 `--ida-path` 手动指定：
   ```bash
   # macOS
   python3 install_plugin.py --ida-path "/Applications/IDA Pro 9.2.app"

   # Linux
   python3 install_plugin.py --ida-path ~/idapro-9.2/idalinux64/plugins

   # Windows
   python3 install_plugin.py --ida-path "C:\Program Files\IDA Pro 9.2\plugins"
   ```

2. 手动安装：
   ```bash
   # macOS
   IDA_PLUGINS="/Applications/MDA.app/Contents/MacOS/plugins"
   cp server/idaipy_plugin.py "$IDA_PLUGINS/"
   cp -r server/idaipy_server "$IDA_PLUGINS/"
   ```

---

### Q: `NameError: name 'IdaIpyPlugin' is not defined`

**原因**: Python 模块缓存（`__pycache__`）未清理。

**解决方案**:
```bash
# 清理 IDA plugins 目录的缓存
rm -rf ~/idaipy_*/plugins/idaipy_server/__pycache__
# 或
find ~/idaipy_*/plugins -name "__pycache__" -exec rm -rf {} +
```

---

### Q: `ModuleNotFoundError: No module named 'rpyc'`

**原因**: IDA 使用的 Python 环境没有安装 rpyc。

**解决方案**:
```bash
# macOS（IDA 自带 Python）
/Applications/MDA.app/Contents/MacOS/python3 -m pip install rpyc

# Linux
~/idapro-9.2/idalinux64/python3 -m pip install rpyc

# 或系统 Python（如果 IDA 使用系统 Python）
pip3 install rpyc
```

---

## 4. 安全问题

### Q: `idaipy: WARNING: IDAIPY_ALLOW_PICKLE=1 is set`

**原因**: 检测到环境变量 `IDAIPY_ALLOW_PICKLE=1`，pickle 反序列化已启用。

**风险**: `allow_pickle=True` 允许反序列化任意 pickled 对象，存在 RCE（远程代码执行）风险。

**解决方案**:
- 如果不需要：移除环境变量 `IDAIPY_ALLOW_PICKLE`
- 如果确实需要pickle序列化：确保只有可信客户端能连接（网络隔离）

---

### Q: Token 认证失败

**原因**: 客户端与服务端的 Token 不匹配。

**解决方案**:
1. 确认服务端设置了 `IDAIPY_TOKEN`：`echo $IDAIPY_TOKEN`
2. 确认客户端连接时传递了正确的 token
3. 如果不需要 Token 认证：关闭服务端的 `IDAIPY_TOKEN` 环境变量

---

## 5. 日志问题

### Q: 日志文件不存在 `~/.idaipy/idaipy.log`

**原因**: 日志目录未创建或无写入权限。

**解决方案**:
1. 手动创建目录：
   ```bash
   mkdir -p ~/.idaipy
   chmod 755 ~/.idaipy
   ```
2. 使用 `IDAIPY_LOG_DIR` 指定其他位置：
   ```bash
   IDAIPY_LOG_DIR=/tmp/idaipy_logs python3 install_plugin.py
   ```

---

### Q: 如何查看 JSON 格式的日志？

**解决方案**:
```bash
idaipy log --lines 100 --json
```

或直接查看文件：
```bash
cat ~/.idaipy/idaipy.log | jq
```

---

### Q: 日志文件无限增长

**原因**: 目前日志文件不自动轮转。

**临时解决方案**:
```bash
# 手动轮转
mv ~/.idaipy/idaipy.log ~/.idaipy/idaipy.log.old
# 然后重启 IDA 服务（Ctrl+Shift+R）

# 或使用 logrotate（macOS/Linux）
# 创建 /etc/logrotate.d/idaipy：
# ~/.idaipy/idaipy.log {
#     rotate 5
#     size 10M
#     compress
# }
```

---

## 获取帮助

1. 查看完整日志：`idaipy log --lines 200 --json`
2. 启用客户端 debug 模式：`idaipy --debug run script.py`
3. 服务端 debug：在 IDA 中修改 `server/idaipy_server/config.py` 设置 `DEBUG = True`，重启服务
4. 查看 IDA Output 窗口的服务端日志输出
