"""
Base class for all child workflows in the agentic framework.

Child workflows are specialized executors for specific software development tasks.
This base class defines the interface that all child workflows must implement.

Key characteristics:
- Pre-compiled LangGraph for fast execution
- Separate typed state (child state) from parent state
- Async execution throughout
- Registry integration via metadata
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata


class BaseChildWorkflow(ABC):
    """
    Abstract base class for all child workflows.

    Each child workflow is responsible for:
    1. Defining its own internal state schema (TypedDict)
    2. Creating and pre-compiling its LangGraph
    3. Validating that parent workflow state contains required inputs
    4. Executing its graph with the parent state
    5. Returning results in a standard format

    Child workflows receive data from the parent workflow through EnhancedWorkflowState
    and return results that the coordinator aggregates.

    Example:
        class ApiDevelopmentWorkflow(BaseChildWorkflow):
            def get_metadata(self) -> WorkflowMetadata:
                return WorkflowMetadata(
                    name="api_development",
                    workflow_type="api_development",
                    ...
                )

            async def create_graph(self) -> CompiledGraph:
                # Build and compile the LangGraph
                graph = StateGraph(ApiDevelopmentState)
                # ... add nodes and edges
                return graph.compile()

            async def validate_input(self, state: EnhancedWorkflowState) -> bool:
                # Check if state has required api_requirements
                return "preprocessor_output" in state

            async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
                graph = await self.create_graph()
                # Map parent state to child state
                child_state = {...}
                result = graph.invoke(child_state)
                # Extract and return results
                return result
    """

    def __init__(self):
        """Initialize the base child workflow."""
        self._compiled_graph: Optional[Any] = None

    @abstractmethod
    def get_metadata(self) -> WorkflowMetadata:
        """
        Return metadata about this workflow for registry.

        This should be a static method that returns the same metadata regardless
        of instance state. It's used by the registry to catalog the workflow.

        Returns:
            WorkflowMetadata containing name, type, version, deployment mode, etc.

        Example:
            def get_metadata(self) -> WorkflowMetadata:
                return WorkflowMetadata(
                    name="api_development",
                    workflow_type="api_development",
                    description="Develops RESTful APIs",
                    version="1.0.0",
                    deployment_mode=DeploymentMode.EMBEDDED,
                    module_path="workflows.children.api_development",
                    tags=["api", "development"]
                )
        """
        pass

    @abstractmethod
    async def create_graph(self) -> Any:
        """
        Create and pre-compile the LangGraph for this workflow.

        The graph should be built using LangGraph's StateGraph with a child-specific
        state TypedDict. The graph is compiled once and cached.

        Returns:
            Compiled LangGraph ready for invocation

        Raises:
            ValueError: If graph construction fails
            ImportError: If required dependencies are missing

        Example:
            async def create_graph(self) -> CompiledGraph:
                graph = StateGraph(ApiDevelopmentState)
                graph.add_node("design", self.design_node)
                graph.add_node("code_gen", self.code_gen_node)
                graph.add_edge("design", "code_gen")
                graph.set_entry_point("design")
                graph.set_finish_point("code_gen")
                return graph.compile()
        """
        pass

    @abstractmethod
    async def validate_input(self, state: EnhancedWorkflowState) -> bool:
        """
        Validate that the parent workflow state has required inputs for this workflow.

        This method checks if the EnhancedWorkflowState contains the necessary data
        (typically from preprocessor or planner outputs) that this workflow needs.

        Args:
            state: The parent workflow state

        Returns:
            True if all required inputs are present and valid, False otherwise

        Example:
            async def validate_input(self, state: EnhancedWorkflowState) -> bool:
                # Check if preprocessor output exists
                if not state.get("preprocessor_output"):
                    return False

                preprocessor_output = state["preprocessor_output"]
                return bool(preprocessor_output.get("api_requirements"))
        """
        pass

    @abstractmethod
    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """
        Execute this workflow and return results.

        This method:
        1. Gets or creates the compiled graph
        2. Extracts relevant data from parent state
        3. Maps it to child state format
        4. Invokes the compiled graph
        5. Extracts and returns results

        Args:
            state: The parent workflow state containing inputs and context

        Returns:
            Dictionary with workflow results. Standard keys should include:
            - status: "success", "failure", or "partial"
            - output: The main output data
            - artifacts: List of generated artifact paths
            - execution_time_seconds: How long execution took
            - error: (Optional) Error message if status is "failure"
            - error_type: (Optional) Type of error if failed

        Raises:
            ValueError: If input validation fails
            RuntimeError: If graph execution fails

        Example:
            async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
                if not await self.validate_input(state):
                    raise ValueError("Missing required inputs")

                graph = await self.create_graph()

                # Map parent state to child state
                child_state = {
                    "api_requirements": state["preprocessor_output"]["requirements"],
                    "context": state.get("context", "")
                }

                result = graph.invoke(child_state)

                return {
                    "status": "success",
                    "output": result,
                    "artifacts": result.get("artifacts", []),
                    "execution_time_seconds": 12.5
                }
        """
        pass

    async def get_compiled_graph(self) -> Any:
        """
        Get the compiled graph, creating it if necessary (lazy loading).

        This method caches the compiled graph to avoid recreating it on each execution.
        The first call creates and caches the graph; subsequent calls return the cached version.

        Returns:
            The compiled CompiledGraph

        Raises:
            RuntimeError: If graph creation fails
        """
        if self._compiled_graph is None:
            self._compiled_graph = await self.create_graph()
        return self._compiled_graph
