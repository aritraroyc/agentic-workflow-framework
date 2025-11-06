"""
Unit tests for the BaseChildWorkflow abstract base class.

Tests cover:
- Abstract method enforcement
- Lazy compilation and caching
- Interface contract validation
- Mock implementations
"""

import pytest
from typing import Dict, Any, TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from workflows.children.base import BaseChildWorkflow
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode


# ========== Test Fixtures ==========


class MockChildState(TypedDict, total=False):
    """State for mock child workflow."""
    input_data: str
    output_data: str
    status: str


class MockChildWorkflow(BaseChildWorkflow):
    """
    Mock implementation of BaseChildWorkflow for testing.

    This mock implements all abstract methods with simple test logic.
    """

    def get_metadata(self) -> WorkflowMetadata:
        """Return metadata for mock workflow."""
        return WorkflowMetadata(
            name="mock_workflow",
            workflow_type="mock",
            description="Mock workflow for testing",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="tests.unit.test_base_workflow",
            tags=["mock", "test"],
        )

    async def create_graph(self):
        """Create a simple mock graph."""

        def mock_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Simple mock node (sync for LangGraph)."""
            state["output_data"] = f"Processed: {state.get('input_data', '')}"
            state["status"] = "completed"
            return state

        graph = StateGraph(MockChildState)
        graph.add_node("process", mock_node)
        graph.set_entry_point("process")
        graph.set_finish_point("process")
        return graph.compile()

    async def validate_input(self, state: EnhancedWorkflowState) -> bool:
        """Validate that state has required fields."""
        return bool(state.get("preprocessor_output"))

    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """Execute the mock workflow."""
        if not await self.validate_input(state):
            raise ValueError("Missing preprocessor_output")

        graph = await self.get_compiled_graph()

        # Map parent state to child state
        child_state: MockChildState = {
            "input_data": state.get("preprocessor_output", {}).get("story_scope", ""),
            "output_data": "",
            "status": "pending",
        }

        result = graph.invoke(child_state)

        return {
            "status": "success",
            "output": result,
            "artifacts": [],
            "execution_time_seconds": 0.1,
        }


class IncompleteWorkflow(BaseChildWorkflow):
    """Incomplete workflow missing execute method (for testing abstract enforcement)."""

    def get_metadata(self) -> WorkflowMetadata:
        return WorkflowMetadata(
            name="incomplete",
            workflow_type="incomplete",
            description="Incomplete workflow",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="tests.unit.test_base_workflow",
        )

    async def create_graph(self):
        graph = StateGraph(MockChildState)
        graph.set_entry_point(START)
        graph.set_finish_point(END)
        return graph.compile()

    async def validate_input(self, state: EnhancedWorkflowState) -> bool:
        return True

    # Missing: execute() method - intentionally left out to test abstract enforcement


@pytest.fixture
def mock_workflow() -> MockChildWorkflow:
    """Create a mock workflow instance."""
    return MockChildWorkflow()


@pytest.fixture
def sample_parent_state() -> EnhancedWorkflowState:
    """Create a sample parent workflow state."""
    return {
        "input_story": "Test story",
        "preprocessor_output": {
            "story_scope": "Test API development",
            "required_sections": ["Story", "Requirements"],
            "metadata": {"story_type": "api_development"},
            "warnings": [],
            "errors": [],
        },
        "planner_output": {
            "story_scope": "Test API development",
            "required_workflows": ["api_development"],
            "workflow_tasks": [],
            "task_dependencies": {},
            "execution_strategy": "sequential",
            "execution_order": [],
            "risk_factors": [],
            "estimated_total_effort_hours": 8.0,
            "planning_rationale": "Simple test",
            "planning_errors": [],
        },
        "coordinator_output": {
            "workflow_results": [],
            "execution_strategy_used": "sequential",
            "total_execution_time_seconds": 0.0,
            "overall_status": "pending",
        },
        "execution_log": [],
        "status": "in_progress",
        "context": {},
    }


# ========== Tests ==========


class TestBaseChildWorkflowAbstractness:
    """Tests for abstract method enforcement."""

    def test_cannot_instantiate_base_class_directly(self) -> None:
        """Test that BaseChildWorkflow cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseChildWorkflow()  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_incomplete_implementation_cannot_instantiate(self) -> None:
        """Test that incomplete implementations cannot be instantiated."""
        with pytest.raises(TypeError) as exc_info:
            IncompleteWorkflow()  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_complete_implementation_can_instantiate(self, mock_workflow) -> None:
        """Test that complete implementations can be instantiated."""
        assert mock_workflow is not None
        assert isinstance(mock_workflow, BaseChildWorkflow)


class TestMetadataInterface:
    """Tests for get_metadata() method."""

    def test_get_metadata_returns_workflow_metadata(self, mock_workflow) -> None:
        """Test that get_metadata returns WorkflowMetadata."""
        metadata = mock_workflow.get_metadata()

        assert isinstance(metadata, WorkflowMetadata)
        assert metadata.name == "mock_workflow"
        assert metadata.workflow_type == "mock"
        assert metadata.deployment_mode == DeploymentMode.EMBEDDED

    def test_metadata_has_required_fields(self, mock_workflow) -> None:
        """Test that metadata has all required fields."""
        metadata = mock_workflow.get_metadata()

        assert hasattr(metadata, "name")
        assert hasattr(metadata, "workflow_type")
        assert hasattr(metadata, "description")
        assert hasattr(metadata, "version")
        assert hasattr(metadata, "deployment_mode")
        assert hasattr(metadata, "module_path")

    def test_metadata_is_consistent(self, mock_workflow) -> None:
        """Test that metadata is consistent across calls."""
        metadata1 = mock_workflow.get_metadata()
        metadata2 = mock_workflow.get_metadata()

        assert metadata1.name == metadata2.name
        assert metadata1.workflow_type == metadata2.workflow_type
        assert metadata1.version == metadata2.version


class TestGraphCompilation:
    """Tests for create_graph() and graph compilation."""

    @pytest.mark.asyncio
    async def test_create_graph_returns_compiled_graph(self, mock_workflow) -> None:
        """Test that create_graph returns a compiled LangGraph."""
        graph = await mock_workflow.create_graph()

        assert graph is not None
        # CompiledGraph should have invoke method
        assert hasattr(graph, "invoke")

    @pytest.mark.asyncio
    async def test_compiled_graph_is_callable(self, mock_workflow) -> None:
        """Test that compiled graph can be invoked."""
        graph = await mock_workflow.create_graph()

        child_state: MockChildState = {
            "input_data": "test",
            "output_data": "",
            "status": "pending",
        }

        result = graph.invoke(child_state)
        assert result is not None
        assert result["status"] == "completed"
        assert "test" in result["output_data"]


class TestLazyCompilation:
    """Tests for lazy compilation and caching with get_compiled_graph()."""

    @pytest.mark.asyncio
    async def test_get_compiled_graph_creates_graph_on_first_call(
        self, mock_workflow
    ) -> None:
        """Test that get_compiled_graph creates graph on first call."""
        assert mock_workflow._compiled_graph is None

        graph = await mock_workflow.get_compiled_graph()

        assert graph is not None
        assert mock_workflow._compiled_graph is not None

    @pytest.mark.asyncio
    async def test_get_compiled_graph_caches_graph(self, mock_workflow) -> None:
        """Test that get_compiled_graph caches the graph."""
        graph1 = await mock_workflow.get_compiled_graph()
        graph2 = await mock_workflow.get_compiled_graph()

        # Should return the same object (cached)
        assert graph1 is graph2

    @pytest.mark.asyncio
    async def test_multiple_instances_have_separate_caches(self) -> None:
        """Test that different instances have separate graph caches."""
        workflow1 = MockChildWorkflow()
        workflow2 = MockChildWorkflow()

        graph1 = await workflow1.get_compiled_graph()
        graph2 = await workflow2.get_compiled_graph()

        # Different instances should have different graph objects
        assert graph1 is not graph2


class TestValidationInterface:
    """Tests for validate_input() method."""

    @pytest.mark.asyncio
    async def test_validate_input_with_valid_state(
        self, mock_workflow, sample_parent_state
    ) -> None:
        """Test validation with valid parent state."""
        result = await mock_workflow.validate_input(sample_parent_state)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_input_with_invalid_state(self, mock_workflow) -> None:
        """Test validation with invalid parent state (missing preprocessor_output)."""
        invalid_state: EnhancedWorkflowState = {
            "input_story": "Test",
            "execution_log": [],
            "status": "in_progress",
            "context": {},
        }

        result = await mock_workflow.validate_input(invalid_state)
        assert result is False


class TestExecutionInterface:
    """Tests for execute() method."""

    @pytest.mark.asyncio
    async def test_execute_with_valid_input(
        self, mock_workflow, sample_parent_state
    ) -> None:
        """Test execute with valid parent state."""
        result = await mock_workflow.execute(sample_parent_state)

        assert result is not None
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_returns_expected_fields(
        self, mock_workflow, sample_parent_state
    ) -> None:
        """Test that execute returns standard result fields."""
        result = await mock_workflow.execute(sample_parent_state)

        assert "status" in result
        assert "output" in result
        assert "artifacts" in result
        assert "execution_time_seconds" in result

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_invalid_input(self, mock_workflow) -> None:
        """Test that execute raises ValueError with invalid input."""
        invalid_state: EnhancedWorkflowState = {
            "input_story": "Test",
            "execution_log": [],
            "status": "in_progress",
            "context": {},
        }

        with pytest.raises(ValueError):
            await mock_workflow.execute(invalid_state)

    @pytest.mark.asyncio
    async def test_execute_output_contains_workflow_results(
        self, mock_workflow, sample_parent_state
    ) -> None:
        """Test that execute output contains the graph invocation results."""
        result = await mock_workflow.execute(sample_parent_state)

        assert "output" in result
        output = result["output"]
        assert isinstance(output, dict)
        # Mock workflow adds output_data
        assert "output_data" in output


class TestInterfaceContract:
    """Tests for the overall interface contract."""

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(
        self, mock_workflow, sample_parent_state
    ) -> None:
        """Test complete workflow lifecycle: metadata → validation → execution."""
        # 1. Get metadata
        metadata = mock_workflow.get_metadata()
        assert metadata.name == "mock_workflow"

        # 2. Validate input
        is_valid = await mock_workflow.validate_input(sample_parent_state)
        assert is_valid is True

        # 3. Execute
        result = await mock_workflow.execute(sample_parent_state)
        assert result["status"] == "success"
        assert result["output"] is not None

    @pytest.mark.asyncio
    async def test_child_workflow_contract_with_coordinator(
        self, mock_workflow, sample_parent_state
    ) -> None:
        """
        Test that child workflow conforms to coordinator's expected contract.

        The coordinator expects:
        1. validate_input(state) -> bool
        2. execute(state) -> Dict[str, Any] with status, output, artifacts, execution_time_seconds
        """
        # Simulate what coordinator does
        if await mock_workflow.validate_input(sample_parent_state):
            result = await mock_workflow.execute(sample_parent_state)

            # Coordinator should be able to create WorkflowExecutionResult from this
            assert "status" in result
            assert "output" in result
            assert "artifacts" in result
            assert "execution_time_seconds" in result
            assert isinstance(result["status"], str)
            assert isinstance(result["artifacts"], list)
            assert isinstance(result["execution_time_seconds"], (int, float))
