"""分析辅助模块 — 被 main.py 导入。"""

import idc
import idautils
import ida_funcs


def get_function_distribution():
    """统计函数大小分布。"""
    dist = {"tiny": 0, "small": 0, "medium": 0, "large": 0}
    for ea in idautils.Functions():
        f = ida_funcs.get_func(ea)
        if not f:
            continue
        size = f.end_ea - f.start_ea
        if size < 16:
            dist["tiny"] += 1
        elif size < 256:
            dist["small"] += 1
        elif size < 4096:
            dist["medium"] += 1
        else:
            dist["large"] += 1
    return dist


def find_special_instructions(limit=50):
    """扫描特殊指令 (MRS, SVC, BR)。"""
    results = {"mrs": [], "svc": [], "br": []}
    text_seg = None
    import ida_segment
    for ea in idautils.Segments():
        seg = ida_segment.getseg(ea)
        if ida_segment.get_segm_name(seg) == ".text":
            text_seg = seg
            break

    if not text_seg:
        return results

    ea = text_seg.start_ea
    while ea < text_seg.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem == "MRS" and len(results["mrs"]) < limit:
            results["mrs"].append(hex(ea))
        elif mnem == "SVC" and len(results["svc"]) < limit:
            results["svc"].append(hex(ea))
        elif mnem == "BR" and len(results["br"]) < limit:
            results["br"].append(hex(ea))
        ea = idc.next_head(ea, text_seg.end_ea)

    return results
