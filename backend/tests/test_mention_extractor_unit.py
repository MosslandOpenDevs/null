from null_engine.services.mention_extractor import _fuzzy_match, _normalize


def test_normalize_collapses_punctuation_and_spaces() -> None:
    assert _normalize("  Roman-Empire!!  ") == "roman empire"
    assert _normalize("Dune/Prophecy") == "dune prophecy"
    assert _normalize("Law & Order") == "law order"


def test_fuzzy_match_handles_punctuation_variants() -> None:
    assert _fuzzy_match("Roman-Empire", "roman empire rises") is True
    assert _fuzzy_match("Dune_Prophecy", "The dune prophecy arc") is True


def test_fuzzy_match_requires_meaningful_tokens() -> None:
    assert _fuzzy_match("x", "x marks the spot") is False
    assert _fuzzy_match("", "anything") is False
