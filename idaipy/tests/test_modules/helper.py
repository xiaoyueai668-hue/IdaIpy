"""被依赖的工具模块。"""

import idautils
import idc
import ida_funcs


def count_functions():
    """返回函数总数。"""
    return ida_funcs.get_func_qty()


def list_segments():
    """返回段名列表。"""
    import ida_segment
    return [ida_segment.get_segm_name(ida_segment.getseg(ea))
            for ea in idautils.Segments()]


def get_first_function():
    """返回第一个函数的名称、地址和大小。"""
    ea = next(idautils.Functions())
    f = ida_funcs.get_func(ea)
    return {
        "address": hex(ea),
        "name": idc.get_func_name(ea),
        "size": f.end_ea - f.start_ea if f else 0,
    }
