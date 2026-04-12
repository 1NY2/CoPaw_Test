---
name: test_helper
description: A test skill for verifying skill loading and execution
metadata:
  copaw:
    emoji: "🧪"
    requires: {}
---

# Test Helper Skill

This is a test skill for verifying the skill loading mechanism.

## Purpose

This skill is used in automated tests to verify:
1. Skills are properly discovered from the filesystem
2. Skills are correctly registered to the toolkit
3. Skill content is parsed correctly (YAML front matter)
4. Skill directories are structured properly

## Capabilities

When this skill is loaded, the agent should be able to:
- Access the test_helper functionality
- Process test requests
- Return test responses

## Usage in Tests

This skill is typically used with the test_skill_dir fixture which creates
a complete skill directory structure:

```python
def test_skill_loading(test_skill_dir):
    # Verify skill directory exists
    assert test_skill_dir.exists()
    assert (test_skill_dir / "SKILL.md").exists()
    
    # Verify skill is discoverable
    from copaw.agents.skills_manager import list_available_skills
    skills = list_available_skills()
    assert "test_helper" in skills
```

## Expected Behavior

When asked about testing, the agent should reference this skill's content
and demonstrate that skills are properly loaded and accessible.
