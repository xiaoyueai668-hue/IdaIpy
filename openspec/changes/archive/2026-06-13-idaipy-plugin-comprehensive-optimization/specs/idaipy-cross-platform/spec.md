## 新增需求

### 需求：跨平台安装脚本
`install_plugin.py` 脚本 SHALL 自动检测操作系统和 IDA 安装路径。

#### 场景：macOS 检测
- **WHEN** 脚本在 macOS 上运行（`sys.platform == "darwin"`）
- **THEN** 检查 `/Applications/MDA.app` 和 `/Applications/IDA Pro.app`
- **AND** 安装到 `Contents/MacOS/plugins`

#### 场景：Linux 检测
- **WHEN** 脚本在 Linux 上运行（`sys.platform.startswith("linux")"`）
- **THEN** 检查 `~/idapro-9.2`、`~/idapro-9.1`、`~/idapro-9.0`
- **AND** 安装到 `idalinux64/plugins`

#### 场景：Windows 检测
- **WHEN** 脚本在 Windows 上运行（`sys.platform == "win32"`）
- **THEN** 检查 `C:\Program Files\IDA Pro 9.2`（及 9.1、9.0）
- **AND** 安装到 `plugins` 子目录

#### 场景：IDA 未找到时给出有用提示
- **WHEN** 脚本找不到 IDA 安装
- **THEN** 打印手动指定 `--ida-path` 的说明

### 需求：IDA 版本检测
脚本 SHALL 检测已安装的 IDA 版本并相应适配。

#### 场景：检测 IDA 9.2
- **WHEN** IDA 9.2 已安装
- **THEN** 插件使用 9.2 相应的 API 调用

#### 场景：检测 IDA 9.1
- **WHEN** IDA 9.1 已安装
- **THEN** 插件使用 9.1 相应的 API 调用

#### 场景：检测 IDA 9.0
- **WHEN** IDA 9.0 已安装
- **THEN** 插件使用 9.0 相应的 API 调用

### 需求：手动 IDA 路径覆盖
安装脚本 SHALL 接受 `--ida-path` 以覆盖自动检测。

#### 场景：指定手动路径
- **WHEN** 用户运行 `python3 install_plugin.py --ida-path /custom/path/to/IDA`
- **THEN** 脚本无论自动检测结果如何都使用指定路径
