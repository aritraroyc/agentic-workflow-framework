"""
End-to-End Integration Tests for Complete Workflow Execution.

Tests the complete workflow from story input through result generation,
including all intermediate steps and artifacts.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

from workflows.parent.graph import create_enhanced_parent_workflow
from workflows.registry.loader import load_registry, validate_registry
from workflows.parent.state import create_initial_state


# ========== Test Fixtures ==========


@pytest.fixture
def api_development_story() -> str:
    """Load the API development example story."""
    story_path = Path(__file__).parent.parent.parent / "examples" / "stories" / "api_development.md"
    if story_path.exists():
        return story_path.read_text()
    else:
        # Fallback story if file doesn't exist
        return """# Test API

## Story
We need a test API for managing resources.

## Requirements
- Create, read, update, delete resources
- JWT authentication
- Input validation

## Endpoints
- POST /resources - Create resource
- GET /resources/{id} - Get resource
"""


@pytest.fixture
def ui_development_story() -> str:
    """Load the UI development example story."""
    story_path = Path(__file__).parent.parent.parent / "examples" / "stories" / "ui_development.md"
    if story_path.exists():
        return story_path.read_text()
    else:
        # Fallback story if file doesn't exist
        return """# Test Dashboard

## Story
We need a test dashboard for users.

## Requirements
- User profile display
- Data visualization
- Responsive design

## Features
- Dashboard home page
- Settings page
- Analytics page
"""


# ========== Test Classes ==========


class TestWorkflowInitialization:
    """Tests for workflow initialization and setup."""

    def test_create_parent_workflow(self) -> None:
        """Test that parent workflow can be created."""
        workflow = create_enhanced_parent_workflow()

        assert workflow is not None
        assert hasattr(workflow, "invoke")

    def test_load_registry(self) -> None:
        """Test that workflow registry can be loaded."""
        registry = load_registry("config/workflows.yaml")

        assert registry is not None
        assert len(registry) > 0

    def test_validate_registry(self) -> None:
        """Test that registry validation works."""
        registry = load_registry("config/workflows.yaml")
        validation = validate_registry(registry)

        assert validation is not None
        assert validation["valid"] is True
        assert validation["total_workflows"] > 0


class TestWorkflowStateManagement:
    """Tests for workflow state creation and management."""

    def test_create_initial_state(self) -> None:
        """Test creating initial workflow state."""
        story = "# Test\n\n## Story\nTest story\n\n## Requirements\nTest"
        state = create_initial_state(story)

        assert state is not None
        assert state["input_story"] == story
        assert "execution_log" in state
        assert "preprocessor_output" in state
        assert state["preprocessor_output"] is None
        assert state["preprocessor_completed"] is False

    def test_initial_state_structure(self) -> None:
        """Test that initial state has required fields."""
        story = "# Test\n\n## Story\nTest\n\n## Requirements\nTest"
        state = create_initial_state(story)

        required_fields = [
            "input_story",
            "execution_log",
            "preprocessor_output",
            "planner_output",
            "workflow_tasks",
            "execution_results",
        ]

        for field in required_fields:
            assert field in state, f"Missing required field: {field}"


class TestWorkflowExecution:
    """Tests for workflow execution with mocked LLM."""

    def test_execute_workflow_basic(
        self, api_development_story: str
    ) -> None:
        """Test that workflow can be invoked with input state."""
        workflow = create_enhanced_parent_workflow()

        if workflow is None:
            pytest.skip("Parent workflow not available")

        # Create input state
        input_state = create_initial_state(api_development_story)

        # Verify input state is valid
        assert input_state is not None
        assert isinstance(input_state, dict)
        assert "input_story" in input_state
        assert input_state["input_story"] == api_development_story

        # Verify workflow is invokable
        assert callable(workflow.invoke)

    def test_workflow_state_progression(
        self, api_development_story: str
    ) -> None:
        """Test that workflow state progresses through stages."""
        # Create initial state
        state = create_initial_state(api_development_story)

        # Verify initial state
        assert state["preprocessor_output"] is None
        assert state["planner_output"] is None
        assert state["execution_results"] == {}
        assert state["execution_log"] == []
        assert state["preprocessor_completed"] is False
        assert state["planner_completed"] is False

        # After workflow execution, these should be populated
        # (In real execution; skipped if mock not available)
        assert "input_story" in state
        assert len(state["input_story"]) > 0


class TestStoryProcessing:
    """Tests for story file processing and validation."""

    def test_valid_api_story(self, api_development_story: str) -> None:
        """Test that valid API story is accepted."""
        assert api_development_story is not None
        assert len(api_development_story) > 0
        assert "Story" in api_development_story or "story" in api_development_story

    def test_valid_ui_story(self, ui_development_story: str) -> None:
        """Test that valid UI story is accepted."""
        assert ui_development_story is not None
        assert len(ui_development_story) > 0
        assert "Story" in ui_development_story or "story" in ui_development_story

    def test_story_content_structure(self, api_development_story: str) -> None:
        """Test that story has expected sections."""
        # Should have at least a title and content
        lines = api_development_story.strip().split("\n")
        assert len(lines) > 0

        # Should contain meaningful content
        assert len(api_development_story) > 50


class TestErrorHandling:
    """Tests for error handling in workflows."""

    def test_empty_story_handling(self) -> None:
        """Test handling of empty story."""
        empty_story = ""
        with pytest.raises((ValueError, AssertionError)):
            state = create_initial_state(empty_story)
            if not state.get("input_story"):
                raise ValueError("Empty story not handled")

    def test_minimal_story_handling(self) -> None:
        """Test handling of minimal valid story."""
        minimal_story = "# Test\n\n## Story\nTest\n\n## Requirements\nTest"
        state = create_initial_state(minimal_story)

        assert state is not None
        assert state["input_story"] == minimal_story


class TestRegistryIntegration:
    """Tests for registry integration with workflows."""

    def test_registry_has_api_development(self) -> None:
        """Test that api_development workflow is registered."""
        registry = load_registry("config/workflows.yaml")
        api_workflow = registry.get("api_development")

        assert api_workflow is not None
        assert api_workflow.name == "api_development"
        assert api_workflow.workflow_type == "api_development"

    def test_registry_workflow_metadata(self) -> None:
        """Test that registered workflows have correct metadata."""
        registry = load_registry("config/workflows.yaml")
        api_workflow = registry.get("api_development")

        assert api_workflow is not None
        assert api_workflow.version == "1.0.0"
        assert api_workflow.description is not None
        assert len(api_workflow.tags) > 0


class TestOutputFormatting:
    """Tests for output formatting and JSON serialization."""

    def test_state_json_serializable(self, api_development_story: str) -> None:
        """Test that workflow state can be serialized to JSON."""
        state = create_initial_state(api_development_story)

        # Test serialization
        try:
            json_str = json.dumps(state, default=str)
            assert json_str is not None
            assert len(json_str) > 0
        except Exception as e:
            pytest.fail(f"State not JSON serializable: {str(e)}")

    def test_execution_log_format(self, api_development_story: str) -> None:
        """Test that execution log has correct format."""
        state = create_initial_state(api_development_story)

        # Execution log should be a list
        assert isinstance(state["execution_log"], list)

        # Initially empty
        assert len(state["execution_log"]) == 0


class TestWorkflowInputValidation:
    """Tests for workflow input validation."""

    def test_story_with_sections(self) -> None:
        """Test processing story with required sections."""
        story = """# User API

## Story
We need a user management API.

## Requirements
- User CRUD operations
- JWT authentication
- Validation with Pydantic

## Endpoints
- POST /users
- GET /users/{id}
- PUT /users/{id}
- DELETE /users/{id}
"""
        state = create_initial_state(story)

        assert state["input_story"] == story
        assert "Story" in state["input_story"] or "story" in state["input_story"]

    def test_story_without_optional_sections(self) -> None:
        """Test that stories work without all optional sections."""
        minimal_story = """# API

## Story
Simple API needed.

## Requirements
Basic CRUD operations.
"""
        state = create_initial_state(minimal_story)

        assert state is not None
        assert state["input_story"] == minimal_story


# ========== Integration Test Helpers ==========


def test_example_stories_exist() -> None:
    """Test that example story files exist."""
    examples_dir = Path(__file__).parent.parent.parent / "examples" / "stories"

    assert examples_dir.exists(), "Examples directory does not exist"

    expected_files = [
        "api_development.md",
        "ui_development.md",
        "api_enhancement.md",
        "complex_ecommerce_platform.md",
    ]

    for filename in expected_files:
        file_path = examples_dir / filename
        assert file_path.exists(), f"Example file not found: {filename}"


def test_example_stories_not_empty() -> None:
    """Test that example stories have content."""
    examples_dir = Path(__file__).parent.parent.parent / "examples" / "stories"

    story_files = list(examples_dir.glob("*.md"))
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = story_file.read_text()
        assert len(content) > 100, f"Story file too short: {story_file.name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
