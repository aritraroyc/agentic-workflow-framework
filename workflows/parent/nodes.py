"""
Node functions for the parent workflow orchestrator.

Each node function:
1. Accepts EnhancedWorkflowState as input
2. Performs its specific task
3. Updates the state with results
4. Adds entries to the execution log
5. Returns the updated state

The nodes form a pipeline:
preprocessor_node → planner_node → coordinator_node → aggregator_node
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any

from workflows.parent.state import (
    EnhancedWorkflowState,
    ExecutionLogEntry,
    add_log_entry,
)
from workflows.parent.agents.preprocessor import PreprocessorAgent
from workflows.parent.agents.planner import PlannerAgent
from workflows.parent.agents.coordinator import WorkflowCoordinator
from core.llm import get_default_llm_client

logger = logging.getLogger(__name__)


async def preprocessor_node(state: EnhancedWorkflowState) -> EnhancedWorkflowState:
    """
    Preprocessor node: Parse and validate the input story.

    This node:
    1. Takes the raw markdown input story
    2. Parses markdown sections
    3. Validates structure
    4. Extracts structured data
    5. Generates metadata

    Args:
        state: Current workflow state with input_story

    Returns:
        Updated state with preprocessor_output and preprocessor_completed
    """
    logger.info("Starting preprocessor node")
    start_time = time.time()

    try:
        # Add start log entry
        state = add_log_entry(
            state,
            component="preprocessor",
            event_type="started",
            message="Preprocessing input story",
        )

        # Initialize preprocessor agent
        llm = get_default_llm_client()
        preprocessor = PreprocessorAgent(llm=llm)

        # Run preprocessing
        preprocessor_output = await preprocessor.process(state["input_story"])

        # Update state
        state["preprocessor_output"] = preprocessor_output
        state["preprocessor_completed"] = True

        elapsed = time.time() - start_time

        # Add success log entry
        state = add_log_entry(
            state,
            component="preprocessor",
            event_type="completed",
            message=f"Preprocessing completed in {elapsed:.2f}s",
            details={
                "sections_parsed": len(preprocessor_output.get("parsed_sections", {})),
                "story_type": preprocessor_output.get("detected_story_type"),
                "structure_valid": preprocessor_output.get("structure_valid"),
                "errors": len(preprocessor_output.get("parsing_errors", [])),
                "warnings": len(preprocessor_output.get("parsing_warnings", [])),
                "execution_time_seconds": elapsed,
            },
        )

        logger.info(
            f"Preprocessor completed: story_type={preprocessor_output.get('detected_story_type')}, "
            f"valid={preprocessor_output.get('structure_valid')}, elapsed={elapsed:.2f}s"
        )
        return state

    except Exception as e:
        logger.error(f"Preprocessor node failed: {str(e)}", exc_info=True)

        elapsed = time.time() - start_time

        # Add error log entry
        state = add_log_entry(
            state,
            component="preprocessor",
            event_type="error",
            message=f"Preprocessing failed: {str(e)}",
            details={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time_seconds": elapsed,
            },
        )

        # Set error state
        state["error"] = str(e)
        state["error_component"] = "preprocessor"
        state["error_timestamp"] = datetime.now().isoformat()
        state["error_details"] = {
            "error_type": type(e).__name__,
            "exception": str(e),
        }

        raise


async def planner_node(state: EnhancedWorkflowState) -> EnhancedWorkflowState:
    """
    Planner node: Create an execution plan for the workflow.

    This node:
    1. Takes preprocessor output
    2. Analyzes the story scope
    3. Identifies required workflows
    4. Creates workflow tasks with dependencies
    5. Determines execution strategy
    6. Identifies risk factors

    Args:
        state: Current workflow state with preprocessor_output

    Returns:
        Updated state with planner_output and planner_completed
    """
    logger.info("Starting planner node")
    start_time = time.time()

    try:
        # Validate prerequisite
        if not state.get("preprocessor_completed"):
            raise RuntimeError("Preprocessor must complete before planner")

        # Add start log entry
        state = add_log_entry(
            state,
            component="planner",
            event_type="started",
            message="Creating workflow execution plan",
        )

        # Initialize planner agent
        llm = get_default_llm_client()
        planner = PlannerAgent(llm=llm)

        # Run planning
        planner_output = await planner.plan(
            preprocessor_output=state["preprocessor_output"]
        )

        # Update state
        state["planner_output"] = planner_output
        state["planner_completed"] = True
        state["workflow_tasks"] = planner_output.get("workflow_tasks", [])

        elapsed = time.time() - start_time

        # Add success log entry
        state = add_log_entry(
            state,
            component="planner",
            event_type="completed",
            message=f"Planning completed in {elapsed:.2f}s",
            details={
                "required_workflows": planner_output.get("required_workflows", []),
                "task_count": len(planner_output.get("workflow_tasks", [])),
                "execution_strategy": planner_output.get("execution_strategy"),
                "estimated_effort_hours": planner_output.get(
                    "estimated_total_effort_hours"
                ),
                "risk_count": len(planner_output.get("risk_factors", [])),
                "execution_time_seconds": elapsed,
            },
        )

        logger.info(
            f"Planner completed: tasks={len(state['workflow_tasks'])}, "
            f"strategy={planner_output.get('execution_strategy')}, elapsed={elapsed:.2f}s"
        )
        return state

    except Exception as e:
        logger.error(f"Planner node failed: {str(e)}", exc_info=True)

        elapsed = time.time() - start_time

        # Add error log entry
        state = add_log_entry(
            state,
            component="planner",
            event_type="error",
            message=f"Planning failed: {str(e)}",
            details={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time_seconds": elapsed,
            },
        )

        # Set error state
        state["error"] = str(e)
        state["error_component"] = "planner"
        state["error_timestamp"] = datetime.now().isoformat()
        state["error_details"] = {
            "error_type": type(e).__name__,
            "exception": str(e),
        }

        raise


async def coordinator_node(state: EnhancedWorkflowState) -> EnhancedWorkflowState:
    """
    Coordinator node: Execute the planned workflows.

    This node:
    1. Takes the planned workflow tasks
    2. Executes them according to the strategy (sequential/parallel/hybrid)
    3. Tracks execution results
    4. Handles dependencies between workflows
    5. Aggregates execution status

    Args:
        state: Current workflow state with planner_output and workflow_tasks

    Returns:
        Updated state with execution_results and coordinator_completed
    """
    logger.info("Starting coordinator node")
    start_time = time.time()

    try:
        # Validate prerequisite
        if not state.get("planner_completed"):
            raise RuntimeError("Planner must complete before coordinator")

        # Add start log entry
        state = add_log_entry(
            state,
            component="coordinator",
            event_type="started",
            message="Starting workflow execution",
        )

        # Get coordinator configuration from planner output
        planner_output = state.get("planner_output", {})
        execution_strategy = planner_output.get("execution_strategy", "sequential")
        execution_order = planner_output.get("execution_order", [])
        task_dependencies = planner_output.get("task_dependencies", {})

        # Initialize coordinator
        coordinator = WorkflowCoordinator(timeout_seconds=3600, max_retries=3)

        # Execute workflows
        execution_results = await coordinator.execute(
            workflow_tasks=state.get("workflow_tasks", []),
            execution_strategy=execution_strategy,
            execution_order=execution_order,
            task_dependencies=task_dependencies,
        )

        # Update state
        state["execution_results"] = execution_results
        state["coordinator_completed"] = True

        # Get execution summary
        execution_summary = coordinator.get_execution_summary(execution_results)

        elapsed = time.time() - start_time

        # Add success log entry
        state = add_log_entry(
            state,
            component="coordinator",
            event_type="completed",
            message=f"Workflow execution completed in {elapsed:.2f}s",
            details={
                "total_tasks": execution_summary.get("total_tasks"),
                "successful": execution_summary.get("successful"),
                "failed": execution_summary.get("failed"),
                "success_rate": execution_summary.get("success_rate"),
                "overall_status": execution_summary.get("overall_status"),
                "total_execution_time_seconds": execution_summary.get(
                    "total_execution_time_seconds"
                ),
                "execution_strategy": execution_strategy,
            },
        )

        logger.info(
            f"Coordinator completed: successful={execution_summary.get('successful')}, "
            f"failed={execution_summary.get('failed')}, status={execution_summary.get('overall_status')}, "
            f"elapsed={elapsed:.2f}s"
        )
        return state

    except Exception as e:
        logger.error(f"Coordinator node failed: {str(e)}", exc_info=True)

        elapsed = time.time() - start_time

        # Add error log entry
        state = add_log_entry(
            state,
            component="coordinator",
            event_type="error",
            message=f"Workflow execution failed: {str(e)}",
            details={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time_seconds": elapsed,
            },
        )

        # Set error state
        state["error"] = str(e)
        state["error_component"] = "coordinator"
        state["error_timestamp"] = datetime.now().isoformat()
        state["error_details"] = {
            "error_type": type(e).__name__,
            "exception": str(e),
        }

        raise


async def aggregator_node(state: EnhancedWorkflowState) -> EnhancedWorkflowState:
    """
    Aggregator node: Aggregate and finalize results.

    This node:
    1. Collects results from all executed workflows
    2. Aggregates artifacts and outputs
    3. Generates final summary
    4. Validates completion status
    5. Records end time and total execution time

    Args:
        state: Current workflow state with execution_results

    Returns:
        Updated state with final_output, final_artifacts, and aggregator_completed
    """
    logger.info("Starting aggregator node")
    start_time = time.time()

    try:
        # Note: Aggregator runs even if coordinator fails, but validates completion
        if not state.get("coordinator_completed"):
            logger.warning("Coordinator did not complete, aggregating partial results")

        # Add start log entry
        state = add_log_entry(
            state,
            component="aggregator",
            event_type="started",
            message="Aggregating workflow results",
        )

        # Collect all artifacts
        final_artifacts: list = []
        execution_results = state.get("execution_results", {})

        for task_id, result in execution_results.items():
            if isinstance(result, dict):
                artifacts = result.get("artifacts", [])
                if artifacts:
                    final_artifacts.extend(artifacts)

        state["final_artifacts"] = final_artifacts

        # Generate final output
        final_output: Dict[str, Any] = {
            "status": _determine_overall_status(execution_results),
            "summary": {
                "total_tasks_executed": len(execution_results),
                "successful_tasks": sum(
                    1
                    for r in execution_results.values()
                    if isinstance(r, dict) and r.get("status") == "success"
                ),
                "failed_tasks": sum(
                    1
                    for r in execution_results.values()
                    if isinstance(r, dict) and r.get("status") == "failure"
                ),
                "total_artifacts_generated": len(final_artifacts),
            },
            "artifacts": final_artifacts,
            "execution_results": execution_results,
            "preprocessor_output": state.get("preprocessor_output", {}),
            "planner_output": state.get("planner_output", {}),
            "execution_log": state.get("execution_log", []),
        }

        state["final_output"] = final_output
        state["aggregator_completed"] = True

        # Record end time
        state["end_time"] = datetime.now().isoformat()

        # Calculate total execution time
        if state.get("start_time"):
            try:
                start = datetime.fromisoformat(state["start_time"])
                end = datetime.fromisoformat(state["end_time"])
                total_seconds = (end - start).total_seconds()
                state["execution_time_seconds"] = total_seconds
            except (ValueError, TypeError):
                logger.warning("Could not calculate total execution time")
                state["execution_time_seconds"] = time.time() - start_time

        elapsed = time.time() - start_time

        # Add success log entry
        state = add_log_entry(
            state,
            component="aggregator",
            event_type="completed",
            message=f"Aggregation completed in {elapsed:.2f}s",
            details={
                "final_status": final_output.get("status"),
                "total_artifacts": len(final_artifacts),
                "total_execution_time_seconds": state.get("execution_time_seconds"),
                "aggregation_time_seconds": elapsed,
            },
        )

        logger.info(
            f"Aggregator completed: status={final_output.get('status')}, "
            f"artifacts={len(final_artifacts)}, total_time={state.get('execution_time_seconds'):.2f}s"
        )
        return state

    except Exception as e:
        logger.error(f"Aggregator node failed: {str(e)}", exc_info=True)

        elapsed = time.time() - start_time

        # Add error log entry
        state = add_log_entry(
            state,
            component="aggregator",
            event_type="error",
            message=f"Aggregation failed: {str(e)}",
            details={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time_seconds": elapsed,
            },
        )

        # Set error state (but don't override if already set)
        if not state.get("error"):
            state["error"] = str(e)
            state["error_component"] = "aggregator"
            state["error_timestamp"] = datetime.now().isoformat()
            state["error_details"] = {
                "error_type": type(e).__name__,
                "exception": str(e),
            }

        state["aggregator_completed"] = False
        return state


def _determine_overall_status(execution_results: Dict[str, Any]) -> str:
    """
    Determine overall workflow status from execution results.

    Args:
        execution_results: Dictionary of execution results

    Returns:
        Overall status: "success", "partial", or "failure"
    """
    if not execution_results:
        return "failure"

    statuses = [
        r.get("status", "unknown")
        for r in execution_results.values()
        if isinstance(r, dict)
    ]

    if not statuses:
        return "failure"

    success_count = sum(1 for s in statuses if s == "success")
    failure_count = sum(1 for s in statuses if s == "failure")

    if failure_count == 0:
        return "success"
    elif success_count > 0:
        return "partial"
    else:
        return "failure"
