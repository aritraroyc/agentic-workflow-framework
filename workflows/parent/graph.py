"""
Parent workflow graph assembly using LangGraph.

This module creates the complete workflow orchestration graph by:
1. Creating a StateGraph with EnhancedWorkflowState
2. Adding all orchestration nodes (preprocessor, planner, coordinator, aggregator)
3. Creating edges to connect nodes in the pipeline
4. Adding conditional edges for error handling
5. Configuring checkpointing for state persistence
6. Compiling the graph to a runnable workflow

The graph flow:
START → preprocessor_node → planner_node → coordinator_node → aggregator_node → END
"""

import logging
from typing import Callable, Dict, Optional, Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from workflows.parent.state import EnhancedWorkflowState, add_log_entry
from workflows.parent.nodes import (
    preprocessor_node,
    planner_node,
    coordinator_node,
    aggregator_node,
)

logger = logging.getLogger(__name__)


def _should_continue_after_preprocessor(state: EnhancedWorkflowState) -> str:
    """
    Determine whether to continue to planner or end on error.

    Args:
        state: Current workflow state

    Returns:
        "continue" to proceed to planner, "end" to stop workflow
    """
    if state.get("error"):
        logger.error(
            f"Preprocessor encountered error: {state.get('error')}. "
            "Ending workflow."
        )
        return "end"

    if not state.get("preprocessor_completed"):
        logger.error("Preprocessor did not complete. Ending workflow.")
        return "end"

    return "continue"


def _should_continue_after_planner(state: EnhancedWorkflowState) -> str:
    """
    Determine whether to continue to coordinator or end on error.

    Args:
        state: Current workflow state

    Returns:
        "continue" to proceed to coordinator, "end" to stop workflow
    """
    if state.get("error"):
        logger.error(
            f"Planner encountered error: {state.get('error')}. "
            "Ending workflow."
        )
        return "end"

    if not state.get("planner_completed"):
        logger.error("Planner did not complete. Ending workflow.")
        return "end"

    return "continue"


def _should_continue_after_coordinator(state: EnhancedWorkflowState) -> str:
    """
    Determine whether to continue to aggregator or end on error.

    Args:
        state: Current workflow state

    Returns:
        "continue" to proceed to aggregator, "end" to stop workflow
    """
    # Coordinator failures don't prevent aggregator from running
    # since aggregator can process partial results
    if not state.get("coordinator_completed"):
        logger.warning("Coordinator did not complete, proceeding to aggregator for partial aggregation")

    return "continue"


def create_enhanced_parent_workflow(
    checkpoint_dir: Optional[str] = None,
) -> "CompiledStateGraph":
    """
    Create and compile the enhanced parent workflow graph.

    This function:
    1. Creates a StateGraph with EnhancedWorkflowState
    2. Adds all orchestration nodes
    3. Creates the main pipeline edges
    4. Adds conditional edges for error handling
    5. Optionally configures checkpointing
    6. Compiles and returns the graph

    Args:
        checkpoint_dir: Optional directory path for SQLite checkpointing.
                       If provided, enables state persistence across executions.
                       If None, no checkpointing is configured.

    Returns:
        Compiled StateGraph ready for execution

    Example:
        ```python
        # Create workflow with checkpointing
        workflow = create_enhanced_parent_workflow(
            checkpoint_dir="./.langgraph_checkpoints"
        )

        # Execute workflow
        input_state = create_initial_state("# My Story\n...")
        final_state = workflow.invoke(input_state)

        # Access results
        print(final_state["final_output"])
        print(final_state["execution_log"])
        ```
    """
    logger.info("Creating enhanced parent workflow graph")

    # Create the StateGraph with our state schema
    graph_builder = StateGraph(EnhancedWorkflowState)

    # Add all nodes to the graph
    logger.debug("Adding workflow nodes to graph")
    graph_builder.add_node("preprocessor", preprocessor_node)
    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("coordinator", coordinator_node)
    graph_builder.add_node("aggregator", aggregator_node)

    # Set the entry point
    logger.debug("Setting entry point to preprocessor")
    graph_builder.set_entry_point("preprocessor")

    # Add main pipeline edges
    logger.debug("Adding main pipeline edges")
    graph_builder.add_conditional_edges(
        "preprocessor",
        _should_continue_after_preprocessor,
        {
            "continue": "planner",
            "end": END,
        },
    )

    graph_builder.add_conditional_edges(
        "planner",
        _should_continue_after_planner,
        {
            "continue": "coordinator",
            "end": END,
        },
    )

    graph_builder.add_conditional_edges(
        "coordinator",
        _should_continue_after_coordinator,
        {
            "continue": "aggregator",
            "end": END,
        },
    )

    # Aggregator always ends the workflow
    graph_builder.add_edge("aggregator", END)

    # Compile the graph
    logger.info("Compiling parent workflow graph")

    # Configure checkpointing if directory is provided
    if checkpoint_dir:
        logger.info(f"Configuring SQLite checkpointing at {checkpoint_dir}")
        try:
            checkpoint_saver = SqliteSaver(checkpoint_dir)
            compiled_graph = graph_builder.compile(checkpointer=checkpoint_saver)
            logger.info("Graph compiled with checkpointing enabled")
        except Exception as e:
            logger.warning(
                f"Failed to configure checkpointing: {str(e)}. "
                "Compiling without checkpointing."
            )
            compiled_graph = graph_builder.compile()
    else:
        logger.debug("No checkpoint directory provided, compiling without checkpointing")
        compiled_graph = graph_builder.compile()

    logger.info("Enhanced parent workflow graph created successfully")
    return compiled_graph


def create_enhanced_parent_workflow_with_memory(
    thread_id: Optional[str] = None,
    checkpoint_dir: str = "./.langgraph_checkpoints",
) -> tuple:
    """
    Create an enhanced parent workflow with memory/checkpointing capabilities.

    This function creates a workflow with SQLite-based state persistence,
    allowing for resumable executions and history tracking.

    Args:
        thread_id: Optional thread ID for execution history tracking.
                  If None, a new UUID-based thread ID is generated.
        checkpoint_dir: Directory for SQLite checkpoints (default: ./.langgraph_checkpoints)

    Returns:
        Tuple of (compiled_graph, thread_id, checkpoint_config)

    Example:
        ```python
        workflow, thread_id, config = create_enhanced_parent_workflow_with_memory(
            thread_id="execution-123"
        )

        # Run workflow with memory
        input_state = create_initial_state("# My Story\n...")
        final_state = workflow.invoke(
            input_state,
            config={"configurable": {"thread_id": thread_id}}
        )
        ```
    """
    import uuid

    # Generate thread ID if not provided
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    logger.info(f"Creating enhanced parent workflow with memory (thread_id={thread_id})")

    # Create the graph with checkpointing
    compiled_graph = create_enhanced_parent_workflow(checkpoint_dir=checkpoint_dir)

    # Create config for this execution thread
    config = {"configurable": {"thread_id": thread_id}}

    logger.info(f"Workflow with memory created: thread_id={thread_id}")

    return compiled_graph, thread_id, config


# Export the workflow creation functions
__all__ = [
    "create_enhanced_parent_workflow",
    "create_enhanced_parent_workflow_with_memory",
    "END",
]
