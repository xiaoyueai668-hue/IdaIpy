"""run_project 示例 — 多文件分析项目。

项目结构:
    my_analysis/
        main.py      ← 入口（本文件）
        helpers.py   ← 辅助模块

用法:
    python3 -c "
    from idaipy import IdaIpyClient
    with IdaIpyClient() as c:
        r = c.run_project('example/my_analysis', entry='main.py')
        print(r['stdout'])
    "

    # 或用 CLI:
    idaipy run-project example/my_analysis --entry main.py
"""

import json
import idc
import idaapi
import ida_ida

from helpers import get_function_distribution, find_special_instructions

report = {
    "file": idc.get_input_file_path(),
    "ida_version": idaapi.get_kernel_version(),
    "bits": ida_ida.inf_get_app_bitness(),
    "function_distribution": get_function_distribution(),
    "special_instructions": {
        k: len(v) for k, v in find_special_instructions().items()
    },
}

total = sum(report["function_distribution"].values())
print(f"文件: {report['file']}")
print(f"IDA {report['ida_version']}, {report['bits']}bit")
print(f"函数: {total}")
for cat, cnt in report["function_distribution"].items():
    print(f"  {cat}: {cnt}")
si = report["special_instructions"]
print(f"特殊指令: MRS={si['mrs']}, SVC={si['svc']}, BR={si['br']}")

print(json.dumps(report))
