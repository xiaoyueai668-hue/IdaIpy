"""依赖 helper 模块和 utils 子包的分析器。"""

from test_modules.helper import count_functions, list_segments, get_first_function
from test_modules.utils.formatter import format_address, format_size, format_function_info


def run_analysis():
    """执行分析。依赖 helper + utils.formatter 两层模块。"""
    func_count = count_functions()
    segments = list_segments()
    first_func = get_first_function()

    first_formatted = format_function_info(
        first_func["name"],
        int(first_func["address"], 16),
        first_func.get("size", 0),
    )

    return {
        "func_count": func_count,
        "segment_count": len(segments),
        "segments": segments,
        "first_function": first_func,
        "first_formatted": first_formatted,
        "status": "ok",
    }
