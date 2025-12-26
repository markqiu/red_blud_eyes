"""
知识层级模型 (Epistemic Logic)

实现公共知识理论中的知识层级概念：
- 零阶知识 p₀: 命题本身
- n阶知识 pₙ: E(pₙ₋₁) = "所有人都知道 pₙ₋₁"
- 公共知识: 无限阶知识
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KnowledgeState:
    """知识状态：表示一个人对某个命题的知识层级"""
    
    # 这个人知道命题 p₀ (存在红眼睛) 吗？
    knows_p0: bool = False
    
    # 这个人确定的知识层级（能确定到第几阶）
    # 例如: knowledge_level = 2 表示这个人知道 "所有人都知道所有人都知道 p₀"
    knowledge_level: int = 0
    
    # 这个人能看到的红眼睛数量
    observed_red_eyes: int = 0
    
    def __repr__(self) -> str:
        return f"KnowledgeState(knows_p0={self.knows_p0}, level={self.knowledge_level}, observed={self.observed_red_eyes})"


@dataclass
class CommonKnowledge:
    """
    公共知识模型
    
    公共知识的定义：
    - p 成立
    - E(p) 成立（所有人知道 p）
    - E(E(p)) 成立（所有人知道所有人知道 p）
    - ... 无限嵌套
    """
    
    # 命题内容
    proposition: str
    
    # 是否已成为公共知识
    is_common: bool = False
    
    # 当前达到的知识层级（公共知识为无限，用 -1 表示）
    level: int = 0
    
    def announce(self) -> None:
        """公开宣布，使命题成为公共知识"""
        self.is_common = True
        self.level = -1  # -1 表示无限层级
    
    def get_level_description(self) -> str:
        """获取知识层级的描述"""
        if self.level == -1:
            return "公共知识（无限阶）"
        elif self.level == 0:
            return "零阶知识：命题本身"
        elif self.level == 1:
            return "一阶知识：所有人都知道命题"
        else:
            return f"{self.level}阶知识：嵌套{self.level}层'所有人都知道'"


def calculate_max_knowledge_level(num_red_eyes: int, observer_sees: int) -> int:
    """
    计算一个观察者能达到的最大知识层级
    
    关键定理：如果村庄里有 n 个红眼睛，
    一个能看到 k 个红眼睛的人最多能确定 k-1 阶知识
    
    Args:
        num_red_eyes: 实际的红眼睛数量
        observer_sees: 观察者能看到的红眼睛数量
    
    Returns:
        该观察者能确定的最大知识层级
    """
    if observer_sees == 0:
        return -1  # 如果看不到红眼睛，无法确定任何知识
    return observer_sees - 1


def build_nested_knowledge_string(level: int) -> str:
    """
    构建嵌套知识的字符串表示
    
    例如：
    - level=0: "存在红眼睛"
    - level=1: "所有人都知道存在红眼睛"
    - level=2: "所有人都知道(所有人都知道存在红眼睛)"
    """
    base = "存在红眼睛"
    if level == 0:
        return base
    
    result = base
    for _ in range(level):
        result = f"所有人都知道({result})"
    return result
