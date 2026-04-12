# -*- coding: utf-8 -*-
"""Fixtures for Local Models module tests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Generator

import pytest

from copaw.local_models.schema import (
    BackendType,
    DownloadSource,
    LocalModelInfo,
    LocalModelsManifest,
)


@pytest.fixture
def mock_models_dir(temp_working_dir: Path) -> Generator[Path, None, None]:
    """Create a mock models directory.

    Args:
        temp_working_dir: Temporary working directory fixture

    Yields:
        Path to the mock models directory
    """
    models_dir = temp_working_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    yield models_dir


@pytest.fixture
def sample_local_model_info() -> LocalModelInfo:
    """Return a sample LocalModelInfo for testing.

    Returns:
        LocalModelInfo instance
    """
    return LocalModelInfo(
        id="Qwen/Qwen2.5-7B-Instruct-GGUF/qwen2.5-7b-instruct-q4_k_m.gguf",
        repo_id="Qwen/Qwen2.5-7B-Instruct-GGUF",
        filename="qwen2.5-7b-instruct-q4_k_m.gguf",
        backend=BackendType.LLAMACPP,
        source=DownloadSource.HUGGINGFACE,
        file_size=4500000000,
        local_path="/models/Qwen--Qwen2.5-7B-Instruct-GGUF/qwen2.5-7b-instruct-q4_k_m.gguf",
        display_name="Qwen2.5-7B-Instruct (qwen2.5-7b-instruct-q4_k_m.gguf)",
    )


@pytest.fixture
def sample_mlx_model_info() -> LocalModelInfo:
    """Return a sample MLX model LocalModelInfo for testing.

    Returns:
        LocalModelInfo instance for MLX model
    """
    return LocalModelInfo(
        id="mlx-community/Qwen2.5-7B-Instruct-4bit",
        repo_id="mlx-community/Qwen2.5-7B-Instruct-4bit",
        filename="(full repo)",
        backend=BackendType.MLX,
        source=DownloadSource.HUGGINGFACE,
        file_size=4500000000,
        local_path="/models/mlx-community--Qwen2.5-7B-Instruct-4bit",
        display_name="Qwen2.5-7B-Instruct-4bit",
    )


@pytest.fixture
def sample_manifest(
    sample_local_model_info: LocalModelInfo,
    sample_mlx_model_info: LocalModelInfo,
) -> LocalModelsManifest:
    """Return a sample manifest with models.

    Args:
        sample_local_model_info: Sample LLAMACPP model info
        sample_mlx_model_info: Sample MLX model info

    Returns:
        LocalModelsManifest with sample models
    """
    return LocalModelsManifest(
        models={
            sample_local_model_info.id: sample_local_model_info,
            sample_mlx_model_info.id: sample_mlx_model_info,
        }
    )


@pytest.fixture
def sample_model_file(temp_working_dir: Path) -> Path:
    """Create a sample model file for testing.

    Args:
        temp_working_dir: Temporary working directory fixture

    Returns:
        Path to the sample model file
    """
    models_dir = temp_working_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    model_file = models_dir / "test-model.gguf"
    model_file.write_bytes(b"fake model content" * 1000)

    return model_file


@pytest.fixture
def sample_think_text() -> str:
    """Return sample text with thinking tags."""
    # Uses Unicode escape sequences to avoid issues with special characters
    # \u003cthink\u003e = <think> and \u003c/think\u003e = </think>
    think_start = "\u003cthink\u003e"
    think_end = "\u003c/think\u003e"
    return f"""Let me think about this problem.
{think_start}
First, I need to analyze the requirements.
Then, I'll propose a solution.
Finally, I'll verify the implementation.
{think_end}
The answer is 42."""


@pytest.fixture
def sample_tool_call_text() -> str:
    """Return sample text with tool call tags."""
    # Uses Unicode escape sequences to avoid issues with special characters
    # \u003ctool_call\u003e = <tool_call> and \u003c/tool_call\u003e = </tool_call>
    tool_start = "\u003ctool_call\u003e"
    tool_end = "\u003c/tool_call\u003e"
    return f"""I need to call a function.
{tool_start}
{{"name": "get_weather", "arguments": {{"location": "Beijing"}}}}
{tool_end}
That's the result."""


@pytest.fixture
def sample_multiple_tool_calls_text() -> str:
    """Return sample text with multiple tool call tags."""
    tool_start = "\u003ctool_call\u003e"
    tool_end = "\u003c/tool_call\u003e"
    return f"""I need to call multiple functions.
{tool_start}
{{"name": "get_weather", "arguments": {{"location": "Beijing"}}}}
{tool_end}
Now let me call another function.
{tool_start}
{{"name": "get_time", "arguments": {{"timezone": "Asia/Shanghai"}}}}
{tool_end}
Done."""
