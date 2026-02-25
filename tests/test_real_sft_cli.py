from src.train.real_sft_train import build_parser, str2bool


def test_str2bool_values() -> None:
    assert str2bool("true") is True
    assert str2bool("1") is True
    assert str2bool("false") is False
    assert str2bool("0") is False


def test_parser_accepts_boolean_kv_args() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--use-lora",
            "false",
            "--load-in-4bit",
            "true",
            "--bf16",
            "false",
            "--fp16",
            "true",
        ]
    )
    assert args.use_lora is False
    assert args.load_in_4bit is True
    assert args.bf16 is False
    assert args.fp16 is True
