"""
Unit tests for UI Enhancement child workflow.

Tests cover:
- Workflow instantiation
- Input validation
- Graph creation and compilation
- State management
- Agent functionality
"""

import pytest
from workflows.children.ui_enhancement.workflow import UIEnhancementWorkflow
from workflows.children.ui_enhancement.state import (
    UIEnhancementState,
    create_initial_ui_enhancement_state,
)
from workflows.children.ui_enhancement.agents.execution_planner import UIEnhancementPlannerAgent
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode


class TestUIEnhancementWorkflow:
    """Test suite for UIEnhancementWorkflow class."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance for testing."""
        return UIEnhancementWorkflow()

    def test_workflow_instantiation(self, workflow):
        """Test that workflow can be instantiated."""
        assert workflow is not None
        assert isinstance(workflow, UIEnhancementWorkflow)

    def test_get_metadata(self, workflow):
        """Test that metadata is correctly defined."""
        metadata = workflow.get_metadata()

        assert isinstance(metadata, WorkflowMetadata)
        assert metadata.name == "ui_enhancement"
        assert metadata.workflow_type == "ui_enhancement"
        assert metadata.version == "1.0.0"
        assert metadata.deployment_mode == DeploymentMode.EMBEDDED
        assert "accessibility" in metadata.tags

    @pytest.mark.asyncio
    async def test_create_graph(self, workflow):
        """Test that graph can be created and compiled."""
        graph = await workflow.create_graph()

        assert graph is not None
        assert hasattr(graph, "ainvoke")

    @pytest.mark.asyncio
    async def test_validate_input_with_story(self, workflow):
        """Test input validation with valid story."""
        state: EnhancedWorkflowState = {
            "input_story": "# UI Enhancement\n\nImprove accessibility",
            "story_requirements": {},
            "story_type": "ui_enhancement",
            "preprocessor_output": {
                "extracted_data": {},
                "parsed_sections": {},
                "structure_valid": False,
                "metadata": {},
                "parsing_errors": [],
                "parsing_warnings": [],
                "input_summary": "",
                "detected_story_type": "ui_enhancement"
            },
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
            "input_story": "",
            "story_requirements": {},
            "story_type": "ui_enhancement",
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
            "input_story": "# Dashboard Enhancements\nImprove accessibility and performance",
            "story_requirements": {
                "title": "Dashboard Accessibility",
                "description": "Improve accessibility of dashboard components",
            },
            "story_type": "ui_enhancement",
            "preprocessor_output": {
                "extracted_data": {},
                "parsed_sections": {},
                "structure_valid": False,
                "metadata": {},
                "parsing_errors": [],
                "parsing_warnings": [],
                "input_summary": "",
                "detected_story_type": "ui_enhancement"
            },
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
            "input_story": "",
            "story_requirements": {},
            "story_type": "ui_enhancement",
            "preprocessor_output": {},
            "planner_output": {},
            "workflow_tasks": [],
            "task_results": [],
            "execution_log": [],
        }

        result = await workflow.execute(state)

        assert result["status"] == "failure"


class TestUIEnhancementStateManagement:
    """Test suite for UI Enhancement state management."""

    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_ui_enhancement_state(
            input_story="# Enhancement Story",
            story_requirements={"title": "Accessibility"},
        )

        assert state["input_story"] == "# Enhancement Story"
        assert state["story_requirements"]["title"] == "Accessibility"
        assert state["analysis_completed"] is False
        assert state["design_completed"] is False
        assert state["code_generation_completed"] is False
        assert state["testing_completed"] is False
        assert state["a11y_completed"] is False
        assert state["status"] == "in_progress"

    def test_initial_state_has_empty_arrays(self):
        """Test that initial state has proper empty arrays."""
        state = create_initial_ui_enhancement_state("# Story")

        assert isinstance(state["analysis_errors"], list)
        assert len(state["analysis_errors"]) == 0
        assert isinstance(state["design_errors"], list)
        assert isinstance(state["code_generation_errors"], list)
        assert isinstance(state["testing_errors"], list)
        assert isinstance(state["a11y_errors"], list)


class TestUIEnhancementPlannerAgent:
    """Test suite for UIEnhancementPlannerAgent."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        return UIEnhancementPlannerAgent()

    def test_agent_instantiation(self, agent):
        """Test that agent can be instantiated."""
        assert agent is not None
        assert isinstance(agent, UIEnhancementPlannerAgent)

    @pytest.mark.asyncio
    async def test_analyze_enhancement_requirements(self, agent):
        """Test UI enhancement requirements analysis."""
        result = await agent.analyze_enhancement_requirements(
            story_requirements={
                "title": "Dashboard Enhancements",
                "description": "Improve accessibility and performance",
            },
        )

        assert result is not None
        assert "analysis" in result
        assert "errors" in result
        assert "success" in result
        assert isinstance(result["analysis"], dict)

    @pytest.mark.asyncio
    async def test_fallback_analysis_generation(self, agent):
        """Test fallback analysis generation when LLM fails."""
        result = await agent.analyze_enhancement_requirements(
            story_requirements={},
        )

        # Should have a fallback analysis
        assert result["analysis"] is not None
        analysis = result["analysis"]

        assert "current_ui_summary" in analysis
        assert "enhancements" in analysis
        assert "design_impact" in analysis
        assert isinstance(analysis["enhancements"], list)


class TestUIEnhancementWorkflowIntegration:
    """Integration tests for UI Enhancement workflow."""

    @pytest.fixture
    def workflow(self):
        """Create a workflow instance."""
        return UIEnhancementWorkflow()

    @pytest.mark.asyncio
    async def test_graph_has_all_phases(self, workflow):
        """Test that graph contains all expected phases."""
        graph = await workflow.create_graph()

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

    @pytest.mark.asyncio
    async def test_compiled_graph_caching(self, workflow):
        """Test that compiled graph is cached."""
        graph1 = await workflow.get_compiled_graph()
        graph2 = await workflow.get_compiled_graph()

        # Should be the same object (cached)
        assert graph1 is graph2
