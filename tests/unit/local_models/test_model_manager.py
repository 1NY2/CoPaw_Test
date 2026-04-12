# -*- coding: utf-8 -*-
"""Tests for local_models manager module."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from copaw.local_models.schema import (
    BackendType,
    DownloadSource,
    LocalModelInfo,
    LocalModelsManifest,
)
from copaw.local_models.manager import (
    _ensure_models_dir,
    _load_manifest,
    _save_manifest,
    _sanitize_repo_id,
    delete_local_model,
    get_local_model,
    list_local_models,
    LocalModelManager,
)


class TestEnsureModelsDir:
    """Tests for _ensure_models_dir function."""

    def test_ensure_models_dir_creates_dir(
        self, temp_working_dir: Path
    ) -> None:
        """Test that models directory is created."""
        models_dir = temp_working_dir / "models"

        with patch("copaw.local_models.manager.MODELS_DIR", models_dir):
            result = _ensure_models_dir()

        assert result == models_dir
        assert models_dir.exists()

    def test_ensure_models_dir_existing(
        self, temp_working_dir: Path
    ) -> None:
        """Test that existing directory is returned."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        with patch("copaw.local_models.manager.MODELS_DIR", models_dir):
            result = _ensure_models_dir()

        assert result == models_dir


class TestLoadManifest:
    """Tests for _load_manifest function."""

    def test_load_manifest_empty(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading when no manifest exists."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            result = _load_manifest()

        assert isinstance(result, LocalModelsManifest)
        assert len(result.models) == 0

    def test_load_manifest_with_models(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading an existing manifest."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        manifest_data = {
            "models": {
                "test/model": {
                    "id": "test/model",
                    "repo_id": "test/model",
                    "filename": "model.gguf",
                    "backend": "llamacpp",
                    "source": "huggingface",
                    "file_size": 1000,
                    "local_path": "/path/to/model",
                    "display_name": "Test Model",
                }
            }
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            result = _load_manifest()

        assert len(result.models) == 1
        assert "test/model" in result.models

    def test_load_manifest_corrupted(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading a corrupted manifest returns empty."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"
        manifest_path.write_text("not valid json", encoding="utf-8")

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            result = _load_manifest()

        assert isinstance(result, LocalModelsManifest)
        assert len(result.models) == 0


class TestSaveManifest:
    """Tests for _save_manifest function."""

    def test_save_manifest(
        self, temp_working_dir: Path
    ) -> None:
        """Test saving a manifest."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        manifest = LocalModelsManifest()
        manifest.models["test/model"] = LocalModelInfo(
            id="test/model",
            repo_id="test/model",
            filename="model.gguf",
            backend=BackendType.LLAMACPP,
            source=DownloadSource.HUGGINGFACE,
            file_size=1000,
            local_path="/path/to/model",
            display_name="Test Model",
        )

        with patch("copaw.local_models.manager.MODELS_DIR", models_dir):
            with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
                _save_manifest(manifest)

        assert manifest_path.exists()
        loaded = json.loads(manifest_path.read_text())
        assert "test/model" in loaded["models"]


class TestSanitizeRepoId:
    """Tests for _sanitize_repo_id function."""

    def test_sanitize_repo_id(self) -> None:
        """Test sanitizing repo ID."""
        assert _sanitize_repo_id("user/model") == "user--model"
        assert _sanitize_repo_id("simple") == "simple"
        assert _sanitize_repo_id("org/repo/name") == "org--repo--name"


class TestListLocalModels:
    """Tests for list_local_models function."""

    def test_list_local_models_empty(
        self, temp_working_dir: Path
    ) -> None:
        """Test listing when no models exist."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            result = list_local_models()

        assert result == []

    def test_list_local_models_with_models(
        self, temp_working_dir: Path, sample_manifest: LocalModelsManifest
    ) -> None:
        """Test listing existing models."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            _save_manifest(sample_manifest)
            result = list_local_models()

        assert len(result) == 2

    def test_list_local_models_filter_backend(
        self, temp_working_dir: Path, sample_manifest: LocalModelsManifest
    ) -> None:
        """Test filtering by backend."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            _save_manifest(sample_manifest)
            result = list_local_models(backend=BackendType.LLAMACPP)

        assert len(result) == 1
        assert result[0].backend == BackendType.LLAMACPP

    def test_list_local_models_filter_mlx(
        self, temp_working_dir: Path, sample_manifest: LocalModelsManifest
    ) -> None:
        """Test filtering by MLX backend."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            _save_manifest(sample_manifest)
            result = list_local_models(backend=BackendType.MLX)

        assert len(result) == 1
        assert result[0].backend == BackendType.MLX


class TestGetLocalModel:
    """Tests for get_local_model function."""

    def test_get_local_model_exists(
        self, temp_working_dir: Path, sample_manifest: LocalModelsManifest
    ) -> None:
        """Test getting an existing model."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            _save_manifest(sample_manifest)
            # Get the first model ID from the manifest
            model_id = next(iter(sample_manifest.models.keys()))
            result = get_local_model(model_id)

        assert result is not None
        assert result.id == model_id

    def test_get_local_model_not_found(
        self, temp_working_dir: Path
    ) -> None:
        """Test getting a nonexistent model."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            result = get_local_model("nonexistent/model")

        assert result is None


class TestDeleteLocalModel:
    """Tests for delete_local_model function."""

    def test_delete_local_model_file(
        self, temp_working_dir: Path
    ) -> None:
        """Test deleting a model file."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        # Create a test model file
        model_file = models_dir / "test-model.gguf"
        model_file.write_bytes(b"test content")

        # Create manifest with the model
        manifest = LocalModelsManifest()
        model_id = "test/model.gguf"
        manifest.models[model_id] = LocalModelInfo(
            id=model_id,
            repo_id="test/model",
            filename="model.gguf",
            backend=BackendType.LLAMACPP,
            source=DownloadSource.HUGGINGFACE,
            file_size=12,
            local_path=str(model_file),
            display_name="Test Model",
        )
        manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json")),
            encoding="utf-8"
        )

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            delete_local_model(model_id)

        assert not model_file.exists()

        # Verify removed from manifest
        loaded = _load_manifest()
        assert model_id not in loaded.models

    def test_delete_local_model_not_found(
        self, temp_working_dir: Path
    ) -> None:
        """Test deleting a nonexistent model raises error."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
            with pytest.raises(ValueError, match="not found"):
                delete_local_model("nonexistent/model")


class TestLocalModelManager:
    """Tests for LocalModelManager class."""

    def test_auto_select_file_gguf(self) -> None:
        """Test auto-selecting a GGUF file."""
        files = [
            "README.md",
            "config.json",
            "model.Q2_K.gguf",
            "model.Q4_K_M.gguf",
            "model.Q8_0.gguf",
        ]

        result = LocalModelManager._auto_select_file(
            files, BackendType.LLAMACPP
        )

        # Should prefer Q4_K_M
        assert result == "model.Q4_K_M.gguf"

    def test_auto_select_file_gguf_no_q4km(self) -> None:
        """Test auto-selecting GGUF when no Q4_K_M available."""
        files = [
            "model.Q2_K.gguf",
            "model.Q8_0.gguf",
        ]

        result = LocalModelManager._auto_select_file(
            files, BackendType.LLAMACPP
        )

        # Should return first GGUF file
        assert result == "model.Q2_K.gguf"

    def test_auto_select_file_no_gguf(self) -> None:
        """Test auto-selecting when no GGUF files available."""
        files = ["README.md", "config.json"]

        with pytest.raises(ValueError, match="No .gguf files"):
            LocalModelManager._auto_select_file(files, BackendType.LLAMACPP)

    def test_auto_select_file_mlx(self) -> None:
        """Test auto-selecting for MLX backend."""
        files = [
            "config.json",
            "model.safetensors",
            "tokenizer.json",
        ]

        result = LocalModelManager._auto_select_file(files, BackendType.MLX)

        assert result == "model.safetensors"

    def test_auto_select_file_mlx_no_safetensors(self) -> None:
        """Test auto-selecting for MLX when no safetensors available."""
        files = ["config.json", "tokenizer.json"]

        with pytest.raises(ValueError, match="No .safetensors"):
            LocalModelManager._auto_select_file(files, BackendType.MLX)

    def test_validate_mlx_directory(
        self, temp_working_dir: Path
    ) -> None:
        """Test validating an MLX directory."""
        mlx_dir = temp_working_dir / "mlx_model"
        mlx_dir.mkdir(parents=True, exist_ok=True)
        (mlx_dir / "config.json").write_text("{}", encoding="utf-8")
        (mlx_dir / "model.safetensors").write_bytes(b"data")

        # Should not raise
        LocalModelManager._validate_mlx_directory(mlx_dir)

    def test_validate_mlx_directory_missing_config(
        self, temp_working_dir: Path
    ) -> None:
        """Test validating MLX directory without config."""
        mlx_dir = temp_working_dir / "mlx_model"
        mlx_dir.mkdir(parents=True, exist_ok=True)
        (mlx_dir / "model.safetensors").write_bytes(b"data")

        with pytest.raises(RuntimeError, match="missing files"):
            LocalModelManager._validate_mlx_directory(mlx_dir)

    def test_validate_mlx_directory_missing_safetensors(
        self, temp_working_dir: Path
    ) -> None:
        """Test validating MLX directory without safetensors."""
        mlx_dir = temp_working_dir / "mlx_model"
        mlx_dir.mkdir(parents=True, exist_ok=True)
        (mlx_dir / "config.json").write_text("{}", encoding="utf-8")

        with pytest.raises(RuntimeError, match="no .safetensors"):
            LocalModelManager._validate_mlx_directory(mlx_dir)

    def test_register_model_file(
        self, temp_working_dir: Path
    ) -> None:
        """Test registering a model file."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        # Create a test model file
        model_file = models_dir / "test-model.gguf"
        model_file.write_bytes(b"x" * 1000)

        with patch("copaw.local_models.manager.MODELS_DIR", models_dir):
            with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
                result = LocalModelManager._register_model(
                    repo_id="test/model",
                    filename="test-model.gguf",
                    backend=BackendType.LLAMACPP,
                    source=DownloadSource.HUGGINGFACE,
                    downloaded_path=str(model_file),
                )

        assert result.id == "test/model/test-model.gguf"
        assert result.file_size == 1000

        # Verify saved to manifest - load directly from file
        loaded = json.loads(manifest_path.read_text())
        assert result.id in loaded["models"]

    def test_register_model_directory(
        self, temp_working_dir: Path
    ) -> None:
        """Test registering a model directory (MLX style)."""
        models_dir = temp_working_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = models_dir / "manifest.json"

        # Create a test model directory
        model_dir = models_dir / "test-mlx-model"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "config.json").write_text("{}", encoding="utf-8")
        (model_dir / "model.safetensors").write_bytes(b"x" * 2000)

        with patch("copaw.local_models.manager.MODELS_DIR", models_dir):
            with patch("copaw.local_models.manager.MANIFEST_PATH", manifest_path):
                result = LocalModelManager._register_model(
                    repo_id="test/mlx-model",
                    filename="(full repo)",
                    backend=BackendType.MLX,
                    source=DownloadSource.HUGGINGFACE,
                    downloaded_path=str(model_dir),
                )

        assert result.id == "test/mlx-model"
        assert result.file_size == 2000 + 2  # safetensors + config.json

    def test_download_model_sync_unknown_source(self) -> None:
        """Test download with unknown source raises error."""
        with pytest.raises(ValueError, match="Unknown download source"):
            LocalModelManager.download_model_sync(
                repo_id="test/model",
                source="unknown",  # type: ignore
            )
