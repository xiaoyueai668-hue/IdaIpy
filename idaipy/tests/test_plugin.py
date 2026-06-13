#!/usr/bin/env python3
"""IdaIpy 插件综合测试。

覆盖 45 项测试：连接、Ping、Status、同步执行（3 种模式）、
文件信息、段信息、函数列表/详情、反汇编、F5 伪代码、
内存读取、指令解码、交叉引用、字符串列表、
异步/批量执行、Workspace、任务管理、断开重连。

用法：python3 test_plugin.py [host] [port]
"""

import json
import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_client_dir = os.path.join(os.path.dirname(_script_dir), "client")
if _client_dir not in sys.path:
    sys.path.insert(0, _client_dir)


def _exec_json(client, code):
    """执行代码并解析 stdout 最后一行的 JSON。"""
    r = client._exec_code(code, mode="main_read")
    if r.get("status") != "ok":
        return None, r
    stdout = r.get("stdout", "").strip()
    if not stdout:
        return None, r
    try:
        return json.loads(stdout.split("\n")[-1]), r
    except (json.JSONDecodeError, IndexError, KeyError):
        return None, r


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

    print("=== 连接测试 ===")
    client = IdaIpyClient(host=host, port=port, auto_push=False)
    try:
        client.connect()
    except ConnectionRefusedError:
        print(f"  连接失败: {host}:{port}")
        print("  请先在 IDA 中按 Ctrl+Shift+R 启动服务")
        return False
    check("connect", client.is_connected())

    # ── Ping ──────────────────────────────────────

    print("\n=== Ping ===")
    info = client.ping()
    check("ping", info.get("status") == "ok")
    check("ida_version", "9." in str(info.get("ida_version", "")),
          info.get("ida_version"))

    # ── Status ────────────────────────────────────

    print("\n=== Status ===")
    st = client.status()
    check("status", st.get("status") == "running")
    check("python_version", "3." in st.get("python_version", ""),
          st.get("python_version"))

    # ── 同步执行 ──────────────────────────────────

    print("\n=== 同步执行 ===")

    r = client._exec_code("print('hello')", mode="main_read")
    check("exec main_read", r.get("status") == "ok" and "hello" in r.get("stdout", ""))

    r = client._exec_code("print('write')", mode="main_write")
    check("exec main_write", r.get("status") == "ok" and "write" in r.get("stdout", ""))

    r = client._exec_code("x = 1 + 2; print(x)", mode="background")
    check("exec background", r.get("status") == "ok" and "3" in r.get("stdout", ""))

    r = client._exec_code("raise ValueError('test error')")
    check("exec error handling", r.get("status") == "error"
          and r.get("error_type") == "ValueError")

    # ── 文件信息 ──────────────────────────────────

    print("\n=== 文件信息 ===")

    data, r = _exec_json(client, """
import idaapi, idc, ida_ida, json
info = {
    "input_file": idc.get_input_file_path(),
    "ida_version": idaapi.get_kernel_version(),
    "processor": ida_ida.inf_get_procname(),
    "bits": 64 if ida_ida.inf_is_64bit() else 32,
    "entry_point": hex(idc.get_inf_attr(idc.INF_START_EA)),
}
print(json.dumps(info))
""")
    check("file_info", isinstance(data, dict) and "input_file" in data)
    if isinstance(data, dict):
        check("processor", len(data.get("processor", "")) > 0, data.get("processor"))
        check("bits", data.get("bits") in (32, 64), data.get("bits"))
        check("entry_point", data.get("entry_point", "").startswith("0x"))

    # ── 段信息 ────────────────────────────────────

    print("\n=== 段信息 ===")

    data, r = _exec_json(client, """
import idautils, ida_segment, json
segs = []
for ea in idautils.Segments():
    seg = ida_segment.getseg(ea)
    segs.append({
        "name": ida_segment.get_segm_name(seg),
        "start": hex(seg.start_ea),
        "end": hex(seg.end_ea),
        "size": seg.end_ea - seg.start_ea,
    })
print(json.dumps(segs))
""")
    check("segments", isinstance(data, list) and len(data) > 0)
    if isinstance(data, list) and data:
        check("segment has name", "name" in data[0])
        check("segment has start/end", "start" in data[0] and "end" in data[0])
        seg_names = [s["name"] for s in data]
        print(f"    段列表: {seg_names}")

    # ── 函数列表 ──────────────────────────────────

    print("\n=== 函数列表 ===")

    data, r = _exec_json(client, """
import idautils, idc, ida_funcs, json
count = ida_funcs.get_func_qty()
funcs = []
for ea in idautils.Functions():
    funcs.append({
        "address": hex(ea),
        "name": idc.get_func_name(ea),
    })
    if len(funcs) >= 5:
        break
print(json.dumps({"count": count, "sample": funcs}))
""")
    check("function_count", isinstance(data, dict) and data.get("count", 0) > 0,
          data.get("count") if isinstance(data, dict) else data)
    if isinstance(data, dict):
        sample = data.get("sample", [])
        check("function_sample", len(sample) > 0)
        if sample:
            check("function has name", "name" in sample[0] and len(sample[0]["name"]) > 0)
        print(f"    函数总数: {data.get('count')}")

    # ── 函数详情 ──────────────────────────────────

    print("\n=== 函数详情 ===")

    data, r = _exec_json(client, """
import idautils, idc, ida_funcs, json
ea = next(idautils.Functions())
f = ida_funcs.get_func(ea)
detail = {
    "start": hex(f.start_ea),
    "end": hex(f.end_ea),
    "name": idc.get_func_name(f.start_ea),
    "size": f.end_ea - f.start_ea,
    "frame_size": idc.get_func_attr(f.start_ea, idc.FUNCATTR_FRSIZE),
}
print(json.dumps(detail))
""")
    check("function_detail", isinstance(data, dict) and "start" in data)
    if isinstance(data, dict):
        check("func has size", data.get("size", 0) > 0)
        print(f"    首个函数: {data.get('name')} [{data.get('start')} - {data.get('end')}]")

    # ── 反汇编 ────────────────────────────────────

    print("\n=== 反汇编 ===")

    data, r = _exec_json(client, """
import idautils, idc, idaapi, json
ea = next(idautils.Functions())
lines = []
cur = ea
for _ in range(10):
    if cur == idc.BADADDR:
        break
    lines.append({
        "address": hex(cur),
        "disasm": idc.GetDisasm(cur),
        "mnem": idc.print_insn_mnem(cur),
    })
    cur = idc.next_head(cur)
print(json.dumps(lines))
""")
    check("disasm", isinstance(data, list) and len(data) > 0)
    if isinstance(data, list) and data:
        check("disasm has mnem", "mnem" in data[0] and len(data[0]["mnem"]) > 0)
        for line in data[:3]:
            print(f"    {line.get('address')}: {line.get('disasm')}")

    # ── F5 伪代码 ─────────────────────────────────

    print("\n=== F5 伪代码 ===")

    data, r = _exec_json(client, """
import idautils, idc, ida_hexrays, json
ea = next(idautils.Functions())
cfunc = ida_hexrays.decompile(ea)
result = {
    "address": hex(ea),
    "name": idc.get_func_name(ea),
    "pseudocode": str(cfunc) if cfunc else None,
    "lines": len(str(cfunc).splitlines()) if cfunc else 0,
}
print(json.dumps(result))
""")
    check("decompile", isinstance(data, dict) and data.get("pseudocode") is not None)
    if isinstance(data, dict) and data.get("pseudocode"):
        check("pseudocode has content", data.get("lines", 0) > 0)
        preview = data["pseudocode"][:120].replace("\n", " ")
        print(f"    {data.get('name')}: {preview}...")

    # ── 内存读取 ──────────────────────────────────

    print("\n=== 内存读取 ===")

    data, r = _exec_json(client, """
import idc, idautils, json
ea = next(idautils.Functions())
raw = idc.get_bytes(ea, 16)
result = {
    "address": hex(ea),
    "hex": raw.hex() if raw else None,
    "dword": idc.get_wide_dword(ea),
    "size": idc.get_item_size(ea),
}
print(json.dumps(result))
""")
    check("read_bytes", isinstance(data, dict) and data.get("hex") is not None)
    if isinstance(data, dict):
        check("read_dword", isinstance(data.get("dword"), int))
        print(f"    {data.get('address')}: {data.get('hex')}")

    # ── 指令解码 ──────────────────────────────────

    print("\n=== 指令解码 ===")

    data, r = _exec_json(client, """
import ida_ua, idc, idautils, json
ea = next(idautils.Functions())
insn = ida_ua.insn_t()
length = ida_ua.decode_insn(insn, ea)
ops = []
for i in range(6):
    if insn.ops[i].type == ida_ua.o_void:
        break
    ops.append({"index": i, "text": idc.print_operand(ea, i), "type": insn.ops[i].type})
result = {"address": hex(ea), "mnem": idc.print_insn_mnem(ea), "size": length, "operands": ops}
print(json.dumps(result))
""")
    check("decode_insn", isinstance(data, dict) and data.get("mnem"))
    if isinstance(data, dict):
        check("insn has operands", len(data.get("operands", [])) > 0)
        ops_str = ", ".join(o["text"] for o in data.get("operands", []))
        print(f"    {data.get('address')}: {data.get('mnem')} {ops_str}")

    # ── 交叉引用 ──────────────────────────────────

    print("\n=== 交叉引用 ===")

    data, r = _exec_json(client, """
import idautils, idc, ida_funcs, json
funcs = list(idautils.Functions())
ea = funcs[min(5, len(funcs)-1)]
xrefs_to = [{"from": hex(x.frm), "type": x.type} for x in idautils.XrefsTo(ea)][:10]
xrefs_from = [{"to": hex(x.to), "type": x.type} for x in idautils.XrefsFrom(ea)][:10]
print(json.dumps({"to": xrefs_to, "from": xrefs_from, "address": hex(ea), "name": idc.get_func_name(ea)}))
""")
    check("xrefs", isinstance(data, dict))
    if isinstance(data, dict):
        to_count = len(data.get("to", []))
        from_count = len(data.get("from", []))
        has_refs = to_count > 0 or from_count > 0
        check("xrefs has refs", has_refs, f"to={to_count}, from={from_count}")
        print(f"    {data.get('name')} @ {data.get('address')}: xrefs_to={to_count}, xrefs_from={from_count}")

    # ── 字符串列表 ────────────────────────────────

    print("\n=== 字符串列表 ===")

    data, r = _exec_json(client, """
import idc, ida_strlist, json
count = ida_strlist.get_strlist_qty()
strs = []
sl = ida_strlist.string_info_t()
for i in range(min(count, 10)):
    if not ida_strlist.get_strlist_item(sl, i):
        continue
    s = idc.get_strlit_contents(sl.ea, sl.length, idc.STRTYPE_C)
    if s:
        try:
            strs.append({"address": hex(sl.ea), "value": s.decode("utf-8", errors="replace")})
        except Exception:
            pass
print(json.dumps({"count": count, "sample": strs}))
""")
    check("strings", isinstance(data, dict) and data.get("count", 0) > 0)
    if isinstance(data, dict):
        sample = data.get("sample", [])
        check("string sample", len(sample) > 0)
        print(f"    字符串总数: {data.get('count')}")
        for s in sample[:3]:
            print(f"    {s.get('address')}: {s.get('value')[:60]}")

    # ── 异步执行 ──────────────────────────────────

    print("\n=== 异步执行 ===")

    tid = client.exec_async("import time; time.sleep(0.1); print('async_ok')")
    check("exec_async returns task_id", tid is not None and len(tid) > 0)

    result = client.wait_task(tid, poll_interval=0.2, timeout=5)
    check("wait_task done", result.get("state") == "done")
    async_result = result.get("result") or {}
    check("async stdout", "async_ok" in str(async_result.get("stdout", "")))

    # ── 批量执行 ──────────────────────────────────

    print("\n=== 批量执行 ===")

    items = [f"print({i})" for i in range(10)]
    tid = client.exec_batch(items, chunk_size=3, yield_ms=50)
    check("exec_batch returns task_id", tid is not None)

    result = client.wait_task(tid, poll_interval=0.2, timeout=10)
    check("batch done", result.get("state") == "done")

    # ── Workspace ─────────────────────────────────

    print("\n=== Workspace ===")

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
    ws_result = client.set_workspace(project_root)
    check("set_workspace", project_root in ws_result)

    ws = client.get_workspace()
    check("get_workspace", ws == project_root)

    r = client._exec_code("import os; print(WORKSPACE)", mode="main_read")
    check("WORKSPACE injected", r.get("status") == "ok" and project_root in r.get("stdout", ""))

    client.clear_workspace()
    ws = client.get_workspace()
    check("clear_workspace", ws == "")

    # ── 任务管理 ──────────────────────────────────

    print("\n=== 任务管理 ===")

    tasks = client.list_tasks()
    check("list_tasks", isinstance(tasks, list))

    # ── 断开重连 ──────────────────────────────────

    print("\n=== 断开重连 ===")
    client.close()
    check("close", not client.is_connected())

    client.reconnect()
    check("reconnect", client.is_connected())

    info2 = client.ping()
    check("ping after reconnect", info2.get("status") == "ok")

    client.close()

    # ── 结果 ──────────────────────────────────────

    total = passed + failed
    print(f"\n{'='*40}")
    print(f"总计: {total}  通过: {passed}  失败: {failed}")
    print(f"{'全部通过!' if failed == 0 else '存在失败'}")
    return failed == 0


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 7123
    sys.exit(0 if test(host, port) else 1)
