"""run_script 示例 — 收集 SO 基本信息。

用法:
    python3 -c "
    from idaipy import IdaIpyClient
    with IdaIpyClient() as c:
        data = c.run_script_json('example/basic_info.py')
        print(data)
    "

    # 或用 CLI:
    idaipy run example/basic_info.py --json
"""

import json
import idc
import idaapi
import idautils
import ida_funcs
import ida_segment
import ida_ida

segments = []
for ea in idautils.Segments():
    seg = ida_segment.getseg(ea)
    segments.append({
        "name": ida_segment.get_segm_name(seg),
        "start": hex(seg.start_ea),
        "end": hex(seg.end_ea),
        "size": seg.end_ea - seg.start_ea,
    })

func_count = ida_funcs.get_func_qty()
first_funcs = []
for i, ea in enumerate(idautils.Functions()):
    if i >= 5:
        break
    first_funcs.append({
        "ea": hex(ea),
        "name": idc.get_func_name(ea),
    })

print(json.dumps({
    "file": idc.get_input_file_path(),
    "ida_version": idaapi.get_kernel_version(),
    "bits": ida_ida.inf_get_app_bitness(),
    "processor": ida_ida.inf_get_procname(),
    "segment_count": len(segments),
    "segments": segments,
    "function_count": func_count,
    "first_functions": first_funcs,
}))
