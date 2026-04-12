# -*- coding: utf-8 -*-
"""Fixtures for Agents module tests."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def mock_builtin_skills_dir(temp_working_dir: Path) -> Generator[Path, None, None]:
    """Create a mock builtin skills directory with sample skills.

    Args:
        temp_working_dir: Temporary working directory fixture

    Yields:
        Path to the mock builtin skills directory
    """
    # Create a mock builtin skills directory
    builtin_skills = temp_working_dir / "builtin_skills"
    builtin_skills.mkdir(parents=True, exist_ok=True)

    # Create a sample skill
    skill1_dir = builtin_skills / "skill1"
    skill1_dir.mkdir(parents=True, exist_ok=True)
    (skill1_dir / "SKILL.md").write_text("""---
name: skill1
description: Test skill 1
---

# Skill 1

This is test skill 1.
""", encoding="utf-8")

    # Create skill with references and scripts
    skill2_dir = builtin_skills / "skill2"
    skill2_dir.mkdir(parents=True, exist_ok=True)
    (skill2_dir / "SKILL.md").write_text("""---
name: skill2
description: Test skill 2
---

# Skill 2

This is test skill 2.
""", encoding="utf-8")

    # Add references
    ref_dir = skill2_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "doc.md").write_text("# Documentation\n", encoding="utf-8")

    # Add scripts
    scripts_dir = skill2_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "helper.py").write_text("print('hello')\n", encoding="utf-8")

    yield builtin_skills


@pytest.fixture
def mock_customized_skills_dir(temp_working_dir: Path) -> Generator[Path, None, None]:
    """Create a mock customized skills directory.

    Args:
        temp_working_dir: Temporary working directory fixture

    Yields:
        Path to the mock customized skills directory
    """
    customized_skills = temp_working_dir / "customized_skills"
    customized_skills.mkdir(parents=True, exist_ok=True)

    # Create a custom skill
    skill_dir = customized_skills / "custom_skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("""---
name: custom_skill
description: A custom skill
---

# Custom Skill

This is a customized skill.
""", encoding="utf-8")

    yield customized_skills


@pytest.fixture
def mock_active_skills_dir(temp_working_dir: Path) -> Generator[Path, None, None]:
    """Create a mock active skills directory.

    Args:
        temp_working_dir: Temporary working directory fixture

    Yields:
        Path to the mock active skills directory
    """
    active_skills = temp_working_dir / "active_skills"
    active_skills.mkdir(parents=True, exist_ok=True)

    # Create an active skill
    skill_dir = active_skills / "active_skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("""---
name: active_skill
description: An active skill
---

# Active Skill

This is an active skill.
""", encoding="utf-8")

    yield active_skills


@pytest.fixture
def sample_skill_content() -> str:
    """Return sample SKILL.md content for testing.

    Returns:
        String containing sample SKILL.md content with YAML front matter
    """
    return """---
name: test_skill
description: A test skill for unit testing
---

# Test Skill

This is a test skill for unit testing purposes.

## Usage

- Step 1: Do something
- Step 2: Do another thing
"""


@pytest.fixture
def sample_skill_content_invalid() -> str:
    """Return invalid SKILL.md content for testing.

    Returns:
        String containing invalid SKILL.md content
    """
    return """# Invalid Skill

This skill has no YAML front matter.
"""


@pytest.fixture
def sample_skill_content_missing_fields() -> str:
    """Return SKILL.md content with missing required fields.

    Returns:
        String containing SKILL.md content with missing fields
    """
    return """---
name: incomplete_skill
---

# Incomplete Skill

This skill is missing the description field.
"""
