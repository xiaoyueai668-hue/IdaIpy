# -*- coding: utf-8 -*-
"""
ida_mba - IDA Microcode Optimization Framework

MBA (Microcode Architecture) 优化和反混淆框架。
"""

# 全局 manager 实例，供外部访问
_manager = None


def set_manager(manager):
    """设置全局 manager 实例（由 plugin.py 调用）"""
    global _manager
    _manager = manager


def get_manager():
    """获取全局 manager 实例"""
    return _manager
