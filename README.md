# IdaIpy

RPyC-based IDA Pro remote execution plugin for macOS/Linux/Windows (IDA 9.0/9.1/9.2).

允许从外部脚本在 IDA 中远程执行 Python 代码，无需直接使用 IDA 控制台。

## 架构

```
Client[Client] --> RPyC --> Server[IDA Pro]
Server --> Result --> Client
```

**服务端 (IDA 插件)**: `server/plugin/`
- `plugin.py` — IDA 插件，Ctrl+Shift+R 切换服务
- `service.py` — RPyC 服务，暴露远程方法
- `executor.py` — 线程安全执行引擎

**客户端**: `client/src/idaipy/`
- `client.py` — RPyC 客户端封装
- `result.py` — Result 数据类
- `cli.py` — 命令行工具 `idaipy`

## 安装

### IDA 插件

```bash
python3 scripts/install_plugin.py
```

安装后在 IDA 中按 **Ctrl+Shift+R** 启动/停止服务。

### Python 客户端

```bash
pip install -e client/
```

或开发模式：
```bash
pip install -e client/
```

## 使用

### 命令行

```bash
idaipy ping                        # 健康检查
idaipy status                      # 服务状态
idaipy run script.py               # 执行脚本
idaipy run script.py --mode main_write  # 写模式
idaipy run-project my_project      # 执行项目
```

### Python API

```python
from idaipy import IdaIpyClient

with IdaIpyClient() as c:
    r = c.run_script("script.py")
    r.raise_if_error()
    print(r.stdout)
```

## 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `IDAIPY_HOST` | 服务器主机 | 127.0.0.1 |
| `IDAIPY_PORT` | 服务器端口 | 7123 |
| `IDAIPY_TIMEOUT` | 超时时间（秒） | 600 |
| `IDAIPY_TOKEN` | 认证令牌 | （无） |

## 测试

```bash
# 需要 IDA 运行且服务启动
python3 -m pytest tests/test_plugin.py -v   # 集成测试
python3 -m pytest tests/test_module.py -v    # 模块测试
python3 -m pytest tests/unit/ -v             # 单元测试
```

## 项目结构

```
idaipy/
├── client/              # Python 客户端包
├── server/              # IDA 插件
├── scripts/             # 安装脚本
├── tests/               # 测试脚本
├── example/             # 示例脚本
└── docs/                # 文档
```
