"""
State definitions for the parent workflow orchestrator.

This module defines the TypedDict schemas used for state management in the LangGraph-based
parent workflow. These schemas enable type-safe state transitions and are compatible with
LangGraph's state graph architecture.
"""

from typing import TypedDict, Optional, Dict, List, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from workflows.registry.registry import WorkflowRegistry


class WorkflowExecutionResult(TypedDict, total=False):
    """
    Result from executing a single workflow.

    Attributes:
        workflow_name: Name of the executed workflow
        status: Execution status (success, failure, partial)
        output: The output data from the workflow
        artifacts: Generated artifacts (file paths, generated code, specs, etc.)
        execution_time_seconds: Time taken to execute in seconds
        error: Error message if execution failed
        error_type: Type of error (if failed)
        metadata: Additional metadata about execution
    """
    workflow_name: str
    status: str  # success, failure, partial, skipped
    output: Dict[str, Any]
    artifacts: List[str]
    execution_time_seconds: float
    error: Optional[str]
    error_type: Optional[str]
    metadata: Dict[str, Any]


class WorkflowTask(TypedDict, total=False):
    """
    A task representing a workflow to be executed by the coordinator.

    Attributes:
        task_id: Unique identifier for this task
        workflow_name: Name of the child workflow to execute
        workflow_type: Type of workflow (api_development, ui_development, etc.)
        responsibilities: Description of what this workflow should accomplish
        dependencies: List of task_ids this task depends on
        parameters: Input parameters for the workflow
        status: Current status (pending, in_progress, completed, failed)
        execution_result: Result if task has been executed
        priority: Task priority (1-10, higher is more important)
        estimated_effort_hours: Estimated effort in hours
    """
    task_id: str
    workflow_name: str
    workflow_type: str
    responsibilities: str
    dependencies: List[str]
    parameters: Dict[str, Any]
    status: str  # pending, in_progress, completed, failed
    execution_result: Optional[WorkflowExecutionResult]
    priority: int
    estimated_effort_hours: float


class PlannerOutput(TypedDict, total=False):
    """
    Output from the planner agent.

    The planner analyzes the preprocessed input and creates an execution plan including
    which workflows to use, how to structure tasks, and dependency relationships.

    Attributes:
        story_scope: Analysis of the input story requirements and scope
        required_workflows: List of workflow names needed
        workflow_tasks: List of WorkflowTask objects to execute
        task_dependencies: Dict mapping task_id to list of dependent task_ids
        execution_strategy: "sequential" or "parallel" or "hybrid"
        execution_order: Ordered list of task_ids showing execution sequence
        risk_factors: Identified risks and mitigation strategies
        estimated_total_effort_hours: Total estimated effort
        planning_rationale: Explanation of planning decisions
        planning_errors: Any errors encountered during planning
    """
    story_scope: str
    required_workflows: List[str]
    workflow_tasks: List[WorkflowTask]
    task_dependencies: Dict[str, List[str]]
    execution_strategy: str  # sequential, parallel, hybrid
    execution_order: List[str]
    risk_factors: List[Dict[str, str]]
    estimated_total_effort_hours: float
    planning_rationale: str
    planning_errors: List[str]


class PreprocessorOutput(TypedDict, total=False):
    """
    Output from the preprocessor agent.

    The preprocessor parses the input story, validates its structure, and extracts
    structured data for downstream processing.

    Attributes:
        parsed_sections: Dict of parsed markdown sections
        structure_valid: Whether the input structure is valid
        extracted_data: Structured data extracted from the input
        metadata: Metadata about the input (title, type, language, etc.)
        parsing_errors: Any errors encountered during parsing
        parsing_warnings: Warnings about the input format
        input_summary: Summary of the input story
        detected_story_type: Inferred type of story (api_development, ui_enhancement, etc.)
    """
    parsed_sections: Dict[str, str]
    structure_valid: bool
    extracted_data: Dict[str, Any]
    metadata: Dict[str, Any]
    parsing_errors: List[str]
    parsing_warnings: List[str]
    input_summary: str
    detected_story_type: str


class ExecutionLogEntry(TypedDict, total=False):
    """
    A single entry in the execution log.

    Attributes:
        timestamp: When this event occurred
        component: Which component (preprocessor, planner, coordinator, aggregator)
        event_type: Type of event (started, completed, error, etc.)
        message: Human-readable message
        details: Additional details
        status: Current status at this point
    """
    timestamp: str
    component: str
    event_type: str
    message: str
    details: Dict[str, Any]
    status: str


class EnhancedWorkflowState(TypedDict, total=False):
    """
    Main state object for the parent workflow orchestrator.

    This state flows through all nodes (preprocessor → planner → coordinator → aggregator)
    and accumulates results from each stage. LangGraph uses this to manage graph state.

    Attributes:
        # Input
        input_story: Raw markdown input from the user

        # Preprocessing stage
        preprocessor_output: Output from the preprocessor agent
        preprocessor_completed: Whether preprocessing is complete

        # Planning stage
        planner_output: Output from the planner agent
        planner_completed: Whether planning is complete

        # Execution stage
        workflow_tasks: List of tasks to execute (from planner)
        execution_results: Dict mapping task_id to WorkflowExecutionResult
        coordinator_completed: Whether coordination is complete

        # Aggregation stage
        final_output: Final aggregated output
        final_artifacts: List of all generated artifacts
        aggregator_completed: Whether aggregation is complete

        # Execution tracking
        execution_log: Log of all executed steps
        start_time: When workflow started
        end_time: When workflow completed
        execution_time_seconds: Total execution time

        # Error handling
        error: Error message if workflow failed
        error_component: Which component threw the error
        error_timestamp: When the error occurred
        error_details: Detailed error information

        # Registry (for child workflow execution)
        registry: WorkflowRegistry instance for invoking child workflows
    """
    # Input
    input_story: str

    # Preprocessing stage
    preprocessor_output: Optional[PreprocessorOutput]
    preprocessor_completed: bool

    # Planning stage
    planner_output: Optional[PlannerOutput]
    planner_completed: bool

    # Execution stage
    workflow_tasks: List[WorkflowTask]
    execution_results: Dict[str, WorkflowExecutionResult]
    coordinator_completed: bool

    # Aggregation stage
    final_output: Dict[str, Any]
    final_artifacts: List[str]
    aggregator_completed: bool

    # Execution tracking
    execution_log: List[ExecutionLogEntry]
    start_time: Optional[str]
    end_time: Optional[str]
    execution_time_seconds: float

    # Error handling
    error: Optional[str]
    error_component: Optional[str]
    error_timestamp: Optional[str]
    error_details: Optional[Dict[str, Any]]

    # Registry (for child workflow execution)
    registry: Optional[Any]  # WorkflowRegistry


def create_initial_state(input_story: str, registry: Optional[Any] = None) -> EnhancedWorkflowState:
    """
    Create an initial state for a new workflow execution.

    Args:
        input_story: The raw markdown input from the user
        registry: Optional WorkflowRegistry instance for child workflow execution

    Returns:
        An initialized EnhancedWorkflowState with default values
    """
    return {
        # Input
        "input_story": input_story,

        # Preprocessing stage
        "preprocessor_output": None,
        "preprocessor_completed": False,

        # Planning stage
        "planner_output": None,
        "planner_completed": False,

        # Execution stage
        "workflow_tasks": [],
        "execution_results": {},
        "coordinator_completed": False,

        # Aggregation stage
        "final_output": {},
        "final_artifacts": [],
        "aggregator_completed": False,

        # Execution tracking
        "execution_log": [],
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "execution_time_seconds": 0.0,

        # Error handling
        "error": None,
        "error_component": None,
        "error_timestamp": None,
        "error_details": None,

        # Registry
        "registry": registry,
    }


def add_log_entry(
    state: EnhancedWorkflowState,
    component: str,
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> EnhancedWorkflowState:
    """
    Add an entry to the execution log.

    Args:
        state: Current workflow state
        component: Which component generated this log entry
        event_type: Type of event
        message: Human-readable message
        details: Optional additional details

    Returns:
        Updated state with new log entry
    """
    entry: ExecutionLogEntry = {
        "timestamp": datetime.now().isoformat(),
        "component": component,
        "event_type": event_type,
        "message": message,
        "details": details or {},
        "status": "logged",
    }

    state["execution_log"].append(entry)
    return state
