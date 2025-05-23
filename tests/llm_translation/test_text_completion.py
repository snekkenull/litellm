import json
import os
import sys
from datetime import datetime

sys.path.insert(
    0, os.path.abspath("../..")
)  # Adds the parent directory to the system path

import litellm
import pytest

from litellm.utils import (
    LiteLLMResponseObjectHandler,
)


from datetime import timedelta

from litellm.types.utils import (
    ModelResponse,
    TextCompletionResponse,
    TextChoices,
    Logprobs as TextCompletionLogprobs,
    Usage,
)


def test_convert_chat_to_text_completion():
    """Test converting chat completion to text completion"""
    chat_response = ModelResponse(
        id="chat123",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            {
                "index": 0,
                "message": {"content": "Hello, world!"},
                "finish_reason": "stop",
            }
        ],
        usage={"total_tokens": 10, "completion_tokens": 10},
        _hidden_params={"api_key": "test"},
    )

    text_completion = TextCompletionResponse()
    result = LiteLLMResponseObjectHandler.convert_chat_to_text_completion(
        response=chat_response, text_completion_response=text_completion
    )

    assert isinstance(result, TextCompletionResponse)
    assert result.id == "chat123"
    assert result.object == "text_completion"
    assert result.created == 1234567890
    assert result.model == "gpt-3.5-turbo"
    assert result.choices[0].text == "Hello, world!"
    assert result.choices[0].finish_reason == "stop"
    assert result.usage == Usage(
        completion_tokens=10,
        prompt_tokens=0,
        total_tokens=10,
        completion_tokens_details=None,
        prompt_tokens_details=None,
    )


def test_convert_provider_response_logprobs_non_huggingface():
    """Test converting provider logprobs for non-huggingface provider"""
    response = ModelResponse(id="test123", _hidden_params={})

    result = LiteLLMResponseObjectHandler._convert_provider_response_logprobs_to_text_completion_logprobs(
        response=response, custom_llm_provider="openai"
    )

    assert result is None


def test_convert_chat_to_text_completion_multiple_choices():
    """Test converting chat completion to text completion with multiple choices"""
    chat_response = ModelResponse(
        id="chat456",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            {
                "index": 0,
                "message": {"content": "First response"},
                "finish_reason": "stop",
            },
            {
                "index": 1,
                "message": {"content": "Second response"},
                "finish_reason": "length",
            },
        ],
        usage={"total_tokens": 20},
        _hidden_params={"api_key": "test"},
    )

    text_completion = TextCompletionResponse()
    result = LiteLLMResponseObjectHandler.convert_chat_to_text_completion(
        response=chat_response, text_completion_response=text_completion
    )

    assert isinstance(result, TextCompletionResponse)
    assert result.id == "chat456"
    assert result.object == "text_completion"
    assert len(result.choices) == 2
    assert result.choices[0].text == "First response"
    assert result.choices[0].finish_reason == "stop"
    assert result.choices[1].text == "Second response"
    assert result.choices[1].finish_reason == "length"
    assert result.usage == Usage(
        completion_tokens=0,
        prompt_tokens=0,
        total_tokens=20,
        completion_tokens_details=None,
        prompt_tokens_details=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_mode", [True, False])
async def test_text_completion_include_usage(sync_mode):
    """Test text completion with include_usage"""
    last_chunk = None
    if sync_mode:
        response = await litellm.atext_completion(
            model="gpt-3.5-turbo",
            prompt="Hello, world!",
            stream=True,
            stream_options={"include_usage": True},
        )

        async for chunk in response:
            print(chunk)
            last_chunk = chunk
    else:
        response = litellm.text_completion(
            model="gpt-3.5-turbo",
            prompt="Hello, world!",
            stream=True,
            stream_options={"include_usage": True},
        )

        for chunk in response:
            print(chunk)
            last_chunk = chunk

    assert last_chunk is not None
    assert last_chunk.usage is not None
    assert last_chunk.usage.prompt_tokens > 0
    assert last_chunk.usage.completion_tokens > 0
    assert last_chunk.usage.total_tokens > 0
