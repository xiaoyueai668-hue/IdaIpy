## 背景

IdaIpy 项目当前 `scripts/` 目录混合了安装脚本、测试脚本和工具脚本。客户端没有清晰区分三种使用模式（独立 CLI、pip 包、程序化导入）。服务端缺少规范的 workspace/cache 目录结构。

**当前结构:**
```
idaipy/
├── scripts/         # 混合: 安装 + 测试 + 工具
├── client/          # 包 + CLI 混合
├── server/          # 插件 + 服务端代码混合
├── docs/            # 双语文档
└── example/         # 示例脚本
```

## 目标 / 非目标

**目标:**
- 清晰分离: `scripts/` 只包含 `install_plugin.py`
- 客户端使用模式清晰可查
- 服务端 workspace/cache 目录设计 (位于 `~/.idaipy/`)
- 优雅、可维护的项目结构
- 包名简洁：`idaipy` 而非 `idaipy_client`

**非目标:**
- 不修改实际代码功能 (Result 类型、异步任务等保持不变)
- 不破坏 `IdaIpyClient` 公有接口
- 不修改服务端插件代码本身

## 决策

### 1. 新顶层结构

**决策:** 采用以下结构:
```
idaipy/
├── scripts/              # 仅 install_plugin.py
│   └── install_plugin.py
├── client/               # Python 包
│   ├── src/idaipy/     # 源码 (pip install -e .)
│   ├── docs/             # 客户端文档
│   └── pyproject.toml
├── server/               # IDA 插件
│   ├── plugin/           # plugin.py + server/
│   ├── docs/             # 服务端文档
│   └── pyproject.toml
├── tools/                # 工具脚本（非 IDA 执行）
│   ├── restart_ida.py
│   └── search_ball_selectors.py
├── tests/                # 测试脚本
│   ├── test_plugin.py
│   ├── test_module.py
│   └── test_modules/
├── docs/                 # 概述 + 索引
│   ├── README.md
│   ├── README-en.md
│   ├── design/
│   ├── client/
│   └── server/
└── example/              # 示例脚本
    ├── basic_info.py
    └── my_analysis/
```

**理由:** 按功能清晰分离。`scripts/` 最小化且专注。`tools/` 存放非 IDA 执行的工具。

### 2. 客户端目录结构

**决策:** 使用 `src/` 布局进行规范 pip 打包:
```
client/
├── src/idaipy/
│   ├── __init__.py
│   ├── client.py
│   ├── cli.py
│   └── result.py
├── docs/
│   ├── README.md
│   └── README-en.md
├── tests/
│   └── test_client.py
├── pyproject.toml
└── README.md              # 指向 docs/
```

**理由:** `src/` 布局是 Python 包的标准做法。包名 `idaipy` 简洁。

### 3. 服务端目录结构

**决策:** 服务端插件结构:
```
server/
├── plugin/               # IDA 插件目录
│   ├── __init__.py
│   ├── plugin.py         # IDA 插件入口
│   ├── server/           # 服务端核心代码
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── executor.py
│   │   └── config.py
│   └── pyproject.toml
├── docs/
│   └── ...
└── pyproject.toml        # 可选：服务端独立打包
```

**理由:** `idaipy_server/` 改为 `server/`，更简洁。服务端独立 `pyproject.toml` 支持后续独立发布。

### 4. 服务端工作区设计

**决策:** 服务端创建和使用 `~/.idaipy/` 及其结构:
```
~/.idaipy/
├── config/
│   └── server.json        # 端口、超时、调试设置
├── workspaces/            # 用户工作区
│   └── <workspace-id>/    # 每个工作区独立目录
├── cache/                  # 执行缓存
│   └── <session-id>/
├── logs/
│   └── idaipy.log         # 结构化 JSON 日志
└── sockets/               # Unix 套接字文件 (Linux/macOS)
    └── idaipy.sock
```

**理由:** 所有服务端状态在一个目录中。工作区隔离。日志统一。缓存允许临时文件清理。

### 5. 文档组织

**决策:** 按组件组织文档:
```
docs/
├── README.md              # 概述、快速开始、导航
├── README-en.md
├── design/
│   └── DESIGN.md
├── client/
│   ├── README.md
│   └── README-en.md
└── server/
    ├── README.md
    ├── README-en.md
    └── TROUBLESHOOTING.md
```

**理由:** 清晰的导航。每个组件有自己的文档文件夹。

### 6. Install 脚本只保留一处

**决策:** `scripts/install_plugin.py` 是唯一的安装脚本入口。

**理由:** 避免重复和符号链接的复杂性。安装脚本只需引用正确的服务端路径 `server/plugin/`。

### 7. mrs_scan.py 是示例脚本

**决策:** `mrs_scan.py` 移到 `example/` 目录。

**理由:** `mrs_scan.py` 使用 `WORKSPACE` 变量，是 IdaIpy 的使用示例，不是通用工具。

## 风险 / 权衡

- [风险] 移动文件破坏用户习惯
  → **缓解:** 更新所有文档，在发布说明中提供迁移说明

- [风险] 客户端依赖 `scripts/` 路径获取 `install_plugin.py`
  → **缓解:** `scripts/install_plugin.py` 保持相同相对路径，仅其他文件移动

- [风险] 现有用户 `~/.idaipy/` 目录迁移
  → **缓解:** 服务端首次运行创建新结构，旧日志保留在原位

## 待解决问题

1. 是否提供 `idaipy-cleanup` 工具来迁移现有 `~/.idaipy/` 到新结构?
2. 服务端 `pyproject.toml` 是否需要？目前插件直接 copy 到 IDA 目录
