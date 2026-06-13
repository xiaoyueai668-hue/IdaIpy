# IdaIpy

基于 **RPyC** 的 IDA Pro 远程执行插件（macOS / Linux / Windows，IDA 9.0/9.1/9.2）。
在外部 Python 脚本中直接调用 IDA API，无需在 IDA 控制台手动操作。

---

## 项目结构

```text
idaipy/
├── client/              # Python 客户端包
│   ├── src/idaipy/    # 源码 (pip install -e .)
│   ├── docs/           # 客户端文档
│   └── pyproject.toml
├── server/             # IDA 服务端插件
│   ├── plugin/         # 插件目录
│   └── docs/           # 服务端文档
├── scripts/            # 安装脚本
│   └── install_plugin.py
├── tools/              # 工具脚本
├── tests/              # 测试脚本
├── docs/               # 文档
│   ├── client/         # 客户端文档
│   ├── server/         # 服务端文档
│   └── design/         # 设计文档
└── example/            # 示例脚本
```

---

## 快速开始

### 1. 安装服务端插件

```bash
# 安装 rpyc（如果尚未安装）
pip3 install rpyc

# 安装插件到 IDA
python3 scripts/install_plugin.py
```

### 2. 启动服务

1. 在 IDA 中打开一个文件
2. 按下 **Ctrl+Shift+R** 启动服务
3. IDA Output 窗口显示 `[IdaIpy] RPyC server listening on 127.0.0.1:7123`

### 3. 使用客户端

```bash
# 安装客户端
pip install idaipy

# 或者开发模式
pip install -e client/

# 执行脚本
idaipy ping
idaipy run script.py
```

---

## 文档

| 组件 | 文档 |
|------|------|
| 客户端 | [client/README.md](./client/) |
| 服务端 | [server/README.md](./server/) |
| 设计 | [design/DESIGN.md](./design/) |
| 故障排查 | [server/TROUBLESHOOTING.md](./server/) |
| CLAUDE.md | [CLAUDE.md](../CLAUDE.md) |
