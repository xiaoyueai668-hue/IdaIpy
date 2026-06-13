# server-workspace

## 新增需求

### 需求: 服务端主目录
服务端 SHALL 使用 `~/.idaipy/` 作为所有服务端状态的主目录。

### 需求: 目录结构
服务端 SHALL 在 `~/.idaipy/` 下创建和使用以下子目录:
- `config/` - 服务端配置文件
- `workspaces/` - 用户工作区目录
- `cache/` - 执行缓存和临时文件
- `logs/` - 结构化日志文件
- `sockets/` - Unix 套接字文件 (Linux/macOS)

### 需求: 工作区隔离
每个用户工作区 SHALL 在 `~/.idaipy/workspaces/<workspace-id>/` 下独立存放。

### 需求: 日志整合
所有结构化日志 SHALL 写入 `~/.idaipy/logs/idaipy.log`，格式为 JSON。

### 需求: 缓存管理
服务端 SHALL 使用 `~/.idaipy/cache/` 存储临时执行文件，并自动清理旧会话。

### 需求: 配置文件
服务端 SHALL 将运行时配置存储在 `~/.idaipy/config/server.json`（端口、超时、调试设置）。
