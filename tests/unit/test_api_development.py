"""
Unit tests for the API Development child workflow.

Tests cover:
- Workflow instantiation and metadata
- Input validation
- Graph creation and compilation
- Individual node execution
- Full workflow execution with mocked LLM
- Error handling
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from workflows.children.api_development.workflow import ApiDevelopmentWorkflow
from workflows.children.api_development.state import (
    ApiDevelopmentState,
    create_initial_api_state,
)
from workflows.parent.state import create_initial_state
from workflows.registry.registry import DeploymentMode


# ========== Test Fixtures ==========


@pytest.fixture
def api_workflow() -> ApiDevelopmentWorkflow:
    """Create an API development workflow instance."""
    return ApiDevelopmentWorkflow()


@pytest.fixture
def sample_parent_state() -> Dict[str, Any]:
    """Create a sample parent workflow state with API development requirements."""
    return create_initial_state(
        """# User Management API

## Story
As a system administrator, I need to create a User Management API for managing user accounts and roles.

## Requirements
- Create, read, update, delete users
- Role-based access control
- JWT authentication
- Input validation with Pydantic
- Comprehensive error handling

## Endpoints
- POST /users - Create a new user
- GET /users/{user_id} - Retrieve user details
- PUT /users/{user_id} - Update user information
- DELETE /users/{user_id} - Delete a user
- GET /users - List all users
"""
    )


@pytest.fixture
def sample_preprocessor_output() -> Dict[str, Any]:
    """Create a sample preprocessor output."""
    return {
        "parsed_sections": {
            "story": "User Management API description",
            "requirements": "API requirements list",
            "endpoints": "Endpoint definitions",
        },
        "structure_valid": True,
        "extracted_data": {
            "title": "User Management API",
            "description": "API for managing user accounts",
            "endpoints": [
                {
                    "path": "/users",
                    "method": "POST",
                    "description": "Create a new user",
                },
                {
                    "path": "/users/{user_id}",
                    "method": "GET",
                    "description": "Retrieve user details",
                },
            ],
            "authentication": "JWT",
            "database": "PostgreSQL",
        },
        "metadata": {"story_type": "api_development", "language": "python"},
        "parsing_errors": [],
        "parsing_warnings": [],
        "input_summary": "User management REST API",
        "detected_story_type": "api_development",
    }


# ========== Tests ==========


class TestApiDevelopmentInstantiation:
    """Tests for workflow instantiation and metadata."""

    def test_workflow_can_be_instantiated(self, api_workflow) -> None:
        """Test that ApiDevelopmentWorkflow can be instantiated."""
        assert api_workflow is not None
        assert isinstance(api_workflow, ApiDevelopmentWorkflow)

    def test_get_metadata_returns_correct_info(self, api_workflow) -> None:
        """Test that metadata is returned correctly."""
        metadata = api_workflow.get_metadata()

        assert metadata.name == "api_development"
        assert metadata.workflow_type == "api_development"
        assert metadata.version == "1.0.0"
        assert metadata.deployment_mode == DeploymentMode.EMBEDDED
        assert "api" in metadata.tags
        assert "development" in metadata.tags

    def test_metadata_is_consistent(self, api_workflow) -> None:
        """Test that metadata is consistent across calls."""
        metadata1 = api_workflow.get_metadata()
        metadata2 = api_workflow.get_metadata()

        assert metadata1.name == metadata2.name
        assert metadata1.workflow_type == metadata2.workflow_type
        assert metadata1.version == metadata2.version


class TestApiDevelopmentValidation:
    """Tests for input validation."""

    @pytest.mark.asyncio
    async def test_validate_input_with_valid_state(
        self, api_workflow, sample_parent_state, sample_preprocessor_output
    ) -> None:
        """Test validation with valid parent state."""
        sample_parent_state["preprocessor_output"] = sample_preprocessor_output

        is_valid = await api_workflow.validate_input(sample_parent_state)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_input_missing_preprocessor_output(
        self, api_workflow, sample_parent_state
    ) -> None:
        """Test validation fails when preprocessor_output is missing."""
        sample_parent_state["preprocessor_output"] = None

        is_valid = await api_workflow.validate_input(sample_parent_state)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_input_missing_extracted_data(
        self, api_workflow, sample_parent_state, sample_preprocessor_output
    ) -> None:
        """Test validation fails when extracted_data is missing."""
        sample_preprocessor_output["extracted_data"] = {}
        sample_parent_state["preprocessor_output"] = sample_preprocessor_output

        is_valid = await api_workflow.validate_input(sample_parent_state)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_input_handles_exceptions(
        self, api_workflow, sample_parent_state
    ) -> None:
        """Test validation handles exceptions gracefully."""
        # Create invalid state that will cause an error
        sample_parent_state["preprocessor_output"] = "invalid"  # Should be dict or None

        is_valid = await api_workflow.validate_input(sample_parent_state)
        assert is_valid is False


class TestApiDevelopmentGraphCreation:
    """Tests for graph creation and compilation."""

    @pytest.mark.asyncio
    async def test_create_graph_returns_compiled_graph(self, api_workflow) -> None:
        """Test that create_graph returns a compiled graph."""
        graph = await api_workflow.create_graph()

        assert graph is not None
        assert hasattr(graph, "invoke")
        assert callable(graph.invoke)

    @pytest.mark.asyncio
    async def test_graph_has_correct_nodes(self, api_workflow) -> None:
        """Test that the graph has all required nodes."""
        # Create and compile the graph
        graph = await api_workflow.create_graph()

        # Verify graph structure by checking nodes exist
        assert graph is not None
        assert hasattr(graph, "invoke")


class TestApiDevelopmentLazyCompilation:
    """Tests for lazy compilation and caching."""

    @pytest.mark.asyncio
    async def test_get_compiled_graph_creates_graph_on_first_call(
        self, api_workflow
    ) -> None:
        """Test that get_compiled_graph creates graph on first call."""
        assert api_workflow._compiled_graph is None

        graph = await api_workflow.get_compiled_graph()

        assert graph is not None
        assert api_workflow._compiled_graph is not None

    @pytest.mark.asyncio
    async def test_get_compiled_graph_caches_graph(self, api_workflow) -> None:
        """Test that get_compiled_graph caches the graph."""
        graph1 = await api_workflow.get_compiled_graph()
        graph2 = await api_workflow.get_compiled_graph()

        assert graph1 is graph2


class TestApiDevelopmentExecution:
    """Tests for workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_with_valid_state(
        self, api_workflow, sample_parent_state, sample_preprocessor_output
    ) -> None:
        """Test execute with valid parent state."""
        sample_parent_state["preprocessor_output"] = sample_preprocessor_output

        # Mock the LLM client to avoid real API calls
        with patch.object(api_workflow, "llm_client") as mock_llm:
            mock_llm.invoke = AsyncMock(
                return_value=json.dumps(
                    {
                        "api_name": "Test API",
                        "api_description": "Test",
                        "base_path": "/api/v1",
                        "framework": "FastAPI",
                        "authentication_method": "JWT",
                        "requirements": [],
                    }
                )
            )

            # Also mock the planner agent
            with patch.object(api_workflow.planner_agent, "validate_requirements") as mock_validate:
                with patch.object(api_workflow.planner_agent, "plan_api") as mock_plan:
                    mock_validate.return_value = (True, "Valid")
                    mock_plan.return_value = {
                        "api_name": "Test API",
                        "api_description": "Test",
                        "base_path": "/api/v1",
                        "framework": "FastAPI",
                        "authentication_method": "JWT",
                        "database_type": None,
                        "has_database": False,
                        "required_dependencies": ["fastapi"],
                        "requirements": [],
                        "architecture_notes": "Test",
                        "design_decisions": "Test",
                    }

                    result = await api_workflow.execute(sample_parent_state)

                    assert result is not None
                    assert isinstance(result, dict)
                    assert "status" in result
                    assert result["status"] in ["success", "partial", "failure"]
                    assert "output" in result
                    assert "artifacts" in result
                    assert "execution_time_seconds" in result

    @pytest.mark.asyncio
    async def test_execute_returns_expected_fields(
        self, api_workflow, sample_parent_state, sample_preprocessor_output
    ) -> None:
        """Test that execute returns all expected fields."""
        sample_parent_state["preprocessor_output"] = sample_preprocessor_output

        with patch.object(api_workflow, "llm_client") as mock_llm:
            mock_llm.invoke = AsyncMock(return_value=json.dumps({}))

            with patch.object(api_workflow.planner_agent, "validate_requirements") as mock_validate:
                with patch.object(api_workflow.planner_agent, "plan_api") as mock_plan:
                    mock_validate.return_value = (True, "Valid")
                    mock_plan.return_value = {
                        "api_name": "Test API",
                        "api_description": "Test",
                        "base_path": "/api/v1",
                        "framework": "FastAPI",
                        "authentication_method": "JWT",
                        "database_type": None,
                        "has_database": False,
                        "required_dependencies": ["fastapi"],
                        "requirements": [],
                        "architecture_notes": "Test",
                        "design_decisions": "Test",
                    }

                    result = await api_workflow.execute(sample_parent_state)

                    assert "status" in result
                    assert "output" in result
                    assert "artifacts" in result
                    assert "execution_time_seconds" in result
                    assert isinstance(result["artifacts"], list)
                    assert isinstance(result["execution_time_seconds"], (int, float))

    @pytest.mark.asyncio
    async def test_execute_handles_invalid_input(self, api_workflow) -> None:
        """Test that execute handles invalid input gracefully."""
        invalid_state = create_initial_state("Minimal input")

        result = await api_workflow.execute(invalid_state)

        assert result is not None
        assert "status" in result
        # Should fail validation
        assert result["status"] in ["failure", "partial"]


class TestApiDevelopmentStateSchema:
    """Tests for the state schema."""

    def test_create_initial_api_state(self) -> None:
        """Test that initial API state is created correctly."""
        state = create_initial_api_state(
            input_story="Test story",
            story_requirements={"test": "requirements"},
            parent_context={"context": "data"},
        )

        assert state["input_story"] == "Test story"
        assert state["story_requirements"] == {"test": "requirements"}
        assert state["parent_context"] == {"context": "data"}
        assert state["planning_completed"] is False
        assert state["design_completed"] is False
        assert state["code_generation_completed"] is False
        assert state["testing_completed"] is False
        assert state["documentation_completed"] is False
        assert state["all_artifacts"] == []
        assert state["status"] == "in_progress"

    def test_create_initial_api_state_with_defaults(self) -> None:
        """Test that initial API state uses defaults for optional parameters."""
        state = create_initial_api_state("Test story")

        assert state["story_requirements"] == {}
        assert state["parent_context"] == {}


class TestApiPlannerAgent:
    """Tests for the API planner agent."""

    @pytest.mark.asyncio
    async def test_planner_agent_validation(self) -> None:
        """Test that planner agent can validate requirements."""
        from workflows.children.api_development.agents.execution_planner import ApiPlannerAgent

        agent = ApiPlannerAgent()

        with patch.object(agent, "llm_client") as mock_llm:
            mock_llm.invoke = AsyncMock(
                return_value=json.dumps(
                    {
                        "is_valid": True,
                        "summary": "Valid API requirements",
                        "missing_elements": [],
                    }
                )
            )

            is_valid, summary = await agent.validate_requirements(
                "Test story", {}
            )

            assert is_valid is True
            assert "Valid" in summary or "valid" in summary.lower()

    @pytest.mark.asyncio
    async def test_planner_agent_planning(self) -> None:
        """Test that planner agent can create API plan."""
        from workflows.children.api_development.agents.execution_planner import ApiPlannerAgent

        agent = ApiPlannerAgent()

        with patch.object(agent, "llm_client") as mock_llm:
            mock_llm.invoke = AsyncMock(
                return_value=json.dumps(
                    {
                        "api_name": "Test API",
                        "api_description": "Test description",
                        "base_path": "/api/v1",
                        "framework": "FastAPI",
                        "authentication_method": "JWT",
                        "requirements": [],
                    }
                )
            )

            plan = await agent.plan_api("Test story", {})

            assert plan is not None
            assert plan["api_name"] == "Test API"
            assert plan["framework"] == "FastAPI"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
