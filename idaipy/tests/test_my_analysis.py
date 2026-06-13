"""测试 run_project: my_analysis/"""

import json
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_plugin_root = os.path.dirname(_here)
_client_dir = os.path.join(_plugin_root, "client")
if _client_dir not in sys.path:
    sys.path.insert(0, _client_dir)

from idaipy import IdaIpyClient


def main():
    print("=== test_my_analysis: run_project 测试 ===\n")

    project_dir = os.path.join(_plugin_root, "example", "my_analysis")

    with IdaIpyClient() as c:
        r = c.run_project(project_dir, entry="main.py")

    assert r["status"] == "ok", \
        f"执行失败: {r.get('error_type')}: {r.get('error_message')}"

    stdout = r["stdout"].strip()
    last_line = stdout.rsplit("\n", 1)[-1]
    data = json.loads(last_line)

    assert "file" in data, "缺少 file 字段"
    assert data["bits"] in (32, 64), f"异常位数: {data['bits']}"
    dist = data["function_distribution"]
    assert sum(dist.values()) > 0, "函数分布为空"
    si = data["special_instructions"]
    assert isinstance(si, dict), "special_instructions 类型错误"

    lines = stdout.split("\n")
    for line in lines:
        if line.strip():
            print(f"  {line}")

    print(f"\n  --- 解析结果 ---")
    print(f"  文件: {data['file']}")
    print(f"  {data['ida_version']}, {data['bits']}bit")
    total = sum(dist.values())
    print(f"  函数: {total}")
    for cat, cnt in dist.items():
        print(f"    {cat}: {cnt}")
    print(f"  MRS: {si['mrs']}, SVC: {si['svc']}, BR: {si['br']}")

    print("\n[PASS] test_my_analysis 通过")


if __name__ == "__main__":
    main()
