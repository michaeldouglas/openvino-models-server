import pytest
from pydantic import ValidationError

from local_llm.config import Settings


def test_fast_profile_is_a_valid_named_profile() -> None:
    settings = Settings(performance_profile="fast")

    assert settings.performance_profile == "fast"


def test_unknown_profile_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(performance_profile="experimental")


def test_concurrency_must_be_positive_and_bounded() -> None:
    with pytest.raises(ValidationError):
        Settings(max_concurrency=0)

    with pytest.raises(ValidationError):
        Settings(max_concurrency=33)
