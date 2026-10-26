import json
from types import SimpleNamespace

import pytest
from openai import APITimeoutError

from config import Settings
from llm_client import EmptyModelResponseError, LLMClient
from model_router import OLLAMA_REQUEST_TIMEOUT_SECONDS


def make_config(*, api_key="test-key", anthropic_api_key=""):
    return Settings(
        ollama_model="test-k2:latest",
        ollama_base_url="http://localhost:11434/v1/",
        mimo_api_key=api_key,
        mimo_base_url="https://api.example.test/v1",
        anthropic_api_key=anthropic_api_key,
    )


class OllamaTimeout(APITimeoutError):
    def __init__(self) -> None:
        Exception.__init__(self, "timed out")


class FakeCompletions:
    def __init__(self, response, error=None):
        self.response = response
        self.error = error
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        if self.error is not None:
            raise self.error
        return self.response


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        return self.response


def fake_provider(*, content="OK", finish_reason="stop", tool_calls=None, error=None):
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content, tool_calls=tool_calls),
                finish_reason=finish_reason,
            )
        ],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=3),
    )
    completions = FakeCompletions(response, error=error)
    provider = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return provider, completions


def fake_anthropic():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", thinking="skip me"),
            SimpleNamespace(type="text", text="from haiku"),
        ],
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=9, output_tokens=4),
    )
    messages = FakeMessages(response)
    return SimpleNamespace(messages=messages), messages


def test_light_request_uses_ollama_and_normalizes_result():
    ollama, completions = fake_provider()
    llm = LLMClient(config=make_config(), provider_clients={"ollama": ollama})

    result = llm.complete(
        task="refund_check",
        max_output_tokens=64,
        system="Use JSON.",
        messages=[{"role": "user", "content": "Check this reply."}],
    )

    assert result.text == "OK"
    assert result.provider == "ollama"
    assert result.model == "test-k2:latest"
    assert result.usage.input_tokens == 12
    assert completions.request["max_tokens"] == 64
    assert completions.request["messages"][0] == {
        "role": "system",
        "content": "Use JSON.",
    }
    assert completions.request["timeout"].read == OLLAMA_REQUEST_TIMEOUT_SECONDS
    assert completions.request["timeout"].connect == 5.0


def test_heavy_request_uses_mimo_parameters():
    mimo, completions = fake_provider()
    llm = LLMClient(config=make_config(), provider_clients={"mimo": mimo})

    result = llm.complete(
        task="architecture",
        max_output_tokens=80,
        messages=[{"role": "user", "content": "Explain briefly."}],
    )

    assert result.provider == "mimo"
    assert result.model == "mimo-v2.6-pro"
    assert completions.request["max_completion_tokens"] == 80
    assert completions.request["extra_body"] == {"thinking": {"type": "disabled"}}
    assert "timeout" not in completions.request


def test_long_code_routes_an_otherwise_light_task_to_mimo():
    mimo, _ = fake_provider()
    llm = LLMClient(config=make_config(), provider_clients={"mimo": mimo})

    result = llm.complete(
        task="summarize",
        code="x" * 30_001,
        max_output_tokens=80,
        messages=[{"role": "user", "content": "Summarize this code."}],
    )

    assert result.provider == "mimo"
    assert result.model == "mimo-v2.6-pro"


def test_long_user_message_is_used_when_code_argument_is_omitted():
    mimo, _ = fake_provider()
    llm = LLMClient(config=make_config(), provider_clients={"mimo": mimo})

    result = llm.complete(
        task="summarize",
        max_output_tokens=80,
        messages=[{"role": "user", "content": "x" * 30_001}],
    )

    assert result.provider == "mimo"


def test_explicit_code_controls_routing_when_messages_are_long():
    ollama, _ = fake_provider()
    llm = LLMClient(config=make_config(), provider_clients={"ollama": ollama})

    result = llm.complete(
        task="summarize",
        code="short code",
        max_output_tokens=80,
        messages=[{"role": "user", "content": "x" * 30_001}],
    )

    assert result.provider == "ollama"


def test_tool_calls_are_returned_as_typed_values():
    raw_call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="lookup_faq", arguments='{"topic":"refund"}'),
    )
    ollama, completions = fake_provider(
        content=None, finish_reason="tool_calls", tool_calls=[raw_call]
    )
    llm = LLMClient(config=make_config(), provider_clients={"ollama": ollama})

    result = llm.complete(
        task="faq",
        max_output_tokens=100,
        messages=[{"role": "user", "content": "How do refunds work?"}],
        tools=[{"type": "function", "function": {"name": "lookup_faq"}}],
        tool_choice="auto",
    )

    assert result.text == ""
    assert result.tool_calls[0].name == "lookup_faq"
    assert result.tool_calls[0].arguments == {"topic": "refund"}
    assert completions.request["tools"] == [
        {"type": "function", "function": {"name": "lookup_faq"}}
    ]
    assert completions.request["tool_choice"] == "auto"
    assert json.loads(json.dumps(result.tool_calls[0].arguments)) == {"topic": "refund"}


def test_empty_text_and_no_tool_calls_raise_a_clear_error():
    ollama, _ = fake_provider(content="", finish_reason="length")
    llm = LLMClient(config=make_config(), provider_clients={"ollama": ollama})

    with pytest.raises(EmptyModelResponseError, match="Increase the output-token limit"):
        llm.complete(
            task="default",
            max_output_tokens=16,
            messages=[{"role": "user", "content": "Reply OK."}],
        )


def test_ollama_timeout_falls_back_to_haiku_at_low_effort():
    ollama, ollama_call = fake_provider(error=OllamaTimeout())
    haiku, haiku_call = fake_anthropic()
    llm = LLMClient(
        config=make_config(anthropic_api_key="anthropic-key"),
        provider_clients={"ollama": ollama, "anthropic": haiku},
    )

    result = llm.complete(
        task="refund_check",
        max_output_tokens=64,
        system="Use JSON.",
        messages=[{"role": "user", "content": "Check this reply."}],
    )

    assert result.provider == "anthropic"
    assert result.model == "claude-haiku-5-5"
    assert result.text == "from haiku"
    assert result.finish_reason == "end_turn"
    assert result.usage.input_tokens == 9
    assert result.usage.output_tokens == 4
    assert haiku_call.request["output_config"] == {"effort": "low"}
    assert haiku_call.request["max_tokens"] == 64
    assert haiku_call.request["system"] == "Use JSON."
    assert haiku_call.request["messages"] == [
        {"role": "user", "content": "Check this reply."}
    ]
    assert "tools" not in haiku_call.request
    assert ollama_call.request["timeout"].read == OLLAMA_REQUEST_TIMEOUT_SECONDS


def test_ollama_timeout_translates_tools_for_haiku():
    ollama, _ = fake_provider(error=OllamaTimeout())
    haiku_response = SimpleNamespace(
        content=[
            SimpleNamespace(
                type="tool_use",
                id="toolu_1",
                name="lookup_faq",
                input={"topic": "refund"},
            )
        ],
        stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=3, output_tokens=2),
    )
    haiku_call = FakeMessages(haiku_response)
    haiku = SimpleNamespace(messages=haiku_call)
    llm = LLMClient(
        config=make_config(anthropic_api_key="anthropic-key"),
        provider_clients={"ollama": ollama, "anthropic": haiku},
    )

    result = llm.complete(
        task="faq",
        max_output_tokens=100,
        messages=[
            {"role": "user", "content": "How do refunds work?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "lookup_faq",
                            "arguments": '{"topic":"refund"}',
                        },
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call-1", "content": "Refunds take 5 days."},
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "lookup_faq",
                    "description": "Find a FAQ",
                    "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}},
                },
            }
        ],
        tool_choice="required",
    )

    assert result.tool_calls[0].name == "lookup_faq"
    assert result.tool_calls[0].arguments == {"topic": "refund"}
    assert haiku_call.request["tool_choice"] == {"type": "any"}
    assert haiku_call.request["tools"][0]["input_schema"]["properties"]["topic"]["type"] == "string"
    assert haiku_call.request["messages"][1]["content"][0]["type"] == "tool_use"
    assert haiku_call.request["messages"][2]["content"][0]["type"] == "tool_result"


def test_ollama_timeout_requires_anthropic_key():
    ollama, _ = fake_provider(error=OllamaTimeout())
    llm = LLMClient(config=make_config(), provider_clients={"ollama": ollama})

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        llm.complete(
            task="refund_check",
            max_output_tokens=64,
            messages=[{"role": "user", "content": "Check this reply."}],
        )


def test_non_timeout_ollama_error_does_not_fall_back():
    ollama, _ = fake_provider(error=RuntimeError("connection refused"))
    haiku, haiku_call = fake_anthropic()
    llm = LLMClient(
        config=make_config(anthropic_api_key="anthropic-key"),
        provider_clients={"ollama": ollama, "anthropic": haiku},
    )

    with pytest.raises(RuntimeError, match="connection refused"):
        llm.complete(
            task="refund_check",
            max_output_tokens=64,
            messages=[{"role": "user", "content": "Check this reply."}],
        )

    assert haiku_call.request is None


def test_mimo_timeout_does_not_fall_back():
    mimo, _ = fake_provider(error=OllamaTimeout())
    haiku, haiku_call = fake_anthropic()
    llm = LLMClient(
        config=make_config(anthropic_api_key="anthropic-key"),
        provider_clients={"mimo": mimo, "anthropic": haiku},
    )

    with pytest.raises(APITimeoutError):
        llm.complete(
            task="architecture",
            max_output_tokens=64,
            messages=[{"role": "user", "content": "Explain briefly."}],
        )

    assert haiku_call.request is None


def test_heavy_route_requires_mimo_key():
    llm = LLMClient(config=make_config(api_key=""))

    with pytest.raises(RuntimeError, match="MIMO_API_KEY"):
        llm.complete(
            task="architecture",
            max_output_tokens=64,
            messages=[{"role": "user", "content": "Reply OK."}],
        )
