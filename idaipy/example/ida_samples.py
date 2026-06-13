"""IDA 只读 API 示例库。

所有函数只读取信息，不修改 IDA 数据库。
通过 IdaIpy 远程执行时 WORKSPACE 由引擎自动注入。

用法（远程）：
    from ida_samples import get_file_info, get_functions, get_pseudocode
    info = get_file_info()

用法（IDA 控制台）：
    import ida_samples
    ida_samples.get_segments()
"""
import idaapi
import idautils
import idc
import ida_funcs
import ida_segment
import ida_ua
import ida_hexrays
import json


# ── 1. 文件信息 ─────────────────────────────────

def get_file_info():
    """获取当前分析文件的基本信息"""
    import ida_ida
    return {
        "input_file": idc.get_input_file_path(),
        "ida_version": idaapi.get_kernel_version(),
        "processor": ida_ida.inf_get_procname(),
        "bits": 64 if ida_ida.inf_is_64bit() else 32,
        "entry_point": hex(idc.get_inf_attr(idc.INF_START_EA)),
        "min_ea": hex(idc.get_inf_attr(idc.INF_MIN_EA)),
        "max_ea": hex(idc.get_inf_attr(idc.INF_MAX_EA)),
    }


# ── 2. 段信息 ───────────────────────────────────

def get_segments():
    """获取所有段的信息"""
    segs = []
    for seg_ea in idautils.Segments():
        seg = ida_segment.getseg(seg_ea)
        segs.append({
            "name": ida_segment.get_segm_name(seg),
            "start": hex(seg.start_ea),
            "end": hex(seg.end_ea),
            "size": seg.end_ea - seg.start_ea,
            "perm": seg.perm,
        })
    return segs


# ── 3. 函数列表 ─────────────────────────────────

def get_functions(limit=0):
    """获取函数列表 (limit=0 表示全部)"""
    funcs = []
    for ea in idautils.Functions():
        f = ida_funcs.get_func(ea)
        funcs.append({
            "address": hex(ea),
            "name": idc.get_func_name(ea),
            "size": f.end_ea - f.start_ea if f else 0,
        })
        if limit and len(funcs) >= limit:
            break
    return funcs


def get_function_count():
    """获取函数总数"""
    return ida_funcs.get_func_qty()


def get_function_detail(ea):
    """获取单个函数的详细信息"""
    f = ida_funcs.get_func(ea)
    if not f:
        return None
    return {
        "start": hex(f.start_ea),
        "end": hex(f.end_ea),
        "name": idc.get_func_name(f.start_ea),
        "size": f.end_ea - f.start_ea,
        "flags": f.flags,
        "frame_size": idc.get_func_attr(f.start_ea, idc.FUNCATTR_FRSIZE),
    }


# ── 4. 汇编代码 ─────────────────────────────────

def get_disasm(ea, count=10):
    """从指定地址获取 count 条反汇编"""
    lines = []
    cur = ea
    for _ in range(count):
        if cur == idc.BADADDR:
            break
        lines.append({
            "address": hex(cur),
            "disasm": idc.GetDisasm(cur),
            "mnem": idc.print_insn_mnem(cur),
            "bytes": idc.get_bytes(cur, idc.get_item_size(cur)).hex(),
        })
        cur = idc.next_head(cur)
    return lines


def get_function_disasm(func_ea, max_lines=200):
    """获取整个函数的反汇编"""
    f = ida_funcs.get_func(func_ea)
    if not f:
        return []
    lines = []
    for head in idautils.Heads(f.start_ea, f.end_ea):
        if not idc.is_code(idaapi.get_full_flags(head)):
            continue
        lines.append({
            "address": hex(head),
            "disasm": idc.GetDisasm(head),
        })
        if len(lines) >= max_lines:
            break
    return lines


# ── 5. F5 伪代码 ─────────────────────────────────

def get_pseudocode(ea):
    """获取函数的 F5 反编译伪代码"""
    cfunc = ida_hexrays.decompile(ea)
    if not cfunc:
        return None
    return {
        "address": hex(ea),
        "name": idc.get_func_name(ea),
        "pseudocode": str(cfunc),
    }


# ── 6. 内存读取 ─────────────────────────────────

def read_bytes(ea, size):
    """从指定地址读取字节"""
    data = idc.get_bytes(ea, size)
    if data is None:
        return None
    return data.hex()


def read_dword(ea):
    """读取 4 字节整数"""
    return idc.get_wide_dword(ea)


def read_qword(ea):
    """读取 8 字节整数"""
    return idc.get_qword(ea)


# ── 7. 指令解码 ─────────────────────────────────

def decode_instruction(ea):
    """解码单条指令"""
    insn = ida_ua.insn_t()
    length = ida_ua.decode_insn(insn, ea)
    if length == 0:
        return None
    ops = []
    for i in range(6):
        op = insn.ops[i]
        if op.type == ida_ua.o_void:
            break
        ops.append({
            "index": i,
            "type": op.type,
            "text": idc.print_operand(ea, i),
        })
    return {
        "address": hex(ea),
        "mnem": idc.print_insn_mnem(ea),
        "size": length,
        "operands": ops,
    }


# ── 8. 交叉引用 ─────────────────────────────────

def get_xrefs_to(ea, limit=20):
    """获取指向 ea 的所有交叉引用"""
    refs = []
    for ref in idautils.XrefsTo(ea):
        refs.append({
            "from": hex(ref.frm),
            "type": ref.type,
        })
        if len(refs) >= limit:
            break
    return refs


def get_xrefs_from(ea, limit=20):
    """获取从 ea 出发的所有交叉引用"""
    refs = []
    for ref in idautils.XrefsFrom(ea):
        refs.append({
            "to": hex(ref.to),
            "type": ref.type,
        })
        if len(refs) >= limit:
            break
    return refs


# ── 9. 字符串列表 ────────────────────────────────

def get_strings(limit=20):
    """获取二进制中的字符串列表"""
    import ida_strlist
    count = ida_strlist.get_strlist_qty()
    strs = []
    sl = ida_strlist.string_info_t()
    for i in range(min(count, limit)):
        if not ida_strlist.get_strlist_item(sl, i):
            continue
        s = idc.get_strlit_contents(sl.ea, sl.length, idc.STRTYPE_C)
        if s:
            strs.append({
                "address": hex(sl.ea),
                "value": s.decode("utf-8", errors="replace"),
                "length": sl.length,
            })
    return strs
