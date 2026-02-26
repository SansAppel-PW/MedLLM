from src.train.real_pref_train import build_parser, str2bool


def test_real_pref_str2bool() -> None:
    assert str2bool("true") is True
    assert str2bool("false") is False


def test_real_pref_default_save_limit() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.save_total_limit == 2
