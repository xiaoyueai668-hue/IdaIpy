## ADDED Requirements

### Requirement: 主要文档提供英文版本

项目主要文档 SHALL 提供中英文两个版本。

#### Scenario: README 中英文版本存在
- **WHEN** 用户访问文档目录
- **THEN** `docs/README.md`（中文）存在
- **AND** `docs/README-en.md`（英文）存在

#### Scenario: 设计文档中英文版本存在
- **WHEN** 用户访问设计文档目录
- **THEN** `docs/design/DESIGN.md`（中文）存在
- **AND** `docs/design/DESIGN-en.md`（英文）存在

#### Scenario: 故障排查文档中英文版本存在
- **WHEN** 用户访问文档目录
- **THEN** `docs/TROUBLESHOOTING.md`（中文）存在
- **AND** `docs/TROUBLESHOOTING-en.md`（英文）存在

### Requirement: 英文版本命名规范

英文版本文档 SHALL 使用 `-en.md` 后缀命名。

#### Scenario: 文件命名符合规范
- **WHEN** 用户列出文档目录
- **THEN** 所有英文版本文件名格式为 `<name>-en.md`

### Requirement: 英文版本为中文版本的翻译

英文版本 SHALL 是中文版本的翻译，内容保持一致。

#### Scenario: 英文版本包含相同主题
- **WHEN** 用户阅读英文文档
- **THEN** 英文文档涵盖与中文文档相同的主题和结构
