"""
红蓝眼谜题核心逻辑

实现村民的推理过程和离开规则
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .reasoning import PerfectInductionPolicy, ReasoningPolicy


class EyeColor(Enum):
    """眼睛颜色"""
    RED = "红色"
    BLUE = "蓝色"


@dataclass
class Villager:
    """村民类"""
    
    id: int
    eye_color: EyeColor
    name: Optional[str] = None

    # 村民“类型/大脑”：用于切换不同推理机制（例如：假人/LLM）
    villager_type: str = "dummy"
    
    # 这个村民看到的红眼睛数量
    observed_red_eyes: int = 0
    
    # 是否已经离开村庄
    has_left: bool = False
    
    # 离开的日期（从游客宣布之后开始计算）
    left_on_day: Optional[int] = None
    
    # 推理日志
    reasoning_log: list[str] = field(default_factory=list)

    # 可观察到的“群体行为”上下文（用于更真实的推理/社会行为模拟）
    # - 昨天离开的人数（全村公开可见）
    observed_left_yesterday: int = 0
    # - 累计离开的人数（全村公开可见）
    observed_left_total: int = 0
    
    def __post_init__(self):
        if self.name is None:
            self.name = f"村民{self.id}"
    
    def __repr__(self) -> str:
        return f"{self.name}({self.eye_color.value}眼睛)"
    
    def observe(self, others: list['Villager']) -> None:
        """观察其他村民，统计看到的红眼睛数量"""
        self.observed_red_eyes = sum(
            1 for v in others 
            if v.id != self.id and v.eye_color == EyeColor.RED and not v.has_left
        )
    
    def reason_and_decide(self, day: int, public_announcement_made: bool) -> bool:
        """
        进行推理并决定是否离开
        
        🔑 核心逻辑解释：
        
        "第N天离开"不是预设规则，而是通过归纳推理得出的！
        
        归纳基础 (n=1):
            如果我看到0个红眼睛，游客说至少有1个，那我就是那个红眼睛
            → 第1天离开（直接从规则推出）
        
        归纳步骤 (n=k → n=k+1):
            如果我看到k个红眼睛，我假设"如果我是蓝眼睛，那就只有k个红眼睛"
            根据归纳假设，k个红眼睛应该在第k天离开
            如果第k天没人离开，说明我的假设错误，我也是红眼睛
            → 第k+1天离开
        
        Args:
            day: 当前是第几天（从公开宣布后开始）
            public_announcement_made: 是否已经公开宣布过
        
        Returns:
            是否决定离开
        """
        if self.has_left:
            return False
        
        if not public_announcement_made:
            self.reasoning_log.append(
                f"第{day}天: 没有公开宣布。我仍会尝试推理，但缺少‘至少一人红眼’的公共知识基准，"
                f"归纳链条无法闭合，所以无法确定自己是否该离开"
            )
            return False
        
        if self.eye_color == EyeColor.BLUE:
            # 蓝眼睛的推理
            self.reasoning_log.append(
                f"第{day}天: 我看到 {self.observed_red_eyes} 个红眼睛，"
                f"我不是红眼睛，所以不需要离开"
            )
            return False
        
        # 红眼睛的推理过程
        # 关键：每个红眼睛都在脑中模拟"如果只有k个红眼睛会怎样"
        
        if self.observed_red_eyes == 0:
            # 归纳基础：n=1 的情况（唯一直接从规则推出的）
            if day == 1:
                self.reasoning_log.append(
                    f"第{day}天: [归纳基础] 我看到 0 个红眼睛，但游客说至少有一个，"
                    f"所以我一定是红眼睛！我必须离开。"
                )
                return True
        else:
            # 归纳步骤：n=k+1 的情况
            # 我看到 k 个红眼睛，我假设"如果我是蓝眼睛，那就只有 k 个红眼睛"
            # 根据归纳假设，k 个红眼睛会在第 k 天离开
            k = self.observed_red_eyes
            expected_leave_day_if_only_k = k  # 根据归纳假设推导
            my_leave_day = k + 1  # 如果第 k 天没人离开，说明我也是红眼睛
            
            if day < my_leave_day:
                self.reasoning_log.append(
                    f"第{day}天: [归纳推理] 我看到 {k} 个红眼睛。"
                    f"假设我是蓝眼睛，那就只有 {k} 个红眼睛。"
                    f"根据归纳假设，{k} 个红眼睛会在第 {k} 天离开。"
                    f"现在才第 {day} 天，我继续等待观察..."
                )
                return False
            elif day == my_leave_day:
                self.reasoning_log.append(
                    f"第{day}天: [归纳推理完成] 我看到的 {k} 个红眼睛昨天没有离开！"
                    f"如果只有他们 {k} 个是红眼睛，根据归纳假设他们应该在第 {k} 天离开。"
                    f"他们没离开，说明我的假设'我是蓝眼睛'错误！"
                    f"唯一的可能是：我也是红眼睛！我必须离开。"
                )
                return True
        
        return False
    
    def leave(self, day: int) -> None:
        """离开村庄"""
        self.has_left = True
        self.left_on_day = day


@dataclass
class Village:
    """村庄类"""
    
    villagers: list[Villager] = field(default_factory=list)

    # 推理策略（用于测试“村民是否聪明/能推理到什么程度”）
    reasoning_policy: ReasoningPolicy = field(default_factory=PerfectInductionPolicy)
    
    # 游客是否已经公开宣布
    # 🔑 这是核心问题1的答案：这个变量从 False 变 True 是唯一的表面变化
    announcement_made: bool = False
    
    # 当前天数
    # 🔑 宣布后这个变量才开始有意义 —— 建立公共时间起点
    current_day: int = 0
    
    # 公共知识层级 (-1 表示无限阶，即公共知识)
    # 🔑 宣布前是有限阶，宣布后变为无限阶
    knowledge_level: int = 0
    
    # 每天的事件日志
    daily_log: list[str] = field(default_factory=list)

    # 用于给村民提供“昨天离开人数”的可观察上下文
    left_yesterday_count: int = 0
    
    def add_villager(
        self,
        eye_color: EyeColor,
        name: Optional[str] = None,
        villager_type: str = "dummy",
    ) -> Villager:
        """添加村民"""
        villager = Villager(
            id=len(self.villagers) + 1,
            eye_color=eye_color,
            name=name,
            villager_type=villager_type,
        )
        self.villagers.append(villager)
        return villager
    
    def initialize_observations(self) -> None:
        """初始化所有村民的观察"""
        for villager in self.villagers:
            villager.observe(self.villagers)
    
    def make_announcement(self) -> str:
        """
        游客公开宣布
        
        🔑 核心问题1的答案：这个函数展示了宣布带来的所有变量变化
        """
        # 变化1: 布尔标志位
        self.announcement_made = True
        
        # 变化2: 知识层级从有限阶变为无限阶 (-1 表示公共知识)
        # 这是最关键的变化！使得递归推理成为可能
        self.knowledge_level = -1
        
        message = "🎤 游客公开宣布: '村庄里至少有一个红眼睛的人！'"
        self.daily_log.append(message)
        self.daily_log.append("💡 关键变化: announcement_made = True")
        self.daily_log.append("💡 关键变化: knowledge_level = -1 (公共知识，无限阶)")
        self.daily_log.append("💡 关键变化: current_day 开始有意义的计时")
        return message
    
    def simulate_day(self) -> list[Villager]:
        """
        模拟一天的过程
        
        Returns:
            当天离开的村民列表
        """
        self.current_day += 1
        self.daily_log.append(f"\n=== 第 {self.current_day} 天 ===")
        
        # 更新观察（可能有人离开后情况变化）
        for villager in self.villagers:
            if not villager.has_left:
                villager.observe(self.villagers)

        # 更新可观察群体信息（昨日离开数/累计离开数）
        total_left_now = sum(1 for v in self.villagers if v.has_left)
        for villager in self.villagers:
            if villager.has_left:
                continue
            villager.observed_left_yesterday = self.left_yesterday_count
            villager.observed_left_total = total_left_now
        
        # 所有村民同时进行推理
        leaving_today = []
        for villager in self.villagers:
            if not villager.has_left:
                should_leave = self.reasoning_policy.decide(
                    villager,
                    self.current_day,
                    self.announcement_made,
                )
                if should_leave:
                    leaving_today.append(villager)
        
        # 记录离开的村民
        for villager in leaving_today:
            villager.leave(self.current_day)
            self.daily_log.append(f"  🚶 {villager} 离开了村庄")
        
        if not leaving_today:
            self.daily_log.append(f"  😴 今天没有人离开")

        # 为下一天准备“昨日离开人数”
        self.left_yesterday_count = len(leaving_today)
        
        return leaving_today
    
    def get_remaining_villagers(self) -> list[Villager]:
        """获取还在村庄里的村民"""
        return [v for v in self.villagers if not v.has_left]
    
    def get_red_eye_count(self) -> int:
        """获取红眼睛村民的总数"""
        return sum(1 for v in self.villagers if v.eye_color == EyeColor.RED)
    
    def get_blue_eye_count(self) -> int:
        """获取蓝眼睛村民的总数"""
        return sum(1 for v in self.villagers if v.eye_color == EyeColor.BLUE)
    
    def print_status(self) -> str:
        """打印当前状态"""
        lines = [
            f"\n📊 村庄状态 (第{self.current_day}天)",
            f"  红眼睛: {self.get_red_eye_count()} 人",
            f"  蓝眼睛: {self.get_blue_eye_count()} 人",
            f"  已离开: {sum(1 for v in self.villagers if v.has_left)} 人",
            f"  剩余: {len(self.get_remaining_villagers())} 人",
        ]
        return "\n".join(lines)
