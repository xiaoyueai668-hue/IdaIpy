"""MRS 指令扫描与函数映射

远程执行时使用 WORKSPACE 变量决定输出路径。
"""
import idautils
import idaapi
import idc
import json
import os

# WORKSPACE 由远程执行引擎自动注入，本地运行时 fallback 到脚本所在目录
_ws = globals().get("WORKSPACE", "")
if _ws:
    OUTPUT_DIR = os.path.join(_ws, "data")
else:
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "mrs_functions.json")


def find_mrs_instructions():
    """查找所有 MRS 指令及其所在函数"""
    mrs_data = []
    mrs_addresses = []
    functions_with_mrs = set()

    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            if not idc.is_code(idaapi.get_full_flags(head)):
                continue
            if idc.print_insn_mnem(head).lower() != "mrs":
                continue

            mrs_addresses.append(f"0x{head:X}")
            func_addr = idc.get_func_attr(head, idc.FUNCATTR_START)
            func_addr_hex = f"0x{func_addr:X}" if func_addr != idc.BADADDR else None

            if func_addr_hex:
                functions_with_mrs.add(func_addr_hex)

            mrs_data.append({
                "mrs_address": f"0x{head:X}",
                "function_address": func_addr_hex or "N/A",
            })

    return mrs_data, mrs_addresses, functions_with_mrs


def get_all_functions():
    """获取所有函数的地址和名称"""
    return [
        {"function_address": f"0x{ea:X}", "function_name": idc.get_func_name(ea)}
        for ea in idautils.Functions()
    ]


def save_results(mrs_data, mrs_addresses, functions_with_mrs, all_functions):
    """保存结果为 JSON"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = {
        "mrs_instructions": mrs_data,
        "total_mrs_count": len(mrs_addresses),
        "mrs_addresses": mrs_addresses,
        "functions_with_mrs": list(functions_with_mrs),
        "total_functions_with_mrs_count": len(functions_with_mrs),
        "all_functions": all_functions,
        "total_functions_count": len(all_functions),
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"Results saved to {OUTPUT_FILE}")


def scan_mrs():
    """执行 MRS 扫描并保存结果"""
    mrs_data, mrs_addresses, functions_with_mrs = find_mrs_instructions()
    all_functions = get_all_functions()

    print(f"Total MRS: {len(mrs_addresses)}")
    print(f"Functions with MRS: {len(functions_with_mrs)}")
    print(f"Total Functions: {len(all_functions)}")

    save_results(mrs_data, mrs_addresses, functions_with_mrs, all_functions)


if __name__ == "__main__":
    scan_mrs()
