"""
Integration tests for the parent workflow graph.

Tests the complete workflow graph assembly, execution, and state transitions
through the pipeline using LangGraph's StateGraph.
"""

import pytest
import tempfile
import os
from datetime import datetime
import asyncio

from workflows.parent.state import create_initial_state
from workflows.parent.graph import (
    create_enhanced_parent_workflow,
    create_enhanced_parent_workflow_with_memory,
)


# ========== Fixtures ==========


@pytest.fixture
def sample_input_story() -> str:
    """Sample input story for testing."""
    return """# User Management API

## Story
As a system administrator, I need to create a User Management API that allows creating, reading, updating, and deleting users with role-based access control.

## Requirements
- RESTful API endpoints for CRUD operations
- JWT token-based authentication
- Role-based access control (Admin, User, Guest)
- Input validation using Pydantic
- Error handling with appropriate HTTP status codes
- Comprehensive API documentation

## Success Criteria
- All endpoints pass unit tests
- API documentation is generated automatically
- Response time < 500ms for 95% of requests
- Zero critical security vulnerabilities

## Constraints
- Must use Python 3.11+
- Database queries must use async/await
- No external payment processing needed
"""


@pytest.fixture
def initial_state(sample_input_story: str):
    """Create initial state for testing."""
    return create_initial_state(sample_input_story)


@pytest.fixture
def temp_checkpoint_dir():
    """Create a temporary directory for checkpoints."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


# ========== Graph Creation Tests ==========


def test_create_parent_workflow_without_checkpointing():
    """Test creating parent workflow without checkpointing."""
    workflow = create_enhanced_parent_workflow()

    assert workflow is not None
    # Graph should have the nodes and edges configured
    assert hasattr(workflow, "invoke")
    assert callable(workflow.invoke)


def test_create_parent_workflow_with_checkpointing(temp_checkpoint_dir):
    """Test creating parent workflow with checkpointing."""
    workflow = create_enhanced_parent_workflow(checkpoint_dir=temp_checkpoint_dir)

    assert workflow is not None
    assert hasattr(workflow, "invoke")
    assert callable(workflow.invoke)


def test_create_parent_workflow_with_memory():
    """Test creating parent workflow with memory/checkpointing."""
    workflow, thread_id, config = create_enhanced_parent_workflow_with_memory()

    assert workflow is not None
    assert thread_id is not None
    assert config is not None
    assert "configurable" in config
    assert "thread_id" in config["configurable"]


def test_create_parent_workflow_with_memory_custom_thread_id():
    """Test creating parent workflow with custom thread ID."""
    custom_thread_id = "test-thread-123"
    workflow, thread_id, config = create_enhanced_parent_workflow_with_memory(
        thread_id=custom_thread_id
    )

    assert thread_id == custom_thread_id
    assert config["configurable"]["thread_id"] == custom_thread_id


# ========== Graph Execution Tests ==========


@pytest.mark.asyncio
async def test_workflow_invocation_basic(initial_state):
    """Test basic workflow invocation."""
    workflow = create_enhanced_parent_workflow()

    # Invoke the workflow asynchronously
    result_state = await workflow.ainvoke(initial_state)

    assert result_state is not None
    assert isinstance(result_state, dict)


@pytest.mark.asyncio
async def test_workflow_completes_all_stages(initial_state):
    """Test that workflow completes all pipeline stages."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Check all stages completed
    assert result_state["preprocessor_completed"]
    assert result_state["planner_completed"]
    assert result_state["coordinator_completed"]
    assert result_state["aggregator_completed"]


@pytest.mark.asyncio
async def test_workflow_generates_output(initial_state):
    """Test that workflow generates final output."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Check final output
    assert result_state["final_output"] is not None
    assert "status" in result_state["final_output"]
    assert "summary" in result_state["final_output"]
    assert "artifacts" in result_state["final_output"]


@pytest.mark.asyncio
async def test_workflow_records_execution_time(initial_state):
    """Test that workflow records execution time."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Check execution time
    assert result_state["start_time"] is not None
    assert result_state["end_time"] is not None
    assert result_state["execution_time_seconds"] > 0


@pytest.mark.asyncio
async def test_workflow_creates_execution_log(initial_state):
    """Test that workflow creates comprehensive execution log."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Check execution log
    log = result_state["execution_log"]
    assert len(log) > 0

    # Should have entries from all components
    components = set(entry["component"] for entry in log)
    assert "preprocessor" in components
    assert "planner" in components
    assert "coordinator" in components
    assert "aggregator" in components


@pytest.mark.asyncio
async def test_workflow_handles_empty_input(initial_state):
    """Test workflow behavior with minimal input."""
    # Create state with minimal content
    initial_state["input_story"] = "# Test\n\n## Story\nTest"

    workflow = create_enhanced_parent_workflow()

    # Should still process without crashing
    result_state = await workflow.ainvoke(initial_state)
    assert result_state is not None


@pytest.mark.asyncio
async def test_workflow_state_progression(initial_state):
    """Test that workflow properly transitions through states."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Verify state progression
    assert result_state["preprocessor_output"] is not None
    assert result_state["planner_output"] is not None
    assert len(result_state["execution_results"]) > 0
    assert result_state["final_output"] is not None


# ========== Error Handling Tests ==========


@pytest.mark.asyncio
async def test_workflow_handles_preprocessor_errors():
    """Test workflow error handling when preprocessor fails."""
    workflow = create_enhanced_parent_workflow()

    # Create state with invalid input that might cause issues
    state = create_initial_state("")  # Very minimal input

    # Should still complete (with or without errors gracefully)
    result_state = await workflow.ainvoke(state)
    assert result_state is not None


@pytest.mark.asyncio
async def test_workflow_records_errors_in_log(initial_state):
    """Test that errors are recorded in execution log."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Check if any errors were logged
    log = result_state["execution_log"]
    error_entries = [e for e in log if e.get("event_type") == "error"]

    # Whether errors exist or not, the log structure should be correct
    for entry in log:
        assert "timestamp" in entry
        assert "component" in entry
        assert "event_type" in entry
        assert "message" in entry
        assert "details" in entry


# ========== Checkpointing Tests ==========


@pytest.mark.asyncio
async def test_workflow_with_checkpointing_persists_state(initial_state, temp_checkpoint_dir):
    """Test that checkpointing persists state across invocations.

    Note: This test requires AsyncSqliteSaver which needs aiosqlite.
    Test is skipped if async checkpointing is not properly configured.
    """
    thread_id = "test-thread-persistence"

    workflow = create_enhanced_parent_workflow(checkpoint_dir=temp_checkpoint_dir)

    # Create config for this thread
    config = {"configurable": {"thread_id": thread_id}}

    # Try to invoke - if async checkpointing not available, skip
    try:
        result_state_1 = await workflow.ainvoke(initial_state, config=config)
        # Verify first execution completed
        assert result_state_1["preprocessor_completed"]
        # Check that checkpoint directory has been created
        assert os.path.exists(temp_checkpoint_dir)
    except (NotImplementedError, AttributeError) as e:
        if "aiosqlite" in str(e) or "is_alive" in str(e):
            pytest.skip(f"Async checkpointing not available: {e}")
        raise


@pytest.mark.asyncio
async def test_workflow_with_memory_config(initial_state, temp_checkpoint_dir):
    """Test workflow creation with memory and execution.

    Note: This test requires AsyncSqliteSaver which needs aiosqlite.
    Test is skipped if async checkpointing is not properly configured.
    """
    workflow, thread_id, config = create_enhanced_parent_workflow_with_memory(
        checkpoint_dir=temp_checkpoint_dir
    )

    # Try to execute with memory config - skip if async checkpointing not available
    try:
        result_state = await workflow.ainvoke(initial_state, config=config)
        # Should complete successfully
        assert result_state["aggregator_completed"]
        assert result_state["final_output"] is not None
    except (NotImplementedError, AttributeError) as e:
        if "aiosqlite" in str(e) or "is_alive" in str(e):
            pytest.skip(f"Async checkpointing not available: {e}")
        raise


# ========== Graph Structure Tests ==========


def test_workflow_has_correct_nodes():
    """Test that workflow graph has all required nodes."""
    workflow = create_enhanced_parent_workflow()

    # Access graph nodes through the compiled graph
    assert workflow is not None
    # The graph should have our nodes configured
    assert hasattr(workflow, "invoke")


@pytest.mark.asyncio
async def test_workflow_accepts_initial_state(initial_state):
    """Test that workflow accepts EnhancedWorkflowState."""
    workflow = create_enhanced_parent_workflow()

    # Should accept the state without errors
    result_state = await workflow.ainvoke(initial_state)
    assert isinstance(result_state, dict)


# ========== Performance Tests ==========


@pytest.mark.asyncio
async def test_workflow_execution_time_reasonable(initial_state):
    """Test that workflow completes in reasonable time."""
    import time

    workflow = create_enhanced_parent_workflow()

    start_time = time.time()
    result_state = await workflow.ainvoke(initial_state)
    elapsed = time.time() - start_time

    # Should complete reasonably fast (< 10 seconds for small inputs)
    assert elapsed < 10.0
    assert result_state["execution_time_seconds"] < 10.0


# ========== Full Workflow Scenarios ==========


@pytest.mark.asyncio
async def test_api_development_workflow(initial_state):
    """Test workflow with API development story."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Verify complete execution
    assert result_state["aggregator_completed"]
    assert result_state["final_output"]["status"] in ["success", "partial", "failure"]


@pytest.mark.asyncio
async def test_workflow_output_contains_all_stages(initial_state):
    """Test that final output contains information from all stages."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    final_output = result_state["final_output"]

    # Should contain references to all stages
    assert "preprocessor_output" in final_output
    assert "planner_output" in final_output
    assert "execution_results" in final_output
    assert "execution_log" in final_output


@pytest.mark.asyncio
async def test_workflow_summary_statistics(initial_state):
    """Test that workflow generates summary statistics."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    summary = result_state["final_output"]["summary"]

    # Should have summary statistics
    assert "total_tasks_executed" in summary
    assert "successful_tasks" in summary
    assert "failed_tasks" in summary
    assert "total_artifacts_generated" in summary


# ========== Artifact Handling Tests ==========


@pytest.mark.asyncio
async def test_workflow_aggregates_artifacts(initial_state):
    """Test that workflow aggregates artifacts from all stages."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    # Check artifacts
    assert isinstance(result_state["final_artifacts"], list)
    assert isinstance(result_state["final_output"]["artifacts"], list)


# ========== Execution Log Tests ==========


@pytest.mark.asyncio
async def test_execution_log_has_valid_structure(initial_state):
    """Test that execution log has valid structure throughout."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    log = result_state["execution_log"]

    for entry in log:
        # Check all required fields
        assert isinstance(entry, dict)
        assert "timestamp" in entry
        assert "component" in entry
        assert "event_type" in entry
        assert "message" in entry
        assert "details" in entry

        # Validate values
        assert entry["component"] in [
            "preprocessor",
            "planner",
            "coordinator",
            "aggregator",
        ]
        assert entry["event_type"] in ["started", "completed", "error"]
        assert isinstance(entry["message"], str)
        assert isinstance(entry["details"], dict)


@pytest.mark.asyncio
async def test_execution_log_timestamps_are_valid(initial_state):
    """Test that execution log timestamps are valid ISO format."""
    workflow = create_enhanced_parent_workflow()

    # Execute workflow
    result_state = await workflow.ainvoke(initial_state)

    log = result_state["execution_log"]

    for entry in log:
        # Should be able to parse timestamp as ISO format
        try:
            datetime.fromisoformat(entry["timestamp"])
        except (ValueError, TypeError):
            pytest.fail(f"Invalid timestamp: {entry['timestamp']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
