# IdaIpy Client Skill

LLM可直接调用的IdaIpy客户端封装，用于在IDA Pro中执行远程Python代码。

## 快速开始

```python
from idaipy import IdaIpyClient

with IdaIpyClient() as c:
    r = c.run_script("script.py")
    r.raise_if_error()
    print(r.stdout)
```

## 连接管理

### 建立连接

```python
from idaipy import IdaIpyClient

# 基本连接（使用默认127.0.0.1:7123）
client = IdaIpyClient()

# 自定义主机和端口
client = IdaIpyClient(host="192.168.1.100", port=8080)

# 带workspace
client = IdaIpyClient(workspace="/path/to/project")

# 使用环境变量
# IDAIPY_HOST=10.0.0.1 IDAIPY_PORT=9999 IDAIPY_TIMEOUT=300
```

### 检查连接状态

```python
client.connect()
if client.is_connected():
    print("已连接")

# 健康检查
info = client.ping()  # 返回 {"status": "ok", "pong": ...}
print(info)

# 服务状态
status = client.status()  # 返回 {"status": "running", ...}
```

### 关闭连接

```python
client.close()
# 或使用上下文管理器自动关闭
with IdaIpyClient() as c:
    # ...
# 自动关闭
```

## 执行脚本

### run_script - 执行本地Python文件

```python
# 执行单个脚本（默认main_read模式）
r = client.run_script("example/gather_info.py")
r.raise_if_error()  # 如果出错则抛出异常
print(r.stdout)       # 打印输出

# 使用main_write模式（可修改IDA数据库）
r = client.run_script("modify_ida.py", mode="main_write")

# 执行并解析JSON结果
data = client.run_script_json("query.py")  # 返回解析后的数据
```

### run_project - 执行项目目录

```python
# 执行整个项目（自动设置workspace）
r = client.run_project("my_analysis", entry="main.py")

# 使用push模式而非workspace
r = client.run_project("my_analysis", entry="main.py", use_workspace=False)
```

## 异步执行

### exec_async - 异步提交任务

```python
# 提交异步任务，返回task_id
task_id = client.exec_async("import time; time.sleep(10); print('done')")
print(f"任务ID: {task_id}")
```

### wait_task - 等待任务完成

```python
# 等待任务完成
result = client.wait_task(task_id, timeout=30)
print(result["state"])   # "done", "cancelled", 或 "error"
print(result["result"])  # Result字典

# 不带超时等待（一直等到完成）
result = client.wait_task(task_id)
```

### task_status - 查询任务状态

```python
status = client.task_status(task_id)
print(status["status"])  # "pending", "running", "done", "cancelled"
```

### cancel_task - 取消任务

```python
client.cancel_task(task_id)
```

### list_tasks - 列出所有任务

```python
tasks = client.list_tasks()
for t in tasks:
    print(f"{t['task_id']}: {t['status']}")
```

### exec_batch - 批量执行

```python
items = ["item1", "item2", "item3"]
task_id = client.exec_batch(items, chunk_size=10, yield_ms=100)
result = client.wait_task(task_id)
```

## Workspace管理

### set_workspace - 设置工作目录

```python
# 设置workspace（加入远程sys.path）
msg = client.set_workspace("/path/to/project")
print(msg)
```

### get_workspace - 获取当前workspace

```python
ws = client.get_workspace()
print(f"当前workspace: {ws}")
```

### clear_workspace - 清除workspace

```python
client.clear_workspace()
```

## Result对象

所有exec方法返回`Result`对象：

```python
r = client.run_script("script.py")

# 属性
r.ok              # True/False
r.status          # "ok" 或 "error"
r.stdout          # 标准输出
r.stderr          # 标准错误
r.error_type      # 错误类型（如"RuntimeError"）
r.error_message   # 错误消息
r.traceback       # 完整traceback

# 方法
r.raise_if_error()  # 如果是错误状态则抛出异常
r.get("field")      # 获取字段值（兼容dict访问）
```

## 错误处理

### 连接失败

```python
try:
    with IdaIpyClient() as c:
        r = c.run_script("script.py")
except ConnectionRefusedError:
    print("无法连接IDA，请确认：")
    print("1. IDA已启动")
    print("2. 已按Ctrl+Shift+R启动服务")
```

### 执行超时

```python
# 设置更长超时时间
client = IdaIpyClient(timeout=600)  # 10分钟

# 或使用异步执行
task_id = client.exec_async("long_running_task()")
# 不等待完成，稍后查询
```

### 脚本错误

```python
r = client.run_script("script.py")
if not r.ok:
    print(f"错误类型: {r.error_type}")
    print(f"错误消息: {r.error_message}")
    print(f"Traceback: {r.traceback}")
    r.raise_if_error()  # 抛出异常
```

## 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `IDAIPY_HOST` | 服务器主机 | 127.0.0.1 |
| `IDAIPY_PORT` | 服务器端口 | 7123 |
| `IDAIPY_TIMEOUT` | 超时时间（秒） | 600 |
| `IDAIPY_TOKEN` | 认证令牌 | （无） |

## 执行模式

| 模式 | 描述 | 何时使用 |
|------|------|----------|
| `main_read` | 主线程读锁（推荐） | 仅读取IDA信息 |
| `main_write` | 主线程写锁 | 修改IDA数据库 |

## 使用示例

### 示例1：获取文件信息

```python
from idaipy import IdaIpyClient

with IdaIpyClient() as c:
    r = c.run_script("""
import idaapi, idc, ida_ida
print(f"文件: {idc.get_input_file_path()}")
print(f"IDA版本: {idaapi.get_kernel_version()}")
print(f"处理器: {ida_ida.inf_get_procname()}")
""")
    r.raise_if_error()
    print(r.stdout)
```

### 示例2：枚举函数

```python
with IdaIpyClient() as c:
    r = c.run_script("""
import idautils, idc, json
funcs = []
for ea in idautils.Functions():
    funcs.append({
        "addr": hex(ea),
        "name": idc.get_func_name(ea)
    })
print(json.dumps(funcs[:10]))
""")
    print(r.stdout)
```

### 示例3：异步长时间任务

```python
with IdaIpyClient() as c:
    task_id = c.exec_async("""
import time
time.sleep(30)
print("完成")
""")
    print(f"任务ID: {task_id}")

    # 等待完成
    result = c.wait_task(task_id, timeout=60)
    print(result)
```

### 示例4：错误恢复

```python
with IdaIpyClient() as c:
    r = c.run_script("可能出错的脚本.py")
    try:
        r.raise_if_error()
    except RuntimeError as e:
        print(f"执行失败: {e}")
        # 根据错误类型进行恢复
        if "segment" in str(e).lower():
            print("可能是段相关错误")
```
