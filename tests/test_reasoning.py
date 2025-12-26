from src.puzzle import EyeColor, Villager
from src.reasoning import (
    _perfect_induction_decide_no_log,
    _reason_implies_certain_red_eye,
    _should_force_leave,
    OpenAIReasoningPolicy,
)


def test_reason_implies_certain_red_eye_true_on_explicit_positive() -> None:
    assert _reason_implies_certain_red_eye("我确定我是红眼，所以今晚离开") is True
    assert _reason_implies_certain_red_eye("我已确定自己是红眼睛，必须走") is True


def test_reason_implies_certain_red_eye_false_on_denial_or_uncertainty() -> None:
    assert _reason_implies_certain_red_eye("我确定自己不是红眼，所以不走") is False
    assert _reason_implies_certain_red_eye("我不认为自己是红眼睛，今晚不离开") is False
    assert _reason_implies_certain_red_eye("我无法确定自己是不是红眼") is False


def test_reason_implies_certain_red_eye_false_without_certainty_marker() -> None:
    assert _reason_implies_certain_red_eye("我是红眼，但我也可能错") is False
    assert _reason_implies_certain_red_eye("我是红眼睛（只是猜测）") is False


def test_should_force_leave_by_confidence_threshold() -> None:
    leave, forced = _should_force_leave(
        leave=False,
        confidence_red=0.97,
        reason="我还不确定，但我猜是红眼",
        threshold=0.95,
    )
    assert leave is True
    assert forced is True

    leave, forced = _should_force_leave(
        leave=False,
        confidence_red=0.50,
        reason="我确定我是红眼",
        threshold=0.95,
    )
    # Confidence wins; we should NOT force on low confidence.
    assert leave is False
    assert forced is False


def test_perfect_induction_decide_no_log_matches_expected_without_mutation() -> None:
    v = Villager(id=1, eye_color=EyeColor.RED, name="红1")
    v.observed_red_eyes = 2
    v.reasoning_log.append("pre")

    # observed_red_eyes=2 => leave day is 3
    assert _perfect_induction_decide_no_log(v, day=1, public_announcement_made=True) is False
    assert _perfect_induction_decide_no_log(v, day=2, public_announcement_made=True) is False
    assert _perfect_induction_decide_no_log(v, day=3, public_announcement_made=True) is True
    assert v.reasoning_log == ["pre"]


def test_perfect_induction_decide_no_log_blue_or_no_announcement() -> None:
    v_blue = Villager(id=2, eye_color=EyeColor.BLUE, name="蓝1")
    v_blue.observed_red_eyes = 1
    assert _perfect_induction_decide_no_log(v_blue, day=2, public_announcement_made=True) is False

    v_red = Villager(id=3, eye_color=EyeColor.RED, name="红2")
    v_red.observed_red_eyes = 0
    assert _perfect_induction_decide_no_log(v_red, day=1, public_announcement_made=False) is False


def test_openai_absolute_rational_still_calls_openai_but_aligns_leave(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_chat(*args, **kwargs):
        calls["n"] += 1
        # Deliberately contradict the standard proof: claim leave=false with 0 confidence.
        return '{"leave": false, "confidence_red": 0.0, "public_reason": "我不确定", "key_points": ["x"]}'

    import src.reasoning as reasoning_mod

    monkeypatch.setattr(reasoning_mod, "_openai_chat_completions", fake_chat)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    v = Villager(id=1, eye_color=EyeColor.RED, name="红1")
    v.villager_type = "openai"
    v.observed_red_eyes = 2

    policy = OpenAIReasoningPolicy(style="absolute_rational", align_to_standard_proof=True)
    # For observed_red_eyes=2, leave day is 3.
    assert policy.decide(v, day=3, public_announcement_made=True) is True
    assert calls["n"] == 1
