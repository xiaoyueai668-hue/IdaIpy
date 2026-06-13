#!/usr/bin/env python3
"""模块依赖加载测试。

验证多层模块依赖的自动加载：
  test_modules/
  ├── helper.py            被依赖的工具模块
  ├── analyzer.py          依赖 helper + utils.formatter
  └── utils/
      └── formatter.py     子目录工具模块

测试两种模式：
  1. Workspace 模式 — 设置目录后服务端直接 import
  2. Push 模式 — 推送文件到服务端临时目录
"""

import json
import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_client_dir = os.path.join(os.path.dirname(_script_dir), "client")
if _client_dir not in sys.path:
    sys.path.insert(0, _client_dir)


def test(host="127.0.0.1", port=7123):
    from idaipy import IdaIpyClient

    passed, failed = 0, 0

    def check(name, ok, detail=""):
        nonlocal passed, failed
        if ok:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}: {detail}")

    # ── 连接 ──────────────────────────────────────

    print("=== 模块依赖加载测试 ===\n")
    client = IdaIpyClient(host=host, port=port, auto_push=False)
    try:
        client.connect()
    except ConnectionRefusedError:
        print(f"  连接失败: {host}:{port}")
        return False
    check("connect", client.is_connected())

    # ── Workspace 模式 ────────────────────────────
    # 把 scripts/ 目录设为 workspace，这样 test_modules 包可以被 import

    print("\n--- Workspace 模式 ---")
    ws = client.set_workspace(_script_dir)
    check("set_workspace", _script_dir in ws)

    # 清除旧缓存，执行 analyzer（它会自动 import helper + utils.formatter）
    r = client._exec_code("""
import sys, json
for m in list(sys.modules):
    if m.startswith('test_modules'):
        del sys.modules[m]
from test_modules.analyzer import run_analysis
result = run_analysis()
print(json.dumps(result))
""", mode="main_read")

    check("exec analyzer", r.get("status") == "ok", r.get("traceback", ""))
    if r.get("status") == "ok":
        data = json.loads(r.stdout.strip().split("\n")[-1])
        check("依赖加载: func_count", data.get("func_count", 0) > 0)
        check("依赖加载: segments", data.get("segment_count", 0) > 0)
        check("依赖加载: first_function", data.get("first_function", {}).get("name", "") != "")
        check("整体 status", data.get("status") == "ok")
        print(f"    函数总数: {data.get('func_count')}")
        print(f"    段数量: {data.get('segment_count')}")
        print(f"    首函数: {data.get('first_function')}")

    # ── 验证模块已加载 ────────────────────────────

    if r.get("status") == "ok":
        check("子目录依赖: formatter", "first_formatted" in data)
        if "first_formatted" in data:
            fmt = data["first_formatted"]
            check("formatter 输出", fmt.get("display", "") != "" and "0x" in fmt.get("address", ""))
            print(f"    格式化: {fmt.get('display')}")

    r2 = client._exec_code("""
import sys, json
loaded = [m for m in sys.modules if m.startswith('test_modules')]
print(json.dumps(sorted(loaded)))
""", mode="main_read")
    if r2.get("status") == "ok":
        modules = json.loads(r2.stdout.strip())
        check("helper 已加载", "test_modules.helper" in modules, modules)
        check("analyzer 已加载", "test_modules.analyzer" in modules, modules)
        check("utils.formatter 已加载", "test_modules.utils.formatter" in modules, modules)
        print(f"    已加载模块: {modules}")

    # ── Push 模式 ─────────────────────────────────

    print("\n--- Push 模式 ---")

    # 先清除 workspace 和已加载模块
    client.clear_workspace()
    client._exec_code("""
import sys
for m in list(sys.modules):
    if m.startswith('test_modules'):
        del sys.modules[m]
""", mode="main_read")

    # 用 push_modules 推送文件
    modules_dir = os.path.join(_script_dir, "test_modules")
    file_map = {}
    for root, _, files in os.walk(modules_dir):
        for f in files:
            if f.endswith(".py"):
                full = os.path.join(root, f)
                rel = os.path.join("test_modules", os.path.relpath(full, modules_dir))
                with open(full) as fh:
                    file_map[rel] = fh.read()

    push_result = client._conn.root.push_modules(file_map)
    check("push_modules", "Pushed" in str(push_result), push_result)
    print(f"    {push_result}")

    # 再次执行 analyzer
    r3 = client._exec_code("""
import json
from test_modules.analyzer import run_analysis
result = run_analysis()
print(json.dumps(result))
""", mode="main_read")

    check("push 模式执行", r3.get("status") == "ok", r3.get("traceback", ""))
    if r3.get("status") == "ok":
        data3 = json.loads(r3.stdout.strip().split("\n")[-1])
        check("push 依赖加载", data3.get("status") == "ok")
        print(f"    函数总数: {data3.get('func_count')}")

    # ── 清理 ──────────────────────────────────────

    client.close()

    total = passed + failed
    print(f"\n{'='*40}")
    print(f"总计: {total}  通过: {passed}  失败: {failed}")
    print(f"{'全部通过!' if failed == 0 else '存在失败'}")
    return failed == 0


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 7123
    sys.exit(0 if test(host, port) else 1)
