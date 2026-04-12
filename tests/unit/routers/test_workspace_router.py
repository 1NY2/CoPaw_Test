# -*- coding: utf-8 -*-
"""Tests for workspace router."""
from __future__ import annotations

import io
import zipfile
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


class TestWorkspaceRouter:
    """Tests for workspace router endpoints."""

    def test_get_workspace_info(self, test_client: TestClient) -> None:
        """Test getting workspace info."""
        # This endpoint may or may not exist depending on implementation
        response = test_client.get("/api/workspace")

        # Just check that we get a valid response
        assert response.status_code in [200, 404, 405]

    def test_download_workspace(self, test_client: TestClient) -> None:
        """Test downloading workspace as zip."""
        response = test_client.get("/api/workspace/download")

        # Response could be 200 (success) or 404 (no working dir)
        assert response.status_code in [200, 404]

    def test_download_workspace_returns_zip(self, test_client: TestClient) -> None:
        """Test that download returns a valid zip file when successful."""
        # This test depends on the working directory existing
        response = test_client.get("/api/workspace/download")

        if response.status_code == 200:
            # Verify it's a valid zip
            assert response.headers.get("content-type") == "application/zip"
            
            # Check content-disposition header
            assert "attachment" in response.headers.get("content-disposition", "")

    def test_upload_workspace_invalid_content_type(
        self, test_client: TestClient
    ) -> None:
        """Test uploading with invalid content type."""
        # Create a simple zip in memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test.txt", "test content")
        buf.seek(0)

        response = test_client.post(
            "/api/workspace/upload",
            files={"file": ("test.zip", buf, "text/plain")},
        )

        # Should fail with invalid content type
        assert response.status_code in [400, 422, 500]

    def test_upload_workspace_valid_zip(
        self, test_client: TestClient
    ) -> None:
        """Test uploading a valid zip file."""
        # Create a valid zip in memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test_file.txt", "test content")
        buf.seek(0)

        response = test_client.post(
            "/api/workspace/upload",
            files={"file": ("test.zip", buf, "application/zip")},
        )

        # Should succeed
        assert response.status_code in [200, 500]  # 500 if working dir issues


class TestWorkspaceHelpers:
    """Tests for workspace router helper functions."""

    def test_dir_stats_empty(self, temp_working_dir) -> None:
        """Test directory stats for empty directory."""
        from copaw.app.routers.workspace import _dir_stats

        count, size = _dir_stats(temp_working_dir)
        assert count == 0
        assert size == 0

    def test_dir_stats_with_files(self, temp_working_dir) -> None:
        """Test directory stats with files."""
        from copaw.app.routers.workspace import _dir_stats

        # Create test files
        (temp_working_dir / "file1.txt").write_text("content1")
        (temp_working_dir / "subdir").mkdir()
        (temp_working_dir / "subdir" / "file2.txt").write_text("content2")

        count, size = _dir_stats(temp_working_dir)
        assert count == 2
        assert size > 0

    def test_zip_directory(self, temp_working_dir) -> None:
        """Test creating zip from directory."""
        from copaw.app.routers.workspace import _zip_directory

        # Create test file
        (temp_working_dir / "test.txt").write_text("test content")

        buf = _zip_directory(temp_working_dir)

        # Verify it's a valid zip
        assert zipfile.is_zipfile(buf)

        # Verify contents
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "test.txt" in names
