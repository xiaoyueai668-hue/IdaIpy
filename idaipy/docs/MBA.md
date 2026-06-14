# IdaIpy MBA 微码优化框架

## 1. MBA 模块架构

```mermaid
flowchart TB
    subgraph IdaIpyPlugin["idaipy 插件"]
        PluginInit["plugin.py<br/>init()"]
    end

    subgraph IdaMba["ida_mba 模块"]
        MbaManager["MbaOptimizerManager"]
        InsManager["InstructionOptimizerManager<br/>optinsn_t"]
        BlkManager["BlockOptimizerManager<br/>optblock_t"]
        MbaManager --> InsManager
        MbaManager --> BlkManager
    end

    PluginInit --> |set_manager| MbaManager
    InsManager --> |hook| HexRays["ida_hexrays"]
    BlkManager --> |hook| HexRays
```

---

## 2. 微码 Maturity 流程

```mermaid
flowchart LR
    subgraph Maturity["微码成熟度级别"]
        ZERO["ZERO 0"]
        GEN["GENERATED 1"]
        PRE["PREOPTIMIZED 2"]
        LOOP["LOOP 3"]
        LOCOPT["LOCOPT 4"]
        CALLS["CALLS 5"]
        GLB1["GLBOPT1 6"]
        GLB2["GLBOPT2 7"]
        GLB3["GLBOPT3 8"]
        HIGH["HIGH 9"]
    end

    ZERO --> GEN --> PRE --> LOOP --> LOCOPT --> CALLS --> GLB1 --> GLB2 --> GLB3 --> HIGH

    subgraph Rules["规则类型"]
        Instruction["InstructionRule<br/>MATURITIES: LOCOPT, GLBOPT1"]
        Block["BlockRule<br/>MATURITIES: CALLS, GLBOPT1, GLBOPT2"]
    end

    Instruction -.-> |触发| LOCOPT
    Instruction -.-> |触发| GLB1
    Block -.-> |触发| CALLS
    Block -.-> |触发| GLB1
    Block -.-> |触发| GLB2
```

---

## 3. Handler 热更新流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as idaipy CLI
    participant Client as IdaIpyClient
    participant Service as IDAService
    participant Manager as MbaOptimizerManager
    participant Handler as ~/.idaipy/handlers/xxx.py

    User->>CLI: idaipy mba reload deflatten
    CLI->>Client: reload_mba_handler("deflatten")
    Client->>Service: reload_mba_handler(name)

    Service->>Handler: 读取文件
    Service->>Service: 删除 sys.modules["mba_handlers.xxx"]

    Service->>Handler: 重新加载模块
    Service->>Service: 创建新规则实例

    Service->>Manager: add_blk_rule(new_rule)
    Manager-->>Service: 注册成功

    Service-->>Client: {"status": "ok", "rule_count": 1}
    Client-->>CLI: Result
    CLI-->>User: 热更新成功
```

---

## 4. MBA 命令

```mermaid
graph LR
    subgraph Commands["MBA 命令"]
        List["idaipy mba list"]
        Reload["idaipy mba reload <name>"]
        Status["idaipy mba status <name>"]
    end

    List --> |列出所有 handlers| Result1["handler 列表"]
    Reload --> |热更新指定 handler| Result2["status: ok"]
    Status --> |查看状态| Result3["loaded/registered"]
```

---

## 5. Handler 开发

### 文件位置

```
~/.idaipy/handlers/
├── deflatten.py      # 控制流反扁平化
├── switch_fix.py     # switch 优化
└── ...
```

### Handler 示例

```python
from ida_mba.mba_optimizer import BlockRule, Maturity

class DeflattenRule(BlockRule):
    """检测并去除 OLLVM 控制流平坦化"""
    MATURITIES = [Maturity.CALLS, Maturity.GLBOPT1, Maturity.GLBOPT2]

    def optimize(self, blk) -> int:
        # 检测分发器块
        if len(list(blk.predset)) > 10:
            return 0  # TODO: 实现 CFG 重构
        return 0

RULE = DeflattenRule
```

### 注册方式

| 方式 | 说明 |
|------|------|
| `RULE = MyRule` | 单个规则 |
| `HANDLERS = [("name", rule_instance), ...]` | 多个规则 |

---

## 6. 规则类型

| 类型 | 基类 | 默认 Maturity | 用途 |
|------|------|---------------|------|
| 指令规则 | `InstructionRule` | LOCOPT, GLBOPT1 | 指令级转换 |
| 块规则 | `BlockRule` | CALLS, GLBOPT1, GLBOPT2 | 块级转换 |

### 方法签名

```python
class InstructionRule:
    def optimize(self, blk, ins) -> bool:
        """优化指令，返回 True 表示进行了修改"""
        raise NotImplementedError

class BlockRule:
    def optimize(self, blk) -> int:
        """优化块，返回修改数量"""
        raise NotImplementedError
```
