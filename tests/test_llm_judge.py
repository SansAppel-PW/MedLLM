from eval.llm_judge import JudgeDecision, parse_judge_decision, win_rate_from_decisions


def test_parse_judge_decision_json() -> None:
    raw = '{"winner":"B","reason":"B更安全","score_a":6.0,"score_b":8.5}'
    out = parse_judge_decision(raw)
    assert out.winner == "B"
    assert out.score_a == 6.0
    assert out.score_b == 8.5


def test_parse_judge_decision_with_noise() -> None:
    raw = "结果如下:\n{'winner':'A','reason':'ok'}"
    out = parse_judge_decision(raw)
    assert out.winner == "TIE"


def test_win_rate_from_decisions() -> None:
    rows = [
        JudgeDecision(winner="B", reason="", score_a=0, score_b=0, raw={}),
        JudgeDecision(winner="A", reason="", score_a=0, score_b=0, raw={}),
        JudgeDecision(winner="TIE", reason="", score_a=0, score_b=0, raw={}),
    ]
    assert abs(win_rate_from_decisions(rows, "B") - 0.5) < 1e-9
