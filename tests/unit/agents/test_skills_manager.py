# -*- coding: utf-8 -*-
"""Tests for skills_manager module."""
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from copaw.agents.skills_manager import (
    SkillInfo,
    SkillService,
    _build_directory_tree,
    _collect_skills_from_dir,
    _create_files_from_tree,
    _is_directory_same,
    ensure_skills_initialized,
    get_active_skills_dir,
    get_builtin_skills_dir,
    get_customized_skills_dir,
    list_available_skills,
    sync_skills_from_active_to_customized,
    sync_skills_to_working_dir,
)


class TestGetBuiltinSkillsDir:
    """Tests for get_builtin_skills_dir function."""

    def test_get_builtin_skills_dir_returns_path(self) -> None:
        """Test that get_builtin_skills_dir returns a Path object."""
        result = get_builtin_skills_dir()
        assert isinstance(result, Path)

    def test_get_builtin_skills_dir_contains_skills(self) -> None:
        """Test that builtin skills directory contains skill directories."""
        result = get_builtin_skills_dir()
        # The builtin skills directory should exist
        assert result.exists()
        # It should contain at least one skill
        skill_dirs = [d for d in result.iterdir() if d.is_dir()]
        assert len(skill_dirs) > 0


class TestGetCustomizedSkillsDir:
    """Tests for get_customized_skills_dir function."""

    def test_get_customized_skills_dir_with_temp(
        self, temp_working_dir: Path
    ) -> None:
        """Test that get_customized_skills_dir returns the correct path."""
        with patch(
            "copaw.agents.skills_manager.CUSTOMIZED_SKILLS_DIR",
            temp_working_dir / "customized_skills",
        ):
            result = get_customized_skills_dir()
            assert result == temp_working_dir / "customized_skills"

    def test_get_customized_skills_dir_returns_path(self) -> None:
        """Test that get_customized_skills_dir returns a Path object."""
        result = get_customized_skills_dir()
        assert isinstance(result, Path)


class TestGetActiveSkillsDir:
    """Tests for get_active_skills_dir function."""

    def test_get_active_skills_dir_with_temp(
        self, temp_working_dir: Path
    ) -> None:
        """Test that get_active_skills_dir returns the correct path."""
        with patch(
            "copaw.agents.skills_manager.ACTIVE_SKILLS_DIR",
            temp_working_dir / "active_skills",
        ):
            result = get_active_skills_dir()
            assert result == temp_working_dir / "active_skills"

    def test_get_active_skills_dir_returns_path(self) -> None:
        """Test that get_active_skills_dir returns a Path object."""
        result = get_active_skills_dir()
        assert isinstance(result, Path)


class TestBuildDirectoryTree:
    """Tests for _build_directory_tree function."""

    def test_build_directory_tree_empty_dir(
        self, temp_working_dir: Path
    ) -> None:
        """Test building tree from an empty directory."""
        empty_dir = temp_working_dir / "empty"
        empty_dir.mkdir(parents=True, exist_ok=True)

        result = _build_directory_tree(empty_dir)
        assert result == {}

    def test_build_directory_tree_nonexistent_dir(
        self, temp_working_dir: Path
    ) -> None:
        """Test building tree from a nonexistent directory."""
        nonexistent = temp_working_dir / "nonexistent"

        result = _build_directory_tree(nonexistent)
        assert result == {}

    def test_build_directory_tree_with_files(
        self, temp_working_dir: Path
    ) -> None:
        """Test building tree from a directory with files."""
        test_dir = temp_working_dir / "test_dir"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "file1.txt").write_text("content1", encoding="utf-8")
        (test_dir / "file2.py").write_text("content2", encoding="utf-8")

        result = _build_directory_tree(test_dir)

        assert result == {"file1.txt": None, "file2.py": None}

    def test_build_directory_tree_with_nested_dirs(
        self, temp_working_dir: Path
    ) -> None:
        """Test building tree from a directory with nested directories."""
        test_dir = temp_working_dir / "test_dir"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "file1.txt").write_text("content1", encoding="utf-8")

        subdir = test_dir / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / "nested.py").write_text("nested content", encoding="utf-8")

        deeper = subdir / "deeper"
        deeper.mkdir(parents=True, exist_ok=True)
        (deeper / "file.sh").write_text("#!/bin/bash", encoding="utf-8")

        result = _build_directory_tree(test_dir)

        expected = {
            "file1.txt": None,
            "subdir": {
                "nested.py": None,
                "deeper": {
                    "file.sh": None
                }
            }
        }
        assert result == expected


class TestCollectSkillsFromDir:
    """Tests for _collect_skills_from_dir function."""

    def test_collect_skills_empty_dir(self, temp_working_dir: Path) -> None:
        """Test collecting skills from an empty directory."""
        empty_dir = temp_working_dir / "empty"
        empty_dir.mkdir(parents=True, exist_ok=True)

        result = _collect_skills_from_dir(empty_dir)
        assert result == {}

    def test_collect_skills_nonexistent_dir(
        self, temp_working_dir: Path
    ) -> None:
        """Test collecting skills from a nonexistent directory."""
        nonexistent = temp_working_dir / "nonexistent"

        result = _collect_skills_from_dir(nonexistent)
        assert result == {}

    def test_collect_skills_with_valid_skills(
        self, temp_working_dir: Path
    ) -> None:
        """Test collecting skills from a directory with valid skills."""
        skills_dir = temp_working_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Create a valid skill
        skill1 = skills_dir / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill 1", encoding="utf-8")

        # Create another valid skill
        skill2 = skills_dir / "skill2"
        skill2.mkdir(parents=True, exist_ok=True)
        (skill2 / "SKILL.md").write_text("# Skill 2", encoding="utf-8")

        # Create a directory without SKILL.md (should be ignored)
        not_a_skill = skills_dir / "not_a_skill"
        not_a_skill.mkdir(parents=True, exist_ok=True)

        result = _collect_skills_from_dir(skills_dir)

        assert "skill1" in result
        assert "skill2" in result
        assert "not_a_skill" not in result
        assert len(result) == 2


class TestSyncSkillsToWorkingDir:
    """Tests for sync_skills_to_working_dir function."""

    def test_sync_skills_all_empty_source(
        self, temp_working_dir: Path
    ) -> None:
        """Test syncing when source directories are empty."""
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)
        active_skills = temp_working_dir / "active_skills"

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    synced, skipped = sync_skills_to_working_dir()

        assert synced == 0
        assert skipped == 0

    def test_sync_skills_all_from_builtin(
        self, temp_working_dir: Path
    ) -> None:
        """Test syncing all skills from builtin directory."""
        # Create builtin skills
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        skill1 = builtin_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill 1", encoding="utf-8")

        # Create empty customized and active dirs
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)
        active_skills = temp_working_dir / "active_skills"

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    synced, skipped = sync_skills_to_working_dir()

        assert synced == 1
        assert skipped == 0
        assert (active_skills / "skill1").exists()

    def test_sync_skills_selected_only(
        self, temp_working_dir: Path
    ) -> None:
        """Test syncing only selected skills."""
        # Create builtin skills
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        skill1 = builtin_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill 1", encoding="utf-8")

        skill2 = builtin_skills / "skill2"
        skill2.mkdir(parents=True, exist_ok=True)
        (skill2 / "SKILL.md").write_text("# Skill 2", encoding="utf-8")

        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)
        active_skills = temp_working_dir / "active_skills"

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    synced, skipped = sync_skills_to_working_dir(
                        skill_names=["skill1"]
                    )

        assert synced == 1
        assert (active_skills / "skill1").exists()
        assert not (active_skills / "skill2").exists()

    def test_sync_skills_skips_existing(
        self, temp_working_dir: Path
    ) -> None:
        """Test that existing skills are skipped without force."""
        # Create builtin skill
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        skill1 = builtin_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Original", encoding="utf-8")

        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        # Create existing skill in active
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)
        existing = active_skills / "skill1"
        existing.mkdir(parents=True, exist_ok=True)
        (existing / "SKILL.md").write_text("# Existing", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    synced, skipped = sync_skills_to_working_dir()

        assert synced == 0
        assert skipped == 1
        # Content should not be overwritten
        assert "Existing" in (active_skills / "skill1" / "SKILL.md").read_text()

    def test_sync_skills_force_overwrites(
        self, temp_working_dir: Path
    ) -> None:
        """Test that force=True overwrites existing skills."""
        # Create builtin skill
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        skill1 = builtin_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Original", encoding="utf-8")

        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        # Create existing skill in active
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)
        existing = active_skills / "skill1"
        existing.mkdir(parents=True, exist_ok=True)
        (existing / "SKILL.md").write_text("# Existing", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    synced, skipped = sync_skills_to_working_dir(force=True)

        assert synced == 1
        # Content should be overwritten
        assert "Original" in (active_skills / "skill1" / "SKILL.md").read_text()

    def test_sync_skills_customized_overrides_builtin(
        self, temp_working_dir: Path
    ) -> None:
        """Test that customized skills override builtin skills with same name."""
        # Create builtin skill
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        skill1 = builtin_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Builtin", encoding="utf-8")

        # Create customized skill with same name
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        custom_skill1 = customized_skills / "skill1"
        custom_skill1.mkdir(parents=True, exist_ok=True)
        (custom_skill1 / "SKILL.md").write_text("# Customized", encoding="utf-8")

        active_skills = temp_working_dir / "active_skills"

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    synced, skipped = sync_skills_to_working_dir()

        assert synced == 1
        # Should use customized version
        assert "Customized" in (active_skills / "skill1" / "SKILL.md").read_text()


class TestIsDirectorySame:
    """Tests for _is_directory_same function."""

    def test_is_directory_same_identical(
        self, temp_working_dir: Path
    ) -> None:
        """Test that identical directories are detected as same."""
        dir1 = temp_working_dir / "dir1"
        dir1.mkdir(parents=True, exist_ok=True)
        (dir1 / "file.txt").write_text("content", encoding="utf-8")

        dir2 = temp_working_dir / "dir2"
        dir2.mkdir(parents=True, exist_ok=True)
        (dir2 / "file.txt").write_text("content", encoding="utf-8")

        assert _is_directory_same(dir1, dir2) is True

    def test_is_directory_same_different_content(
        self, temp_working_dir: Path
    ) -> None:
        """Test that directories with different content are detected."""
        dir1 = temp_working_dir / "dir1"
        dir1.mkdir(parents=True, exist_ok=True)
        (dir1 / "file.txt").write_text("content1", encoding="utf-8")

        dir2 = temp_working_dir / "dir2"
        dir2.mkdir(parents=True, exist_ok=True)
        (dir2 / "file.txt").write_text("content2", encoding="utf-8")

        assert _is_directory_same(dir1, dir2) is False

    def test_is_directory_same_missing_file(
        self, temp_working_dir: Path
    ) -> None:
        """Test that directories with missing files are detected."""
        dir1 = temp_working_dir / "dir1"
        dir1.mkdir(parents=True, exist_ok=True)
        (dir1 / "file.txt").write_text("content", encoding="utf-8")

        dir2 = temp_working_dir / "dir2"
        dir2.mkdir(parents=True, exist_ok=True)

        assert _is_directory_same(dir1, dir2) is False

    def test_is_directory_same_nonexistent(
        self, temp_working_dir: Path
    ) -> None:
        """Test that nonexistent directories return False."""
        dir1 = temp_working_dir / "dir1"
        dir1.mkdir(parents=True, exist_ok=True)

        dir2 = temp_working_dir / "dir2"  # Doesn't exist

        assert _is_directory_same(dir1, dir2) is False


class TestSyncSkillsFromActiveToCustomized:
    """Tests for sync_skills_from_active_to_customized function."""

    def test_sync_from_active_empty(
        self, temp_working_dir: Path
    ) -> None:
        """Test syncing when active_skills is empty."""
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)
        customized_skills = temp_working_dir / "customized_skills"
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_builtin_skills_dir",
                    return_value=builtin_skills,
                ):
                    synced, skipped = sync_skills_from_active_to_customized()

        assert synced == 0
        assert skipped == 0

    def test_sync_from_active_creates_customized(
        self, temp_working_dir: Path
    ) -> None:
        """Test that skills are copied from active to customized."""
        # Create active skill
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        skill1 = active_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Active Skill", encoding="utf-8")

        customized_skills = temp_working_dir / "customized_skills"
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_builtin_skills_dir",
                    return_value=builtin_skills,
                ):
                    synced, skipped = sync_skills_from_active_to_customized()

        assert synced == 1
        assert (customized_skills / "skill1").exists()

    def test_sync_from_active_skips_unchanged_builtin(
        self, temp_working_dir: Path
    ) -> None:
        """Test that unchanged builtin skills are skipped."""
        # Create identical skill in both active and builtin
        skill_content = "# Builtin Skill\nOriginal content"

        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)
        builtin_skill = builtin_skills / "skill1"
        builtin_skill.mkdir(parents=True, exist_ok=True)
        (builtin_skill / "SKILL.md").write_text(skill_content, encoding="utf-8")

        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)
        active_skill = active_skills / "skill1"
        active_skill.mkdir(parents=True, exist_ok=True)
        (active_skill / "SKILL.md").write_text(skill_content, encoding="utf-8")

        customized_skills = temp_working_dir / "customized_skills"

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_builtin_skills_dir",
                    return_value=builtin_skills,
                ):
                    synced, skipped = sync_skills_from_active_to_customized()

        assert skipped == 1
        assert synced == 0


class TestListAvailableSkills:
    """Tests for list_available_skills function."""

    def test_list_available_skills_empty(
        self, temp_working_dir: Path
    ) -> None:
        """Test listing when no skills are available."""
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            result = list_available_skills()

        assert result == []

    def test_list_available_skills_nonexistent_dir(
        self, temp_working_dir: Path
    ) -> None:
        """Test listing when directory doesn't exist."""
        active_skills = temp_working_dir / "nonexistent"

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            result = list_available_skills()

        assert result == []

    def test_list_available_skills_with_skills(
        self, temp_working_dir: Path
    ) -> None:
        """Test listing available skills."""
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        # Create skills
        skill1 = active_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill 1", encoding="utf-8")

        skill2 = active_skills / "skill2"
        skill2.mkdir(parents=True, exist_ok=True)
        (skill2 / "SKILL.md").write_text("# Skill 2", encoding="utf-8")

        # Create a directory without SKILL.md (should be ignored)
        not_a_skill = active_skills / "not_a_skill"
        not_a_skill.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            result = list_available_skills()

        assert set(result) == {"skill1", "skill2"}


class TestEnsureSkillsInitialized:
    """Tests for ensure_skills_initialized function."""

    def test_ensure_skills_initialized_empty(
        self, temp_working_dir: Path
    ) -> None:
        """Test function runs when no skills are found."""
        active_skills = temp_working_dir / "active_skills"

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.list_available_skills",
                return_value=[],
            ):
                # Should not raise any exception
                ensure_skills_initialized()

    def test_ensure_skills_initialized_with_skills(
        self, temp_working_dir: Path
    ) -> None:
        """Test function runs when skills are found."""
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.list_available_skills",
                return_value=["skill1", "skill2"],
            ):
                # Should not raise any exception
                ensure_skills_initialized()


class TestCreateFilesFromTree:
    """Tests for _create_files_from_tree function."""

    def test_create_files_from_tree_empty(
        self, temp_working_dir: Path
    ) -> None:
        """Test creating files from empty tree."""
        target = temp_working_dir / "target"
        target.mkdir(parents=True, exist_ok=True)

        _create_files_from_tree(target, {})

        assert len(list(target.iterdir())) == 0

    def test_create_files_from_tree_files(
        self, temp_working_dir: Path
    ) -> None:
        """Test creating files from tree with files."""
        target = temp_working_dir / "target"
        target.mkdir(parents=True, exist_ok=True)

        tree = {
            "file1.txt": "content1",
            "file2.py": "content2",
        }

        _create_files_from_tree(target, tree)

        assert (target / "file1.txt").read_text() == "content1"
        assert (target / "file2.py").read_text() == "content2"

    def test_create_files_from_tree_directories(
        self, temp_working_dir: Path
    ) -> None:
        """Test creating files from tree with nested directories."""
        target = temp_working_dir / "target"
        target.mkdir(parents=True, exist_ok=True)

        tree = {
            "subdir": {
                "nested.py": "nested content",
                "deeper": {
                    "file.sh": "#!/bin/bash"
                }
            }
        }

        _create_files_from_tree(target, tree)

        assert (target / "subdir" / "nested.py").read_text() == "nested content"
        assert (target / "subdir" / "deeper" / "file.sh").read_text() == "#!/bin/bash"

    def test_create_files_from_tree_none_value(
        self, temp_working_dir: Path
    ) -> None:
        """Test creating files with None value creates empty file."""
        target = temp_working_dir / "target"
        target.mkdir(parents=True, exist_ok=True)

        tree = {
            "empty.txt": None,
        }

        _create_files_from_tree(target, tree)

        assert (target / "empty.txt").read_text() == ""

    def test_create_files_from_tree_invalid_value(
        self, temp_working_dir: Path
    ) -> None:
        """Test that invalid tree values raise ValueError."""
        target = temp_working_dir / "target"
        target.mkdir(parents=True, exist_ok=True)

        tree = {
            "invalid": 123,  # type: ignore
        }

        with pytest.raises(ValueError, match="Invalid tree value"):
            _create_files_from_tree(target, tree)


class TestSkillService:
    """Tests for SkillService class."""

    def test_list_all_skills(
        self, temp_working_dir: Path
    ) -> None:
        """Test listing all skills from builtin and customized."""
        # Create builtin skill
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)
        skill1 = builtin_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("""---
name: skill1
description: Builtin skill
---
# Skill 1
""", encoding="utf-8")

        # Create customized skill
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)
        skill2 = customized_skills / "skill2"
        skill2.mkdir(parents=True, exist_ok=True)
        (skill2 / "SKILL.md").write_text("""---
name: skill2
description: Custom skill
---
# Skill 2
""", encoding="utf-8")

        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    skills = SkillService.list_all_skills()

        assert len(skills) == 2
        names = [s.name for s in skills]
        assert "skill1" in names
        assert "skill2" in names

    def test_list_available_skills(
        self, temp_working_dir: Path
    ) -> None:
        """Test listing available (active) skills."""
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        skill1 = active_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("""---
name: skill1
description: Active skill
---
# Skill 1
""", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            skills = SkillService.list_available_skills()

        assert len(skills) == 1
        assert skills[0].name == "skill1"
        assert skills[0].source == "active"

    def test_create_skill(
        self, temp_working_dir: Path, sample_skill_content: str
    ) -> None:
        """Test creating a new skill."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.create_skill(
                name="test_skill",
                content=sample_skill_content,
            )

        assert result is True
        assert (customized_skills / "test_skill" / "SKILL.md").exists()

    def test_create_skill_with_files(
        self, temp_working_dir: Path, sample_skill_content: str
    ) -> None:
        """Test creating a skill with references and scripts."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.create_skill(
                name="test_skill",
                content=sample_skill_content,
                references={"doc.md": "# Documentation"},
                scripts={"helper.py": "print('hello')"},
            )

        assert result is True
        assert (customized_skills / "test_skill" / "references" / "doc.md").exists()
        assert (customized_skills / "test_skill" / "scripts" / "helper.py").exists()

    def test_create_skill_invalid_content(
        self, temp_working_dir: Path, sample_skill_content_invalid: str
    ) -> None:
        """Test creating a skill with invalid content fails."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.create_skill(
                name="invalid_skill",
                content=sample_skill_content_invalid,
            )

        assert result is False

    def test_create_skill_missing_fields(
        self, temp_working_dir: Path, sample_skill_content_missing_fields: str
    ) -> None:
        """Test creating a skill with missing required fields fails."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.create_skill(
                name="incomplete_skill",
                content=sample_skill_content_missing_fields,
            )

        assert result is False

    def test_create_skill_already_exists(
        self, temp_working_dir: Path, sample_skill_content: str
    ) -> None:
        """Test creating a skill that already exists fails."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        # Create existing skill
        existing = customized_skills / "test_skill"
        existing.mkdir(parents=True, exist_ok=True)
        (existing / "SKILL.md").write_text("# Existing", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.create_skill(
                name="test_skill",
                content=sample_skill_content,
            )

        assert result is False

    def test_create_skill_overwrite(
        self, temp_working_dir: Path, sample_skill_content: str
    ) -> None:
        """Test overwriting an existing skill."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        # Create existing skill
        existing = customized_skills / "test_skill"
        existing.mkdir(parents=True, exist_ok=True)
        (existing / "SKILL.md").write_text("# Existing", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.create_skill(
                name="test_skill",
                content=sample_skill_content,
                overwrite=True,
            )

        assert result is True
        content = (customized_skills / "test_skill" / "SKILL.md").read_text()
        assert "test_skill" in content

    def test_enable_skill(
        self, temp_working_dir: Path, sample_skill_content: str
    ) -> None:
        """Test enabling a skill."""
        # Create builtin skill
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)
        skill1 = builtin_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text(sample_skill_content, encoding="utf-8")

        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)
        active_skills = temp_working_dir / "active_skills"

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    result = SkillService.enable_skill("skill1")

        assert result is True
        assert (active_skills / "skill1").exists()

    def test_enable_skill_not_found(
        self, temp_working_dir: Path
    ) -> None:
        """Test enabling a skill that doesn't exist."""
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)
        active_skills = temp_working_dir / "active_skills"

        with patch(
            "copaw.agents.skills_manager.get_builtin_skills_dir",
            return_value=builtin_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_active_skills_dir",
                    return_value=active_skills,
                ):
                    result = SkillService.enable_skill("nonexistent")

        assert result is False

    def test_disable_skill(
        self, temp_working_dir: Path
    ) -> None:
        """Test disabling a skill."""
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        skill1 = active_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill 1", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            result = SkillService.disable_skill("skill1")

        assert result is True
        assert not skill1.exists()

    def test_disable_skill_not_found(
        self, temp_working_dir: Path
    ) -> None:
        """Test disabling a skill that doesn't exist."""
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            result = SkillService.disable_skill("nonexistent")

        assert result is False

    def test_delete_skill(
        self, temp_working_dir: Path
    ) -> None:
        """Test deleting a skill from customized_skills."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        skill1 = customized_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill 1", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.delete_skill("skill1")

        assert result is True
        assert not skill1.exists()

    def test_delete_skill_not_found(
        self, temp_working_dir: Path
    ) -> None:
        """Test deleting a skill that doesn't exist."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.delete_skill("nonexistent")

        assert result is False

    def test_load_skill_file(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading a file from a skill."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        skill1 = customized_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill", encoding="utf-8")

        refs = skill1 / "references"
        refs.mkdir(parents=True, exist_ok=True)
        (refs / "doc.md").write_text("# Documentation", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            content = SkillService.load_skill_file(
                "skill1",
                "references/doc.md",
                "customized",
            )

        assert content == "# Documentation"

    def test_load_skill_file_invalid_source(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading a file with invalid source."""
        result = SkillService.load_skill_file(
            "skill1",
            "references/doc.md",
            "invalid",
        )

        assert result is None

    def test_load_skill_file_invalid_path(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading a file with invalid path (not starting with references/ or scripts/)."""
        result = SkillService.load_skill_file(
            "skill1",
            "invalid/path.md",
            "customized",
        )

        assert result is None

    def test_load_skill_file_path_traversal(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading a file with path traversal attempt."""
        result = SkillService.load_skill_file(
            "skill1",
            "references/../../../etc/passwd",
            "customized",
        )

        assert result is None

    def test_load_skill_file_skill_not_found(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading a file from a nonexistent skill."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.load_skill_file(
                "nonexistent",
                "references/doc.md",
                "customized",
            )

        assert result is None

    def test_load_skill_file_file_not_found(
        self, temp_working_dir: Path
    ) -> None:
        """Test loading a nonexistent file from a skill."""
        customized_skills = temp_working_dir / "customized_skills"
        customized_skills.mkdir(parents=True, exist_ok=True)

        skill1 = customized_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Skill", encoding="utf-8")

        with patch(
            "copaw.agents.skills_manager.get_customized_skills_dir",
            return_value=customized_skills,
        ):
            result = SkillService.load_skill_file(
                "skill1",
                "references/nonexistent.md",
                "customized",
            )

        assert result is None

    def test_sync_from_active_to_customized(
        self, temp_working_dir: Path
    ) -> None:
        """Test syncing skills from active to customized via SkillService."""
        # Create active skill
        active_skills = temp_working_dir / "active_skills"
        active_skills.mkdir(parents=True, exist_ok=True)

        skill1 = active_skills / "skill1"
        skill1.mkdir(parents=True, exist_ok=True)
        (skill1 / "SKILL.md").write_text("# Active Skill", encoding="utf-8")

        customized_skills = temp_working_dir / "customized_skills"
        builtin_skills = temp_working_dir / "builtin_skills"
        builtin_skills.mkdir(parents=True, exist_ok=True)

        with patch(
            "copaw.agents.skills_manager.get_active_skills_dir",
            return_value=active_skills,
        ):
            with patch(
                "copaw.agents.skills_manager.get_customized_skills_dir",
                return_value=customized_skills,
            ):
                with patch(
                    "copaw.agents.skills_manager.get_builtin_skills_dir",
                    return_value=builtin_skills,
                ):
                    synced, skipped = SkillService.sync_from_active_to_customized()

        assert synced == 1


class TestSkillInfo:
    """Tests for SkillInfo model."""

    def test_skill_info_defaults(self) -> None:
        """Test SkillInfo default values."""
        info = SkillInfo(
            name="test",
            content="# Test",
            source="builtin",
            path="/path/to/skill",
        )

        assert info.name == "test"
        assert info.content == "# Test"
        assert info.source == "builtin"
        assert info.path == "/path/to/skill"
        assert info.references == {}
        assert info.scripts == {}

    def test_skill_info_with_trees(self) -> None:
        """Test SkillInfo with reference and script trees."""
        info = SkillInfo(
            name="test",
            content="# Test",
            source="customized",
            path="/path/to/skill",
            references={"doc.md": None},
            scripts={"helper.py": None},
        )

        assert info.references == {"doc.md": None}
        assert info.scripts == {"helper.py": None}
