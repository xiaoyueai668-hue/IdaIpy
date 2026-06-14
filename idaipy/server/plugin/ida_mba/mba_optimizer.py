# -*- coding: utf-8 -*-
"""
MBA Optimizer Framework - 微码优化器封装框架

提供简单的规则接口，自动处理钩子注册，支持 maturity 级别过滤。
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class Maturity:
    """微码成熟度级别，对应 ida_hexrays MMAT_*"""
    ZERO = 0
    GENERATED = 1
    PREOPTIMIZED = 2
    LOOP = 3
    LOCOPT = 4
    CALLS = 5
    GLBOPT1 = 6
    GLBOPT2 = 7
    GLBOPT3 = 8
    HIGH = 9


class InstructionRule:
    """指令优化规则基类。子类只需实现 optimize() 方法。"""
    MATURITIES = [Maturity.LOCOPT, Maturity.GLBOPT1]

    def optimize(self, blk, ins) -> bool:
        """优化指令，返回 True 表示进行了修改。"""
        raise NotImplementedError


class BlockRule:
    """块优化规则基类。子类只需实现 optimize() 方法。"""
    MATURITIES = [Maturity.CALLS, Maturity.GLBOPT1, Maturity.GLBOPT2]

    def optimize(self, blk) -> int:
        """优化块，返回修改数量。"""
        raise NotImplementedError


class _OptimizerManagerBase:
    """优化管理器基类，处理通用的规则生命周期。"""

    _hook_class = None  # 子类设置: optinsn_t 或 optblock_t

    def __init__(self):
        self._rules: List[tuple] = []  # (rule, maturities)
        self._installed = False

    def add_rule(self, rule, maturities: Optional[List[int]] = None):
        """添加规则。"""
        if maturities is None:
            maturities = rule.MATURITIES
        self._rules.append((rule, maturities))
        logger.debug(f"Added {rule.__class__.__name__}, maturities={maturities}")

    def remove(self):
        """移除所有规则。"""
        self._rules.clear()
        if self._installed:
            self.unhook()
            self._installed = False

    def hook(self):
        """安装钩子。"""
        if not self._installed:
            try:
                super().hook()
                self._installed = True
            except Exception:
                pass

    def unhook(self):
        """卸载钩子。"""
        if self._installed:
            try:
                super().unhook()
            except Exception:
                pass
            self._installed = False

    def _process_rules(self, blk):
        """遍历规则，返回是否进行了修改。子类实现具体调用逻辑。"""
        raise NotImplementedError

    def func(self, blk, ins=None):
        """IDA 调用的优化函数。"""
        if not self._rules:
            return False
        mba = blk.mba
        current_maturity = mba.maturity if mba else 0
        for rule, maturities in self._rules:
            if current_maturity not in maturities:
                continue
            try:
                if self._process_rule(rule, blk, ins):
                    return True
            except Exception as e:
                logger.error(f"Error in {rule.__class__.__name__}: {e}")
        return False

    def _process_rule(self, rule, blk, ins):
        """处理单条规则，子类实现。"""
        raise NotImplementedError


class InstructionOptimizerManager(_OptimizerManagerBase):
    """指令优化管理器，内部使用 optinsn_t 钩子。"""

    def __init__(self):
        from ida_hexrays import optinsn_t
        super().__init__()

    def _process_rule(self, rule, blk, ins):
        return rule.optimize(blk, ins)


class BlockOptimizerManager(_OptimizerManagerBase):
    """块优化管理器，内部使用 optblock_t 钩子。"""

    def __init__(self):
        from ida_hexrays import optblock_t
        super().__init__()

    def _process_rule(self, rule, blk, ins):
        return rule.optimize(blk) > 0


class MbaOptimizerManager:
    """微码优化管理器，整合指令和块优化管理器。"""

    def __init__(self):
        self.ins_manager = InstructionOptimizerManager()
        self.blk_manager = BlockOptimizerManager()

    def add_ins_rule(self, rule: InstructionRule,
                      maturities: Optional[List[int]] = None):
        self.ins_manager.add_rule(rule, maturities)

    def add_blk_rule(self, rule: BlockRule,
                      maturities: Optional[List[int]] = None):
        self.blk_manager.add_rule(rule, maturities)

    def install(self):
        """安装钩子。"""
        self.ins_manager.hook()
        self.blk_manager.hook()
        logger.info("MbaOptimizerManager installed")

    def remove(self):
        """卸载钩子。"""
        self.ins_manager.remove()
        self.blk_manager.remove()
        logger.info("MbaOptimizerManager removed")
