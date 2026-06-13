"""子目录工具模块 — 格式化工具。"""


def format_address(ea):
    """将整数地址格式化为十六进制字符串。"""
    return f"0x{ea:X}"


def format_size(size):
    """将大小格式化为可读字符串。"""
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def format_function_info(name, address, size):
    """格式化函数信息。"""
    return {
        "display": f"{name} @ {format_address(address)} ({format_size(size)})",
        "name": name,
        "address": format_address(address),
        "size_display": format_size(size),
    }
