"""
红蓝眼谜题模拟器

运行完整的模拟过程，验证推理逻辑
"""

from .puzzle import Village, EyeColor, Villager
from .knowledge import CommonKnowledge, build_nested_knowledge_string
from .reasoning import PerfectInductionPolicy, ReasoningPolicy


def create_village(
    num_red: int,
    num_blue: int,
    reasoning_policy: ReasoningPolicy | None = None,
    villager_type: str = "dummy",
    villager_types: list[str] | None = None,
) -> Village:
    """
    创建一个有指定数量红眼睛和蓝眼睛村民的村庄
    
    Args:
        num_red: 红眼睛村民数量
        num_blue: 蓝眼睛村民数量
    
    Returns:
        初始化好的村庄
    """
    village = Village(reasoning_policy=reasoning_policy or PerfectInductionPolicy())

    total = num_red + num_blue
    if villager_types is not None and len(villager_types) != total:
        raise ValueError(f"villager_types length must be {total}, got {len(villager_types)}")
    idx = 0
    
    # 添加红眼睛村民
    for i in range(num_red):
        t = villager_types[idx] if villager_types is not None else villager_type
        village.add_villager(EyeColor.RED, name=f"红{i+1}", villager_type=t)
        idx += 1
    
    # 添加蓝眼睛村民
    for i in range(num_blue):
        t = villager_types[idx] if villager_types is not None else villager_type
        village.add_villager(EyeColor.BLUE, name=f"蓝{i+1}", villager_type=t)
        idx += 1
    
    # 初始化观察
    village.initialize_observations()
    
    return village


def run_simulation(
    num_red: int,
    num_blue: int,
    verbose: bool = True,
    announce: bool = True,
    reasoning_policy: ReasoningPolicy | None = None,
    villager_type: str = "dummy",
    villager_types: list[str] | None = None,
) -> dict:
    """
    运行完整的模拟
    
    Args:
        num_red: 红眼睛数量
        num_blue: 蓝眼睛数量
        verbose: 是否输出详细信息
        announce: 是否进行游客公开宣布（默认 True）
    
    Returns:
        模拟结果字典
    """
    if verbose:
        print("=" * 60)
        print("🏘️  红蓝眼谜题模拟器")
        print("=" * 60)
        print(f"\n设置: {num_red} 个红眼睛, {num_blue} 个蓝眼睛")
    
    village = create_village(
        num_red,
        num_blue,
        reasoning_policy=reasoning_policy,
        villager_type=villager_type,
        villager_types=villager_types,
    )
    
    # 展示初始状态
    if verbose:
        print("\n📋 初始状态:")
        for v in village.villagers:
            print(f"  {v} - 看到 {v.observed_red_eyes} 个红眼睛")
    
    # 分析知识层级（宣布之前）
    if verbose:
        print("\n" + "-" * 40)
        print("📚 知识层级分析（宣布前）")
        print("-" * 40)
        
        knowledge = CommonKnowledge(proposition="村庄里存在红眼睛")
        
        if num_red >= 2:
            # 所有人都能看到红眼睛
            print(f"  ✅ p₀ = '{knowledge.proposition}' 被所有人知道")
            max_level = num_red - 1
            print(f"  📊 当前最大知识层级: {max_level} 阶")
            print(f"     {build_nested_knowledge_string(max_level)}")
            print(f"  ❌ 无法达到 {max_level + 1} 阶，因为红眼睛只能看到 {num_red - 1} 个红眼睛")
        elif num_red == 1:
            print(f"  ⚠️ p₀ 不被唯一的红眼睛知道（他看不到任何红眼睛）")
        else:
            print(f"  ❌ 没有红眼睛，p₀ 不成立")
    
    # 游客宣布（可选）
    if announce:
        if verbose:
            print("\n" + "-" * 40)
        announcement = village.make_announcement()
        if verbose:
            print(announcement)
            print("-" * 40)
            print("💡 公共知识形成: p₀ 瞬间达到无限阶!")
    else:
        if verbose:
            print("\n" + "-" * 40)
            print(
                "🚫 无游客宣布：大家仍会思考，但缺少‘至少一人红眼’的公共知识基准，归纳链条无法闭合"
            )
            print("-" * 40)
    
    # 开始每日模拟
    max_days = (num_red + 5) if announce else max(10, num_red + 10)  # 无宣布时用更显著的演示上限
    results = {
        "num_red": num_red,
        "num_blue": num_blue,
        "days_to_leave": 0,
        "all_red_left": False,
        "left_villagers": [],
        "daily_events": []
    }
    
    for day in range(1, max_days + 1):
        prev_log_len = len(village.daily_log)
        left_today = village.simulate_day()
        
        results["daily_events"].append({
            "day": day,
            "left": [str(v) for v in left_today]
        })
        
        if verbose:
            for log_entry in village.daily_log[prev_log_len:]:
                print(log_entry)
        
        # 检查是否所有红眼睛都离开了
        remaining_red = sum(
            1 for v in village.villagers 
            if v.eye_color == EyeColor.RED and not v.has_left
        )
        
        if remaining_red == 0 and num_red > 0:
            results["days_to_leave"] = day
            results["all_red_left"] = True
            results["left_villagers"] = [
                {"name": str(v), "day": v.left_on_day}
                for v in village.villagers if v.has_left
            ]
            break
    
    # 验证结果
    if verbose:
        print("\n" + "=" * 60)
        print("📊 结果")
        print("=" * 60)
        
        expected_day = num_red if num_red > 0 else 0
        actual_day = results["days_to_leave"]
        
        # 如果村民并非全体“假人/完美归纳”，这里更多是“观察结果”而非标准验证。
        is_exploratory = any(getattr(v, "villager_type", "dummy") != "dummy" for v in village.villagers)

        if num_red == 0:
            print("  ℹ️ 没有红眼睛，没有人需要离开")
            print("  ✅ 验证通过!")
        elif not announce:
            print("  ℹ️ 未进行游客宣布：大家仍会思考，但归纳链条无法闭合")
            print("     预期现象：无论有多少红眼睛，都不会有人离开")
            print("  ✅ 演示通过!")
        elif is_exploratory:
            print("  ℹ️ 使用了非标准/更真实的村民类型（例如 OpenAI）：不做‘第 N 天游离开’硬性验证")
            if results["all_red_left"]:
                print(f"     观察到：所有红眼睛在第 {results['days_to_leave']} 天离开")
            else:
                print("     观察到：并未在演示上限内全部离开（这在真实/有限理性模型中是可能的）")
        elif actual_day == expected_day:
            print(f"  ✅ 验证通过!")
            print(f"     预期: 所有 {num_red} 个红眼睛在第 {expected_day} 天离开")
            print(f"     实际: 所有 {num_red} 个红眼睛在第 {actual_day} 天离开")
        else:
            print(f"  ❌ 验证失败!")
            print(f"     预期: 第 {expected_day} 天")
            print(f"     实际: 第 {actual_day} 天")
        
        # 打印详细推理过程
        print("\n" + "-" * 40)
        print("🧠 红眼睛村民的推理过程:")
        print("-" * 40)
        for v in village.villagers:
            if v.eye_color == EyeColor.RED:
                print(f"\n  【{v}】")
                for log in v.reasoning_log:
                    print(f"    {log}")
    
    return results


def explain_puzzle():
    """打印谜题的详细解释"""
    explanation = """
╔══════════════════════════════════════════════════════════════════╗
║                     红蓝眼谜题详解                                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  【设定】                                                         ║
║  - 村庄里有一些红眼睛的人和蓝眼睛的人                             ║
║  - 每个人能看到所有其他人的眼睛颜色，但不知道自己的               ║
║  - 村民不能直接交流眼睛颜色的信息                                 ║
║  - 如果确定知道自己是红眼睛，必须当天晚上离开                     ║
║  - 所有人都是完美的逻辑推理者                                     ║
║                                                                   ║
║  【谜题】                                                         ║
║  一位游客公开说："村庄里至少有一个红眼睛的人。"                   ║
║  为什么这句话（看似人尽皆知）会导致所有红眼睛的人离开？           ║
║                                                                   ║
║  【解答核心：公共知识 vs 共有知识】                               ║
║                                                                   ║
║  共有知识: 每个人都知道某个命题                                   ║
║  公共知识: 每个人都知道每个人都知道每个人都知道...（无限嵌套）    ║
║                                                                   ║
║  游客的宣布使"存在红眼睛"从有限阶知识变成公共知识（无限阶）       ║
║  这就是关键的变化！                                               ║
║                                                                   ║
║  【推理过程（归纳链条）】                                         ║
║                                                                   ║
║  n=1: 唯一的红眼睛看到0个，游客说至少有1个 → 我是红眼睛 → 第1天离开 ║
║       ↓ (这是唯一直接从规则推出的！)                              ║
║  n=2: 每人看到1个红眼睛，假设"如果我是蓝眼睛，那只有1个红眼睛"     ║
║       根据n=1的结论，那个人应该第1天离开                           ║
║       第1天没人离开 → 我的假设错了 → 我也是红眼睛 → 第2天离开       ║
║       ↓                                                          ║
║  n=3: 每人看到2个红眼睛，假设"如果我是蓝眼睛，那只有2个红眼睛"     ║
║       根据n=2的结论，那2个人应该第2天离开                           ║
║       第2天没人离开 → 我的假设错了 → 我也是红眼睛 → 第3天离开       ║
║       ↓                                                          ║
║  ...以此类推                                                      ║
║                                                                   ║
║  所以：假如有 N 个红眼睛，那么红眼睛们就应该在第 N 天离开。        ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(explanation)


def main():
    """主程序入口"""
    explain_puzzle()
    
    # 测试不同场景
    test_cases = [
        (1, 3),  # 1个红眼睛，3个蓝眼睛
        (2, 2),  # 2个红眼睛，2个蓝眼睛
        (3, 2),  # 3个红眼睛，2个蓝眼睛
        (5, 3),  # 5个红眼睛，3个蓝眼睛
    ]
    
    print("\n" + "🧪 " * 20)
    print("\n开始运行测试用例...\n")
    
    all_passed = True
    for num_red, num_blue in test_cases:
        result = run_simulation(num_red, num_blue, verbose=True)
        
        expected = num_red if num_red > 0 else 0
        if result["days_to_leave"] != expected:
            all_passed = False
        
        print("\n" + "━" * 60 + "\n")
    
    # 总结
    print("=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试用例通过！")
        print("\n💡 结论：n 个红眼睛的村民会在第 n 天同时离开")
    else:
        print("❌ 有测试用例失败")
    
    return all_passed


if __name__ == "__main__":
    main()
