"""测试 run_script: basic_info.py"""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_plugin_root = os.path.dirname(_here)
_client_dir = os.path.join(_plugin_root, "client")
if _client_dir not in sys.path:
    sys.path.insert(0, _client_dir)

from idaipy import IdaIpyClient


def main():
    print("=== test_basic: run_script 测试 ===\n")

    script = os.path.join(_here, "basic_info.py")

    with IdaIpyClient() as c:
        data = c.run_script_json(script)

    assert isinstance(data, dict), f"返回类型错误: {type(data)}"
    assert "file" in data, "缺少 file 字段"
    assert "ida_version" in data, "缺少 ida_version 字段"
    assert data["bits"] in (32, 64), f"异常位数: {data['bits']}"
    assert data["segment_count"] > 0, "段数为 0"
    assert data["function_count"] > 0, "函数数为 0"
    assert len(data["segments"]) == data["segment_count"]
    assert len(data["first_functions"]) <= 5

    print(f"  文件: {data['file']}")
    print(f"  IDA:  {data['ida_version']}")
    print(f"  位数: {data['bits']}bit, 处理器: {data['processor']}")
    print(f"  段:   {data['segment_count']}")
    print(f"  函数: {data['function_count']}")
    print(f"  前 {len(data['first_functions'])} 个函数:")
    for f in data["first_functions"]:
        print(f"    {f['ea']}  {f['name']}")

    print("\n[PASS] test_basic 通过")


if __name__ == "__main__":
    main()
