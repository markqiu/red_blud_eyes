"""
红蓝眼谜题单元测试

验证核心逻辑的正确性
"""

import pytest
from src.puzzle import Village, Villager, EyeColor
from src.knowledge import (
    KnowledgeState,
    CommonKnowledge,
    calculate_max_knowledge_level,
    build_nested_knowledge_string,
)
from src.simulation import create_village, run_simulation
from src.reasoning import NoReasoningPolicy, BoundedInductionPolicy, MaxDayReasoningPolicy, FalliblePolicy


class TestVillager:
    """测试村民类"""
    
    def test_villager_creation(self):
        """测试村民创建"""
        v = Villager(id=1, eye_color=EyeColor.RED, name="测试")
        assert v.id == 1
        assert v.eye_color == EyeColor.RED
        assert v.name == "测试"
        assert not v.has_left
    
    def test_villager_observation(self):
        """测试村民观察"""
        v1 = Villager(id=1, eye_color=EyeColor.RED)
        v2 = Villager(id=2, eye_color=EyeColor.RED)
        v3 = Villager(id=3, eye_color=EyeColor.BLUE)
        
        villagers = [v1, v2, v3]
        v1.observe(villagers)
        
        # v1（红眼睛）应该看到1个红眼睛（v2）
        assert v1.observed_red_eyes == 1
    
    def test_villager_leave(self):
        """测试村民离开"""
        v = Villager(id=1, eye_color=EyeColor.RED)
        v.leave(day=3)
        
        assert v.has_left
        assert v.left_on_day == 3


class TestVillage:
    """测试村庄类"""
    
    def test_village_creation(self):
        """测试村庄创建"""
        village = Village()
        village.add_villager(EyeColor.RED, "红1")
        village.add_villager(EyeColor.BLUE, "蓝1")
        
        assert len(village.villagers) == 2
        assert village.get_red_eye_count() == 1
        assert village.get_blue_eye_count() == 1
    
    def test_announcement(self):
        """测试公开宣布"""
        village = Village()
        assert not village.announcement_made
        
        village.make_announcement()
        assert village.announcement_made


class TestKnowledge:
    """测试知识模型"""
    
    def test_common_knowledge_creation(self):
        """测试公共知识创建"""
        ck = CommonKnowledge(proposition="存在红眼睛")
        assert not ck.is_common
        assert ck.level == 0
    
    def test_common_knowledge_announce(self):
        """测试公共知识宣布"""
        ck = CommonKnowledge(proposition="存在红眼睛")
        ck.announce()
        
        assert ck.is_common
        assert ck.level == -1  # 无限阶
    
    def test_max_knowledge_level(self):
        """测试最大知识层级计算"""
        # 看到0个红眼睛，无法确定任何知识
        assert calculate_max_knowledge_level(1, 0) == -1
        
        # 看到1个红眼睛，能确定0阶知识
        assert calculate_max_knowledge_level(2, 1) == 0
        
        # 看到2个红眼睛，能确定1阶知识
        assert calculate_max_knowledge_level(3, 2) == 1
        
        # 看到5个红眼睛，能确定4阶知识
        assert calculate_max_knowledge_level(6, 5) == 4
    
    def test_nested_knowledge_string(self):
        """测试嵌套知识字符串"""
        assert build_nested_knowledge_string(0) == "存在红眼睛"
        assert "所有人都知道" in build_nested_knowledge_string(1)
        assert build_nested_knowledge_string(2).count("所有人都知道") == 2


class TestSimulation:
    """测试模拟器"""
    
    def test_create_village(self):
        """测试村庄创建函数"""
        village = create_village(num_red=3, num_blue=2)
        
        assert len(village.villagers) == 5
        assert village.get_red_eye_count() == 3
        assert village.get_blue_eye_count() == 2
    
    @pytest.mark.parametrize("num_red,num_blue,expected_day", [
        (1, 0, 1),   # 1个红眼睛，第1天离开
        (1, 3, 1),   # 1个红眼睛，3个蓝眼睛，第1天离开
        (2, 0, 2),   # 2个红眼睛，第2天离开
        (2, 2, 2),   # 2个红眼睛，2个蓝眼睛，第2天离开
        (3, 0, 3),   # 3个红眼睛，第3天离开
        (3, 2, 3),   # 3个红眼睛，2个蓝眼睛，第3天离开
        (5, 3, 5),   # 5个红眼睛，3个蓝眼睛，第5天离开
        (10, 5, 10), # 10个红眼睛，5个蓝眼睛，第10天离开
    ])
    def test_simulation_correct_day(self, num_red, num_blue, expected_day):
        """
        测试：n个红眼睛应该在第n天离开
        
        这是红蓝眼谜题的核心定理
        """
        result = run_simulation(num_red, num_blue, verbose=False)
        
        assert result["days_to_leave"] == expected_day, \
            f"预期第{expected_day}天离开，实际第{result['days_to_leave']}天"
        assert result["all_red_left"], "并非所有红眼睛都离开了"
    
    def test_no_red_eyes(self):
        """测试没有红眼睛的情况"""
        result = run_simulation(0, 5, verbose=False)
        
        assert result["days_to_leave"] == 0
        assert not result["all_red_left"]  # 没有红眼睛需要离开

    def test_no_announcement_no_one_leaves(self):
        """
        测试：没有游客宣布时，即使存在红眼睛，也不会有人离开。

        直觉：没有宣布就没有公共知识的“计时起点”，归纳链条无法启动。
        """
        result = run_simulation(3, 2, verbose=False, announce=False)

        assert result["days_to_leave"] == 0
        assert not result["all_red_left"]

    def test_not_smart_no_one_leaves_even_with_announcement(self):
        """测试：村民不够聪明（不会推理）时，即使有宣布也不会有人离开。"""
        result = run_simulation(3, 2, verbose=False, announce=True, reasoning_policy=NoReasoningPolicy())

        assert result["days_to_leave"] == 0
        assert not result["all_red_left"]

    def test_bounded_reasoning_only_works_for_small_n(self):
        """
        测试：有限归纳推理。

        max_k=1: 能推到 n=2，但推不到 n=3。
        - 当红眼睛数=2 时应在第2天离开
        - 当红眼睛数=3 时不应有人离开
        """
        policy = BoundedInductionPolicy(max_k=1)

        ok = run_simulation(2, 2, verbose=False, announce=True, reasoning_policy=policy)
        assert ok["days_to_leave"] == 2
        assert ok["all_red_left"]

        fail = run_simulation(3, 2, verbose=False, announce=True, reasoning_policy=policy)
        assert fail["days_to_leave"] == 0
        assert not fail["all_red_left"]

    def test_max_day_reasoning_cuts_off_chain(self):
        """
        测试：只能推理到第 D 天。

        - D=2 时：n=2 能在第2天离开
        - D=2 时：n=3 需要第3天才能推出，因能力限制不会离开
        """
        policy = MaxDayReasoningPolicy(max_day=2)

        ok = run_simulation(2, 2, verbose=False, announce=True, reasoning_policy=policy)
        assert ok["days_to_leave"] == 2
        assert ok["all_red_left"]

        fail = run_simulation(3, 2, verbose=False, announce=True, reasoning_policy=policy)
        assert fail["days_to_leave"] == 0
        assert not fail["all_red_left"]

    def test_fallible_policy_zero_rate_equals_perfect(self):
        """测试：犯错率为 0 时应等价于完美推理。"""
        policy = FalliblePolicy(mistake_rate=0.0, seed=123)
        result = run_simulation(4, 3, verbose=False, announce=True, reasoning_policy=policy)

        assert result["days_to_leave"] == 4
        assert result["all_red_left"]

    def test_fallible_policy_always_mistakes_no_one_leaves(self):
        """测试：犯错率为 1 时，红眼睛永远不会执行离开（漏走），从而无人离开。"""
        policy = FalliblePolicy(mistake_rate=1.0, seed=123)
        result = run_simulation(2, 2, verbose=False, announce=True, reasoning_policy=policy)

        assert result["days_to_leave"] == 0
        assert not result["all_red_left"]
    
    def test_all_red_leave_same_day(self):
        """测试所有红眼睛在同一天离开"""
        result = run_simulation(4, 3, verbose=False)
        
        # 所有离开的村民应该在同一天离开
        left_days = [v["day"] for v in result["left_villagers"]]
        assert len(set(left_days)) == 1, "红眼睛不是同一天离开的"
        assert left_days[0] == 4
    
    def test_blue_eyes_stay(self):
        """测试蓝眼睛不会离开"""
        village = create_village(num_red=3, num_blue=2)
        village.make_announcement()
        
        # 模拟足够多的天数
        for _ in range(10):
            village.simulate_day()
        
        # 检查蓝眼睛是否还在
        for v in village.villagers:
            if v.eye_color == EyeColor.BLUE:
                assert not v.has_left, f"{v} 不应该离开"


class TestEdgeCases:
    """边界情况测试"""
    
    def test_single_red_eye(self):
        """测试只有一个红眼睛的情况"""
        result = run_simulation(1, 5, verbose=False)
        
        assert result["days_to_leave"] == 1
        assert len(result["left_villagers"]) == 1
    
    def test_all_red_eyes(self):
        """测试全是红眼睛的情况"""
        result = run_simulation(5, 0, verbose=False)
        
        assert result["days_to_leave"] == 5
        assert len(result["left_villagers"]) == 5
    
    def test_many_red_eyes(self):
        """测试大量红眼睛的情况"""
        result = run_simulation(20, 10, verbose=False)
        
        assert result["days_to_leave"] == 20
        assert result["all_red_left"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
