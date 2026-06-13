# IdaIpy 服务端

IDA Pro 插件，通过 RPyC 提供远程代码执行服务。

## 安装

```bash
python3 scripts/install_plugin.py
```

安装后，在 IDA 中按下 **Ctrl+Shift+R** 启动/停止服务。

## 服务地址

- 默认地址：`127.0.0.1:7123`
- 仅监听本地连接（安全）

## 配置

服务端配置位于 `server/plugin/config.py`：
- `HOST = "127.0.0.1"`
- `PORT = 7123`
- `TIMEOUT = 300`

## 日志

日志位于 `~/.idaipy/` 目录：
- `logs/idaipy.log` - 结构化 JSON 日志

## 故障排查

参见 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)（中文）
