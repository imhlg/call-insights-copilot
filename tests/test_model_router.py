import pytest

from config import MIMO_PRO_MODEL, Settings, settings
from model_router import (
    HAIKU_EFFORT,
    HAIKU_FALLBACK_MODEL,
    OLLAMA_REQUEST_TIMEOUT_SECONDS,
    ollama_timeout_fallback,
    pick_model,
    route_for_task,
)


def test_ollama_timeout_fallback_is_haiku_at_low_effort():
    route = ollama_timeout_fallback()

    assert route.provider == "anthropic"
    assert route.model == HAIKU_FALLBACK_MODEL
    assert HAIKU_FALLBACK_MODEL == "claude-haiku-5-5"
    assert HAIKU_EFFORT == "low"
    assert OLLAMA_REQUEST_TIMEOUT_SECONDS == 180


def test_simple_task_routes_to_local_ollama():
    config = Settings(
        ollama_model="test-k2:latest",
        ollama_base_url="http://localhost:11434/v1/",
        mimo_api_key="",
    )

    assert route_for_task("refund_check", "short code", config=config).provider == "ollama"
    assert pick_model("refund_check", "short code") == settings.ollama_model


@pytest.mark.parametrize("task", ["refactor", "architecture", "debug_hard"])
def test_heavy_task_routes_to_mimo_pro(task):
    config = Settings(
        ollama_model="test-k2:latest",
        ollama_base_url="http://localhost:11434/v1/",
        mimo_api_key="test-key",
    )

    assert route_for_task(task, "short code", config=config).provider == "mimo"
    assert pick_model(task, "short code") == settings.mimo_model


def test_escalation_overrides_the_size_and_task_rules():
    config = Settings(
        ollama_model="test-k2:latest",
        ollama_base_url="http://localhost:11434/v1/",
        mimo_api_key="test-key",
    )

    assert route_for_task("refund_check", "short code", escalate=True, config=config).provider == "mimo"


def test_unlisted_short_task_defaults_to_local():
    config = Settings(
        ollama_model="test-k2:latest",
        ollama_base_url="http://localhost:11434/v1/",
        mimo_api_key="test-key",
    )

    assert pick_model("summarize", "short code") == settings.ollama_model


def test_code_size_threshold_is_strictly_greater_than_30000():
    config = Settings(
        ollama_model="test-k2:latest",
        ollama_base_url="http://localhost:11434/v1/",
        mimo_api_key="test-key",
    )

    assert pick_model("summarize", "x" * 30_000) == settings.ollama_model
    assert pick_model("summarize", "x" * 30_001) == MIMO_PRO_MODEL


def test_heavy_model_cannot_be_changed_to_flash():
    with pytest.raises(ValueError, match="Heavy tasks must use"):
        Settings(
            ollama_model="test-k2:latest",
            ollama_base_url="http://localhost:11434/v1/",
            mimo_api_key="test-key",
            mimo_model="mimo-v2.6-flash",
        )


def test_token_plan_requires_explicit_region_url():
    config = Settings(
        ollama_model="test-k2:latest",
        ollama_base_url="http://localhost:11434/v1/",
        mimo_api_key="tp-test-key",
    )

    with pytest.raises(RuntimeError, match="MIMO_BASE_URL"):
        config.get_mimo_base_url()
