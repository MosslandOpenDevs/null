from types import SimpleNamespace

from null_engine.api.routes.export import (
    _conversation_training_sample,
    _knowledge_graph_training_sample,
    _parse_include,
    _wiki_training_sample,
)


def test_parse_include_trims_and_deduplicates() -> None:
    include_set = _parse_include("conversations, wiki,kg,kg,, ")
    assert include_set == {"conversations", "wiki", "kg"}


def test_conversation_chatml_sample() -> None:
    conversation = SimpleNamespace(
        topic="Faction diplomacy",
        summary="Tensions rise between two blocs.",
        messages=[
            {"agent_id": "A1", "content": "We should negotiate first."},
            {"agent_id": "B3", "content": "Only if sanctions are removed."},
        ],
    )

    sample = _conversation_training_sample(conversation, "chatml")
    assert sample == {
        "messages": [
            {"role": "system", "content": "Topic: Faction diplomacy"},
            {"role": "user", "content": "[A1]: We should negotiate first."},
            {"role": "user", "content": "[B3]: Only if sanctions are removed."},
            {"role": "assistant", "content": "Tensions rise between two blocs."},
        ]
    }


def test_conversation_alpaca_uses_summary_when_output_missing() -> None:
    conversation = SimpleNamespace(
        topic="Silent meeting",
        summary="No public statements were made.",
        messages=[
            {"agent_id": "X", "content": "We meet at dawn."},
            {"agent_id": "Y", "content": "Understood."},
        ],
    )

    sample = _conversation_training_sample(conversation, "alpaca")
    assert sample == {
        "instruction": "Continue the conversation about 'Silent meeting'",
        "input": "X: We meet at dawn.\nY: Understood.",
        "output": "No public statements were made.",
    }


def test_conversation_returns_none_when_empty() -> None:
    conversation = SimpleNamespace(topic="Empty", summary="", messages=[])
    assert _conversation_training_sample(conversation, "sharegpt") is None


def test_wiki_sharegpt_sample() -> None:
    page = SimpleNamespace(title="Neon Joseon", content="A techno-feudal kingdom.")
    sample = _wiki_training_sample(page, "sharegpt")

    assert sample == {
        "conversations": [
            {"from": "human", "value": "Write about Neon Joseon"},
            {"from": "gpt", "value": "A techno-feudal kingdom."},
        ]
    }


def test_knowledge_graph_chatml_sample() -> None:
    edges = [
        SimpleNamespace(subject="Guild", predicate="controls", object="Port"),
        SimpleNamespace(subject="Court", predicate="allies_with", object="Academy"),
    ]
    sample = _knowledge_graph_training_sample(edges, "chatml")

    assert sample == {
        "messages": [
            {"role": "system", "content": "Extract knowledge triples."},
            {
                "role": "assistant",
                "content": "Guild controls Port\nCourt allies_with Academy",
            },
        ]
    }
