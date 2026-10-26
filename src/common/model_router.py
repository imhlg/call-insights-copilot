"""Pure task-to-provider routing rules."""

from dataclasses import dataclass
from typing import Literal

from config import Settings, settings

Provider = Literal["ollama", "mimo", "anthropic"]

CODE_SIZE_LIMIT = 30_000
HEAVY_TASKS = frozenset({"refactor", "architecture", "debug_hard"})
OLLAMA_REQUEST_TIMEOUT_SECONDS = 180
HAIKU_FALLBACK_MODEL = "claude-haiku-5-5"
HAIKU_EFFORT = "low"


@dataclass(frozen=True)
class ModelRoute:
    provider: Provider
    model: str


def _needs_heavy_model(task: str, code: str) -> bool:
    normalized_task = task.strip().lower()
    return len(code) > CODE_SIZE_LIMIT or normalized_task in HEAVY_TASKS


def _pick_model(task: str, code: str, config: Settings) -> str:
    if _needs_heavy_model(task, code):
        return config.mimo_model
    return config.ollama_model


def pick_model(task: str, code: str) -> str:
    """Choose MiMo for large code inputs or tasks needing cross-file reasoning."""
    return _pick_model(task, code, settings)


def route_for_task(
    task: str,
    code: str = "",
    *,
    escalate: bool = False,
    config: Settings = settings,
) -> ModelRoute:
    """Resolve the selected model ID to its provider."""
    use_mimo = escalate or _needs_heavy_model(task, code)
    model = config.mimo_model if use_mimo else config.ollama_model
    provider: Provider = "mimo" if use_mimo else "ollama"
    return ModelRoute(provider=provider, model=model)


def ollama_timeout_fallback() -> ModelRoute:
    """Light-task route used after the local model exceeds its request timeout."""
    return ModelRoute(provider="anthropic", model=HAIKU_FALLBACK_MODEL)
