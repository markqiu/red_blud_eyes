"""推理策略（Reasoning Policies）

把“村民是否聪明/能推理到什么程度”做成可替换策略，便于做成测试系统。

核心目标：
- 同一套世界规则下，通过更换推理策略（policy）来测试不同假设：
  1) 没有游客宣布会怎样？
  2) 村民不够聪明（推不出来）会怎样？
  3) 村民只能推理有限深度会怎样？

注意：这里的“聪明程度”只影响推理能力，不改变世界规则。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from random import Random
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import TYPE_CHECKING, Literal, Protocol

from .env import load_dotenv

if TYPE_CHECKING:  # pragma: no cover
    from .puzzle import Villager


def _is_blue(villager: "Villager") -> bool:
    # Works for Enum (EyeColor.BLUE.name == 'BLUE') and is resilient to value changes.
    return getattr(getattr(villager, "eye_color", None), "name", None) == "BLUE"


def _perfect_induction_decide_no_log(
    villager: "Villager", day: int, public_announcement_made: bool
) -> bool:
    """Perfect induction decision without mutating villager.reasoning_log.

    This mirrors PerfectInductionPolicy.decide()'s decision logic, but avoids
    writing logs so it can be used for enforcement/correction.
    """

    if villager.has_left:
        return False

    if not public_announcement_made:
        return False

    if _is_blue(villager):
        return False

    # Red-eyes: base + inductive step
    if villager.observed_red_eyes == 0:
        return day == 1

    k = villager.observed_red_eyes
    my_leave_day = k + 1
    return day == my_leave_day


def _standard_proof_public_summary(
    villager: "Villager", day: int, public_announcement_made: bool
) -> tuple[bool, float, str, list[str]]:
    """Deterministic, proof-aligned decision + explainable summary.

    Used to guarantee convergence without relying on LLM stability/network.
    """

    observed = int(getattr(villager, "observed_red_eyes", 0))
    left_yesterday = int(getattr(villager, "observed_left_yesterday", 0))

    if villager.has_left:
        return False, 0.0, "我已经离开。", []

    if not public_announcement_made:
        return (
            False,
            0.0,
            "没有公开宣布，缺少‘至少一人红眼’的公共知识基准，归纳链条无法闭合，所以我无法确定自己是红眼。",
            ["未宣布→非公共知识", "无法闭合归纳链条"],
        )

    # Note: villagers still cannot see their own eyes; for explanation we only
    # claim certainty when the induction forces it.
    should_leave = _perfect_induction_decide_no_log(villager, day, public_announcement_made)

    if should_leave:
        if observed == 0:
            return (
                True,
                1.0,
                "我看到0个红眼睛，但游客已宣布至少有一个红眼睛，只能是我，所以我确定自己是红眼，今晚必须离开。",
                ["看到0个红眼", "宣布=公共知识", "只能是我"],
            )

        k = observed
        # The classic reason hinges on the fact that nobody left on day k.
        # In proof-aligned mode the overall system should make that true; we still
        # reference the observable.
        return (
            True,
            1.0,
            f"我看到{k}个红眼睛。直到第{k}晚仍无人离开（昨晚离开人数={left_yesterday}），"
            f"若我不是红眼则总红眼应为{k}并会在第{k}晚离开；既然没有发生，我确定自己也是红眼，今晚离开。",
            [f"看到{k}个红眼", f"第{k}晚无人离开", "反证→我也是红眼"],
        )

    # Not leaving today: cannot be certain yet.
    if observed == 0:
        return (
            False,
            0.0,
            "我看到0个红眼睛，但在未到第1晚之前还无法触发归纳基础结论，因此今晚不离开。",
            ["看到0个红眼", "等待第1晚"],
        )

    k = observed
    my_leave_day = k + 1
    return (
        False,
        0.0,
        f"我看到{k}个红眼睛。按归纳链条，只有在第{my_leave_day}晚（在第{k}晚无人离开后）才能确定自己是红眼；"
        f"今天是第{day}晚，我还不能确定，所以不离开。",
        [f"看到{k}个红眼", f"需等到第{my_leave_day}晚才可确定"],
    )


class ReasoningPolicy(Protocol):
    """推理策略接口"""

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        """返回该村民当晚是否离开（并可写入 villager.reasoning_log）。"""


@dataclass(frozen=True)
class PolicyByVillagerType:
    """按 villager.villager_type 路由到不同策略。

    用法：
    - mapping={"dummy": PerfectInductionPolicy(), "openai": OpenAIReasoningPolicy(...)}
    - default 用于兜底
    """

    mapping: dict[str, ReasoningPolicy]
    default: ReasoningPolicy | None = None

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        villager_type = getattr(villager, "villager_type", None)
        policy = self.mapping.get(str(villager_type), self.default)
        if policy is None:
            policy = PerfectInductionPolicy()
        return policy.decide(villager, day, public_announcement_made)


@dataclass(frozen=True)
class PerfectInductionPolicy:
    """完美逻辑学家：使用归纳链条推理（等价于当前实现的逻辑）。"""

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        if villager.has_left:
            return False

        if not public_announcement_made:
            villager.reasoning_log.append(
                f"第{day}天: 没有公开宣布。我仍会尝试推理，但缺少‘至少一人红眼’的公共知识基准，"
                f"归纳链条无法闭合，所以无法确定自己是否该离开"
            )
            return False

        if _is_blue(villager):
            villager.reasoning_log.append(
                f"第{day}天: 我看到 {villager.observed_red_eyes} 个红眼睛，"
                f"我不是红眼睛，所以不需要离开"
            )
            return False

        # 红眼睛：归纳基础 + 归纳步骤
        if villager.observed_red_eyes == 0:
            if day == 1:
                villager.reasoning_log.append(
                    f"第{day}天: [归纳基础] 我看到 0 个红眼睛，但游客说至少有一个，"
                    f"所以我一定是红眼睛！我必须离开。"
                )
                return True
            return False

        k = villager.observed_red_eyes
        my_leave_day = k + 1

        if day < my_leave_day:
            villager.reasoning_log.append(
                f"第{day}天: [归纳推理] 我看到 {k} 个红眼睛。"
                f"假设我是蓝眼睛，那就只有 {k} 个红眼睛。"
                f"根据归纳链条，{k} 个红眼睛会在第 {k} 天离开。"
                f"现在才第 {day} 天，我继续等待观察..."
            )
            return False

        if day == my_leave_day:
            villager.reasoning_log.append(
                f"第{day}天: [归纳推理完成] 我看到的 {k} 个红眼睛昨天没有离开！"
                f"如果只有他们 {k} 个是红眼睛，根据归纳链条他们应该在第 {k} 天离开。"
                f"他们没离开，说明我的假设'我是蓝眼睛'错误！"
                f"唯一的可能是：我也是红眼睛！我必须离开。"
            )
            return True

        return False


@dataclass(frozen=True)
class NoReasoningPolicy:
    """不够聪明：无法从观察+公共知识中推理出自己的眼睛颜色。"""

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        if villager.has_left:
            return False

        if not public_announcement_made:
            villager.reasoning_log.append(f"第{day}天: 没有公开宣布，我也不会推理")
            return False

        villager.reasoning_log.append(
            f"第{day}天: 我看到 {villager.observed_red_eyes} 个红眼睛，但我推理能力不足，"
            f"无法确定自己是否是红眼睛，所以不离开"
        )
        return False


@dataclass(frozen=True)
class BoundedInductionPolicy:
    """有限聪明：只能做有限深度的归纳推理。

    定义：
    - 对红眼睛村民来说，如果他看到 k 个红眼睛，想要在第 k+1 天得出“我也是红眼睛”，
      本质上需要“知道 k 个红眼睛会在第 k 天离开”的归纳链条。

    我们用 max_k 来表达他最多能处理到“k 个红眼睛在第 k 天离开”的层级。

    例子：
    - max_k=1：只知道 n=1 的情况可以推出 n=2（能处理到 2 个红眼睛离开）
    - max_k=2：还能推出 n=3

    当看到的 k > max_k 时：他无法完成归纳链条，因此永远不会离开。
    """

    max_k: int

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        if villager.has_left:
            return False

        if not public_announcement_made:
            villager.reasoning_log.append(
                f"第{day}天: 没有公开宣布。我仍会尝试推理，但缺少‘至少一人红眼’的公共知识基准，"
                f"归纳链条无法闭合，所以无法确定自己是否该离开"
            )
            return False

        if _is_blue(villager):
            villager.reasoning_log.append(
                f"第{day}天: 我看到 {villager.observed_red_eyes} 个红眼睛，"
                f"我不是红眼睛，所以不需要离开"
            )
            return False

        if villager.observed_red_eyes == 0:
            # n=1 的基础情况
            if day == 1 and self.max_k >= 0:
                villager.reasoning_log.append(
                    f"第{day}天: [有限归纳] 我看到0个红眼睛，游客说至少有一个 → 我是红眼睛，离开"
                )
                return True
            villager.reasoning_log.append(
                f"第{day}天: [有限归纳] 我看到0个红眼睛，但我无法把结论落实到行动"
            )
            return False

        k = villager.observed_red_eyes
        if k > self.max_k:
            villager.reasoning_log.append(
                f"第{day}天: [有限归纳] 我看到{k}个红眼睛，但我只能处理到 k≤{self.max_k} 的归纳链条，"
                f"无法得出结论，所以不离开"
            )
            return False

        # k 在能力范围内：按完美归纳执行
        my_leave_day = k + 1
        if day < my_leave_day:
            villager.reasoning_log.append(
                f"第{day}天: [有限归纳] 我看到{k}个红眼睛，且我能处理到 k≤{self.max_k}，继续等待"
            )
            return False

        if day == my_leave_day:
            villager.reasoning_log.append(
                f"第{day}天: [有限归纳完成] 第{k}天无人离开 → 我也是红眼睛，离开"
            )
            return True

        return False


@dataclass(frozen=True)
class MaxDayReasoningPolicy:
    """只能推理到某一天：超过该天数后就无法继续推理。

    这对应“村民没有那么聪明/耐心有限/推理链条太长会断掉”。

    行为：
    - day <= max_day 时：把决定委托给 inner
    - day > max_day 时：记录日志并永远不离开
    """

    max_day: int
    inner: ReasoningPolicy = PerfectInductionPolicy()

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        if villager.has_left:
            return False

        if day > self.max_day:
            villager.reasoning_log.append(
                f"第{day}天: [能力限制] 我只能推理到第{self.max_day}天，无法继续推理，所以不离开"
            )
            return False

        return self.inner.decide(villager, day, public_announcement_made)


@dataclass(frozen=True)
class FalliblePolicy:
    """有概率犯错的推理者（用于测试：如果村民不总是完美逻辑学家会怎样）。

    说明：
    - mistake_rate ∈ [0,1]
    - 默认只制造“漏走”（false negative）：
      即当 inner 推导应离开时，可能因为犯错而选择不离开。
      这样更贴近“推理不出/不敢确定”的直觉，也能避免出现不合规则的“误走”。
    - seed 用于让测试结果可复现。
    """

    mistake_rate: float
    seed: int = 0
    inner: ReasoningPolicy = PerfectInductionPolicy()

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        if villager.has_left:
            return False

        should_leave = self.inner.decide(villager, day, public_announcement_made)
        if not should_leave:
            return False

        # 可复现的伪随机：每个村民、每一天生成独立随机数
        rnd = Random(f"{self.seed}:{villager.id}:{day}").random()
        if rnd < self.mistake_rate:
            villager.reasoning_log.append(
                f"第{day}天: [犯错] 我本应离开，但我犯错/不确定，选择留下"
            )
            return False

        return True


def _extract_first_json_object(text: str) -> dict:
    """尽力从模型输出中提取第一个 JSON object。"""
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        obj = json.loads(snippet)
        if isinstance(obj, dict):
            return obj

    raise ValueError("Model output is not valid JSON object")


def _reason_implies_certain_red_eye(reason: str) -> bool:
    """Heuristic: detect when the model claims certainty that it is red-eyed.

    We only use this to enforce the puzzle's rule: if a villager is *certain* they are red-eyed,
    they must leave that night.
    """

    r = (reason or "").strip()
    if not r:
        return False

    # Negative certainty / hedges
    neg_phrases = (
        "不确定",
        "无法确定",
        "不能确定",
        "没法确定",
        "未能确定",
        "不能确认",
        "无法确认",
        "不敢确定",
        "无法断定",
    )
    if any(p in r for p in neg_phrases):
        return False

    # Explicitly deny red-eye (must never force-leave)
    deny_red_phrases = (
        "不是红眼",
        "不是红眼睛",
        "我不是红眼",
        "我不是红眼睛",
        "不认为自己是红眼",
        "不认为自己是红眼睛",
        "我不认为自己是红眼",
        "我不认为自己是红眼睛",
        "确定自己不是红眼",
        "确定自己不是红眼睛",
        "我确定自己不是红眼",
        "我确定自己不是红眼睛",
    )
    if any(p in r for p in deny_red_phrases):
        return False

    # Require explicit positive statement that *self* is red-eyed
    positive_red_phrases = (
        "我是红眼",
        "我是红眼睛",
        "我也是红眼",
        "我也是红眼睛",
        "自己是红眼",
        "自己是红眼睛",
    )
    if not any(p in r for p in positive_red_phrases):
        return False

    # Require explicit certainty marker
    certainty_markers = ("我确定", "能确定", "可以确定", "我能确定", "我已确定")
    if not any(m in r for m in certainty_markers):
        return False

    return True


def _should_force_leave(
    *,
    leave: bool,
    confidence_red: float | None,
    reason: str,
    threshold: float,
) -> tuple[bool, bool]:
    """Apply the puzzle rule: if certainty of being red-eyed is high, must leave.

    Returns:
        (final_leave, forced)
    """

    if confidence_red is not None:
        if (confidence_red >= threshold) and (not leave):
            return True, True
        return leave, False

    # Fallback for models that don't provide confidence_red
    if _reason_implies_certain_red_eye(reason) and (not leave):
        return True, True
    return leave, False


def _openai_chat_completions(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> str:
    normalized = base_url.rstrip("/")
    # Some providers (or user config) include '/v1' in base_url already.
    # Support both forms:
    # - https://api.siliconflow.cn        -> /v1/chat/completions
    # - https://api.siliconflow.cn/v1     -> /chat/completions
    if normalized.endswith("/v1"):
        url = normalized + "/chat/completions"
    else:
        url = normalized + "/v1/chat/completions"
    base_payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    # Some models/endpoints have evolved parameter names.
    # We try the newer `max_completion_tokens` first, then fall back to `max_tokens`.
    # We also try with response_format json_object, and fall back if unsupported.
    attempts: list[dict] = []
    for token_key in ("max_completion_tokens", "max_tokens"):
        for include_response_format in (True, False):
            payload = dict(base_payload)
            payload[token_key] = max_tokens
            if include_response_format:
                payload["response_format"] = {"type": "json_object"}
            attempts.append(payload)

    last_error: Exception | None = None
    for payload in attempts:
        req = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(req, timeout=timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            last_error = None
            break
        except HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
            last_error = RuntimeError(f"Chat Completions API HTTPError: {e.code} {detail}")
            continue
        except URLError as e:
            last_error = RuntimeError(f"Chat Completions API URLError: {e}")
            continue

    if last_error is not None:
        raise last_error

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Unexpected OpenAI response format: {data}") from e


@dataclass(frozen=True)
class OpenAIReasoningPolicy:
    """使用 OpenAI 推理模型来模拟“更像真实人”的村民。

    这不是为了保证标准谜题一定得出“第 N 天游离开”，而是为了观察：
    - 在信息有限、逻辑有限、表达混乱时，村民可能会如何选择。

    配置：
    - 兼容 OpenAI 接口的服务（默认使用 SiliconFlow）
    - 需要 API Key：优先读取 OPENAI_API_KEY，其次读取 SILICONFLOW_API_KEY
    - 可选模型：优先 OPENAI_MODEL，其次 SILICONFLOW_MODEL
    - 可选 base_url：优先 OPENAI_BASE_URL，其次 SILICONFLOW_BASE_URL
    """

    style: Literal["absolute_rational", "rational", "ordinary", "social"] = "rational"
    model: str | None = None
    base_url: str = "https://api.siliconflow.cn"
    temperature: float = 0.7
    max_tokens: int = 220
    timeout_s: float = 20.0
    certainty_threshold: float = 0.95
    align_to_standard_proof: bool = False

    def decide(self, villager: "Villager", day: int, public_announcement_made: bool) -> bool:
        if villager.has_left:
            return False

        # Load local `.env` (if present) so secrets can be configured without exporting.
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No API key found. Set OPENAI_API_KEY or SILICONFLOW_API_KEY in your environment "
                "to use OpenAIReasoningPolicy."
            )

        model = self.model or os.getenv("OPENAI_MODEL") or os.getenv("SILICONFLOW_MODEL") or "Qwen/QwQ-32B"
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("SILICONFLOW_BASE_URL") or self.base_url
        announcement = "是" if public_announcement_made else "否"
        observed = getattr(villager, "observed_red_eyes", 0)
        left_yesterday = getattr(villager, "observed_left_yesterday", 0)
        left_total = getattr(villager, "observed_left_total", 0)

        # 风格预设：更贴近“真实村民反应”，但可选对齐标准证明收敛行为
        style = self.style
        if style == "absolute_rational":
            style_desc = (
                "你是绝对理性、完美逻辑学家。"
                "你会严格遵循公共知识与归纳链条推理，不会情绪化，不会随意改变规则解释。"
            )
            temperature = 0.0
        elif style == "rational":
            style_desc = (
                "你是理性人：会尽力推理，但推理深度有限，遇到不确定会选择保守（更倾向留下）。"
            )
            temperature = min(self.temperature, 0.3)
        elif style == "ordinary":
            style_desc = (
                "你是普通人：可能紧张、犹豫、误解信息；不保证能完成归纳链条。"
            )
            temperature = max(self.temperature, 0.8)
        elif style == "social":
            style_desc = (
                "你是普通人且强烈受群体影响：会参考‘昨天是否有人离开’、‘已经有多少人离开’来决定。"
                "你仍遵守规则：只有当你确定自己是红眼睛时才离开。"
            )
            temperature = max(self.temperature, 0.8)
        else:  # pragma: no cover
            style_desc = "你是理性人。"
            temperature = self.temperature

        alignment_on = bool(self.align_to_standard_proof) or style == "absolute_rational"

        expected_leave = (
            _perfect_induction_decide_no_log(villager, day, public_announcement_made)
            if alignment_on
            else None
        )

        system = (
            "你在模拟一个村民的当晚决定。"
            + style_desc
            + "请不要输出逐步推理过程或内部思考链条，只给出可对外解释的简短理由与要点。"
        )

        if alignment_on:
            system += (
                "重要：本题采用标准红蓝眼谜题的强前提："
                "(1) 所有人都是完美逻辑推理者；"
                "(2) 这一点是公共知识；"
                "(3) 每个人都严格遵守规则：当且仅当自己确定是红眼睛时，当晚离开。"
                "你必须对齐标准归纳证明得到的行为（保证收敛）。"
            )

        user = (
            "谜题背景：村里每个人都能看到别人眼睛颜色但看不到自己。"
            "所有人都遵守规则：一旦自己确定是红眼睛，就会在当晚离开村子。"
            "每晚大家同时决定，第二天所有人都能看到谁离开了。\n\n"
            f"今天是第 {day} 天。游客是否公开宣布‘至少有一个红眼睛’：{announcement}。\n"
            f"你能看到别人里红眼睛的数量：{observed}。\n"
            f"你看到昨天离开的人数：{left_yesterday}。\n"
            f"你看到累计离开的人数：{left_total}。\n"
            "\n"
            '请输出严格 JSON：{'
            '"leave": true/false, '
            '"confidence_red": 0.0~1.0, '
            '"public_reason": string, '
            '"key_points": [string, ...]'
            '}。'
            "其中 confidence_red 表示你对‘自己是红眼睛’的确信程度（1.0=完全确定）。"
            "public_reason 是一段给旁人听得懂的简短理由；key_points 给出 1-3 条要点（不要写逐步推导）。"
        )

        if alignment_on:
            user += (
                "\n\n"
                "对齐标准证明的提示（用于帮助你给出一致输出）："
                "若游客已宣布，且你看到 k 个红眼睛："
                "- 在第 1..k 天：你无法确定自己是红眼睛，因此 leave=false；"
                "- 在第 k+1 天：如果之前无人离开，则你必须确定自己是红眼睛，因此 leave=true。"
                "当 leave=true 时，confidence_red 必须接近 1.0。"
            )

        content: str | None = None
        openai_error: str | None = None
        try:
            started = time.time()
            print(
                f"[OpenAI] start day={day} villager={getattr(villager, 'name', villager.id)} style={self.style} model={model}",
                flush=True,
            )
            content = _openai_chat_completions(
                api_key=api_key,
                base_url=base_url,
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=self.max_tokens,
                timeout_s=self.timeout_s,
            )
            elapsed_ms = int((time.time() - started) * 1000)
            print(
                f"[OpenAI] end   day={day} villager={getattr(villager, 'name', villager.id)} ({elapsed_ms}ms)",
                flush=True,
            )
        except Exception as e:
            openai_error = str(e)

        leave: bool
        confidence_red: float | None
        public_reason: str
        key_points: list[str]
        parsed_ok = False

        if content is not None:
            try:
                obj = _extract_first_json_object(content)
                leave = bool(obj.get("leave", False))
                confidence_raw = obj.get("confidence_red", None)
                if confidence_raw is None:
                    confidence_red = None
                else:
                    confidence_red = float(confidence_raw)
                    if confidence_red < 0.0:
                        confidence_red = 0.0
                    if confidence_red > 1.0:
                        confidence_red = 1.0
                public_reason = str(obj.get("public_reason", "") or obj.get("reason", ""))

                key_points_raw = obj.get("key_points", None)
                key_points = []
                if isinstance(key_points_raw, list):
                    for item in key_points_raw:
                        if isinstance(item, str) and item.strip():
                            key_points.append(item.strip())

                parsed_ok = True
            except Exception as e:
                openai_error = f"解析失败: {e}"

        if not parsed_ok:
            # Fallback: deterministic proof-aligned summary (still attempted OpenAI).
            leave, confidence_red, public_reason, key_points = _standard_proof_public_summary(
                villager,
                day,
                public_announcement_made,
            )

        public_reason = public_reason.strip().replace("\n", " ")
        if not public_reason:
            public_reason = "(无理由)"

        # In alignment mode: force the decision to match the standard proof.
        aligned = False
        if expected_leave is not None:
            if leave != expected_leave:
                leave = expected_leave
                aligned = True
            if leave:
                confidence_red = 1.0

        # Enforce the puzzle rule: if certainty is high, must leave.
        leave, forced = _should_force_leave(
            leave=leave,
            confidence_red=confidence_red,
            reason=public_reason,
            threshold=self.certainty_threshold,
        )

        conf_display = "?" if confidence_red is None else f"{confidence_red:.2f}"

        key_points_text = "" if not key_points else f"；要点: {' | '.join(key_points[:3])}"
        err_text = "" if not openai_error else f"；OpenAI错误: {openai_error}"
        villager.reasoning_log.append(
            f"第{day}天: [OpenAI] 决策={'离开' if leave else '留下'}"
            f"{'（对齐标准证明）' if (expected_leave is not None) else ''}"
            f"{'（强制：确信为红眼）' if forced else ''}"
            f"；confidence_red={conf_display}；理由: {public_reason}{key_points_text}{err_text}"
        )
        return leave
