import json

from local_llm.cli import main


def test_models_list_returns_installable_runtime_manifests(capsys) -> None:
    assert main(["models", "list"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert [item["alias"] for item in payload] == ["qwen3-1.7b", "qwen3-8b"]
    assert payload[0]["devices"] == ["GPU", "CPU"]


def test_models_info_returns_error_for_unknown_alias(capsys) -> None:
    assert main(["models", "info", "not-configured"]) == 2
    assert "não configurado" in capsys.readouterr().out
