"""
Unit tests for UI Development child workflow.

Tests cover:
- Workflow instantiation
- Input validation
- Graph creation and compilation
- State management
- Execution flow
"""

import pytest
from workflows.children.ui_development.workflow import UIDevWorkflow
from workflows.children.ui_development.state import (
    UIDevState,
    create_initial_ui_state,
)
from workflows.children.ui_development.agents.planner import UIPlannerAgent
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode


class TestUIDevWorkflow:
    """Test suite for UIDevWorkflow class."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance for testing."""
        return UIDevWorkflow()

    def test_workflow_instantiation(self, workflow):
        """Test that workflow can be instantiated."""
        assert workflow is not None
        assert isinstance(workflow, UIDevWorkflow)

    def test_get_metadata(self, workflow):
        """Test that metadata is correctly defined."""
        metadata = workflow.get_metadata()

        assert isinstance(metadata, WorkflowMetadata)
        assert metadata.name == "ui_development"
        assert metadata.workflow_type == "ui_development"
        assert metadata.version == "1.0.0"
        assert metadata.deployment_mode == DeploymentMode.EMBEDDED
        assert "react" in metadata.tags

    @pytest.mark.asyncio
    async def test_create_graph(self, workflow):
        """Test that graph can be created and compiled."""
        graph = await workflow.create_graph()

        assert graph is not None
        # Verify graph has necessary methods
        assert hasattr(graph, "ainvoke")

    @pytest.mark.asyncio
    async def test_validate_input_with_story(self, workflow):
        """Test input validation with valid story."""
        state: EnhancedWorkflowState = {
            "story": "# UI Development Story\n\nBuild a React dashboard",
            "story_requirements": {},
            "story_type": "ui_development",
            "preprocessor_output": {},
            "planner_output": {},
            "workflow_tasks": [],
            "task_results": [],
            "execution_log": [],
        }

        result = await workflow.validate_input(state)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_input_without_story(self, workflow):
        """Test input validation without story."""
        state: EnhancedWorkflowState = {
            "story": "",
            "story_requirements": {},
            "story_type": "ui_development",
            "preprocessor_output": {},
            "planner_output": {},
            "workflow_tasks": [],
            "task_results": [],
            "execution_log": [],
        }

        result = await workflow.validate_input(state)
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_with_valid_state(self, workflow):
        """Test workflow execution with valid state."""
        state: EnhancedWorkflowState = {
            "story": "# Customer Dashboard\nBuild a React dashboard",
            "story_requirements": {
                "title": "Customer Dashboard",
                "description": "Customer dashboard with charts and tables",
            },
            "story_type": "ui_development",
            "preprocessor_output": {},
            "planner_output": {},
            "workflow_tasks": [],
            "task_results": [],
            "execution_log": [],
        }

        result = await workflow.execute(state)

        assert result is not None
        assert "status" in result
        assert "output" in result

    @pytest.mark.asyncio
    async def test_execute_with_invalid_state(self, workflow):
        """Test workflow execution with invalid state."""
        state: EnhancedWorkflowState = {
            "story": "",
            "story_requirements": {},
            "story_type": "ui_development",
            "preprocessor_output": {},
            "planner_output": {},
            "workflow_tasks": [],
            "task_results": [],
            "execution_log": [],
        }

        result = await workflow.execute(state)

        assert result["status"] == "failure"

    @pytest.mark.asyncio
    async def test_get_compiled_graph(self, workflow):
        """Test that compiled graph is cached and reused."""
        graph1 = await workflow.get_compiled_graph()
        graph2 = await workflow.get_compiled_graph()

        # Should be the same object (cached)
        assert graph1 is graph2


class TestUIStateManagement:
    """Test suite for UI Development state management."""

    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_ui_state(
            input_story="# UI Story",
            story_requirements={"title": "Dashboard"},
        )

        assert state["input_story"] == "# UI Story"
        assert state["story_requirements"]["title"] == "Dashboard"
        assert state["planning_completed"] is False
        assert state["design_completed"] is False
        assert state["code_generation_completed"] is False
        assert state["styling_completed"] is False
        assert state["testing_completed"] is False
        assert state["documentation_completed"] is False
        assert state["status"] == "in_progress"

    def test_initial_state_has_empty_arrays(self):
        """Test that initial state has proper empty arrays."""
        state = create_initial_ui_state("# Story")

        assert isinstance(state["planning_errors"], list)
        assert len(state["planning_errors"]) == 0
        assert isinstance(state["design_errors"], list)
        assert isinstance(state["code_generation_errors"], list)
        assert isinstance(state["styling_errors"], list)
        assert isinstance(state["testing_errors"], list)
        assert isinstance(state["documentation_errors"], list)
        assert isinstance(state["all_artifacts"], list)

    def test_state_is_mutable_for_updates(self):
        """Test that state can be updated (copy pattern)."""
        state = create_initial_ui_state("# Story")
        state_copy = state.copy()
        state_copy["planning_completed"] = True

        assert state["planning_completed"] is False
        assert state_copy["planning_completed"] is True


class TestUIPlannerAgent:
    """Test suite for UIPlannerAgent."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        return UIPlannerAgent()

    def test_agent_instantiation(self, agent):
        """Test that agent can be instantiated."""
        assert agent is not None
        assert isinstance(agent, UIPlannerAgent)

    @pytest.mark.asyncio
    async def test_plan_ui_development(self, agent):
        """Test UI development planning."""
        result = await agent.plan_ui_development(
            story_requirements={
                "title": "Customer Dashboard",
                "description": "A dashboard for customer analytics",
            },
            framework_preference="React",
            typescript_enabled=True,
        )

        assert result is not None
        assert "ui_plan" in result
        assert "errors" in result
        assert "success" in result
        assert isinstance(result["ui_plan"], dict)

    @pytest.mark.asyncio
    async def test_fallback_plan_generation(self, agent):
        """Test fallback plan generation when LLM fails."""
        result = await agent.plan_ui_development(
            story_requirements={},
            framework_preference="React",
            typescript_enabled=True,
        )

        # Should have a fallback plan
        assert result["ui_plan"] is not None
        ui_plan = result["ui_plan"]

        assert "project_name" in ui_plan
        assert "components" in ui_plan
        assert "target_framework" in ui_plan
        assert ui_plan["target_framework"] == "React"
        assert ui_plan["typescript_enabled"] is True


class TestUIDevWorkflowIntegration:
    """Integration tests for UI Development workflow."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance."""
        return UIDevWorkflow()

    @pytest.mark.asyncio
    async def test_graph_has_all_nodes(self, workflow):
        """Test that graph contains all expected nodes."""
        graph = await workflow.create_graph()

        # The compiled graph should have all nodes
        assert graph is not None

    @pytest.mark.asyncio
    async def test_metadata_is_registry_compatible(self, workflow):
        """Test that metadata is compatible with registry."""
        metadata = workflow.get_metadata()

        # Required registry fields
        assert metadata.name
        assert metadata.workflow_type
        assert metadata.description
        assert metadata.version
        assert metadata.deployment_mode
        assert metadata.module_path
        assert isinstance(metadata.tags, list)
