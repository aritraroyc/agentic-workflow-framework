#!/usr/bin/env python3
"""
Main entry point for the Agentic Workflow Framework.

This script orchestrates the complete workflow execution:
1. Load workflow registry from configuration
2. Initialize parent workflow with agents
3. Read story from markdown file or stdin
4. Execute parent workflow
5. Display and save results

Usage:
    python main.py [story_file.md]
    python main.py < story.md
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
import argparse

from workflows.parent.graph import create_enhanced_parent_workflow
from workflows.registry.loader import load_registry, validate_registry
from workflows.registry.invoker import WorkflowInvoker
from workflows.parent.agents.coordinator import WorkflowCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_story(story_path: Optional[str] = None) -> str:
    """
    Load story from file or stdin.

    Args:
        story_path: Optional path to story markdown file

    Returns:
        Story content as string
    """
    if story_path:
        path = Path(story_path)
        if not path.exists():
            raise FileNotFoundError(f"Story file not found: {story_path}")
        logger.info(f"Loading story from: {story_path}")
        return path.read_text()
    else:
        logger.info("Reading story from stdin...")
        return sys.stdin.read()


def setup_registry() -> Any:
    """
    Load and validate the workflow registry.

    Returns:
        Configured WorkflowRegistry instance
    """
    config_path = "config/workflows.yaml"
    logger.info(f"Loading workflow registry from: {config_path}")

    registry = load_registry(config_path)

    # Validate registry
    validation_results = validate_registry(registry)
    logger.info(f"Registry validation: {validation_results['total_workflows']} workflows loaded")

    if not validation_results["valid"]:
        for error in validation_results.get("errors", []):
            logger.error(f"Registry validation error: {error}")
        raise ValueError("Registry validation failed")

    return registry


async def run_workflow(story: str, registry: Any) -> Dict[str, Any]:
    """
    Execute the complete parent workflow.

    Args:
        story: Story content
        registry: WorkflowRegistry instance

    Returns:
        Workflow execution results
    """
    try:
        logger.info("=" * 80)
        logger.info("STARTING AGENTIC WORKFLOW EXECUTION")
        logger.info("=" * 80)

        # Create invoker with registry
        invoker = WorkflowInvoker(default_timeout=3600, default_retries=3)

        # Create parent workflow graph
        logger.info("Initializing parent workflow...")
        parent_workflow = await create_enhanced_parent_workflow()

        if parent_workflow is None:
            raise RuntimeError("Failed to create parent workflow graph")

        logger.info("Parent workflow initialized successfully")

        # Prepare input state
        input_state = {
            "input_story": story,
            "context": {},
            "execution_log": [],
            "intermediate_results": {},
            "preprocessor_output": None,
            "planner_output": None,
            "all_workflow_results": {},
        }

        logger.info("Executing parent workflow...")
        logger.info("-" * 80)

        # Execute workflow
        result_state = parent_workflow.invoke(input_state)

        logger.info("-" * 80)
        logger.info("Parent workflow execution completed")

        return result_state

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        raise


def save_results(result_state: Dict[str, Any], output_dir: str = "outputs") -> None:
    """
    Save workflow results to output directory.

    Args:
        result_state: Final workflow state
        output_dir: Directory to save results
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Save full state as JSON
    full_state_file = output_path / "full_state.json"
    logger.info(f"Saving full state to: {full_state_file}")

    # Convert state to JSON-serializable format
    serializable_state = {}
    for key, value in result_state.items():
        try:
            json.dumps(value)
            serializable_state[key] = value
        except (TypeError, ValueError):
            serializable_state[key] = str(value)

    with open(full_state_file, "w") as f:
        json.dump(serializable_state, f, indent=2)

    # Save execution log
    if "execution_log" in result_state:
        execution_log_file = output_path / "execution_log.json"
        logger.info(f"Saving execution log to: {execution_log_file}")
        with open(execution_log_file, "w") as f:
            json.dump(result_state["execution_log"], f, indent=2)

    # Save preprocessor output
    if result_state.get("preprocessor_output"):
        preprocessor_file = output_path / "preprocessor_output.json"
        logger.info(f"Saving preprocessor output to: {preprocessor_file}")
        with open(preprocessor_file, "w") as f:
            json.dump(result_state["preprocessor_output"], f, indent=2)

    # Save planner output
    if result_state.get("planner_output"):
        planner_file = output_path / "planner_output.json"
        logger.info(f"Saving planner output to: {planner_file}")
        with open(planner_file, "w") as f:
            json.dump(result_state["planner_output"], f, indent=2)

    # Save all workflow results
    if result_state.get("all_workflow_results"):
        results_file = output_path / "workflow_results.json"
        logger.info(f"Saving workflow results to: {results_file}")

        serializable_results = {}
        for key, value in result_state["all_workflow_results"].items():
            try:
                json.dumps(value)
                serializable_results[key] = value
            except (TypeError, ValueError):
                serializable_results[key] = str(value)

        with open(results_file, "w") as f:
            json.dump(serializable_results, f, indent=2)

    logger.info(f"Results saved to: {output_path}")


def print_summary(result_state: Dict[str, Any]) -> None:
    """
    Print a summary of workflow results.

    Args:
        result_state: Final workflow state
    """
    print("\n" + "=" * 80)
    print("WORKFLOW EXECUTION SUMMARY")
    print("=" * 80)

    # Print preprocessor output summary
    if result_state.get("preprocessor_output"):
        print("\n✓ Preprocessor Output:")
        preproc = result_state["preprocessor_output"]
        if preproc.get("structure_valid"):
            print("  - Structure validation: ✓ PASSED")
        if preproc.get("parsed_sections"):
            print(f"  - Sections parsed: {len(preproc['parsed_sections'])}")
        if preproc.get("extracted_data"):
            print(f"  - Data extracted: ✓")

    # Print planner output summary
    if result_state.get("planner_output"):
        print("\n✓ Planner Output:")
        planner = result_state["planner_output"]
        if planner.get("workflow_tasks"):
            print(f"  - Workflow tasks created: {len(planner['workflow_tasks'])}")
        if planner.get("execution_strategy"):
            print(f"  - Execution strategy: {planner['execution_strategy']}")

    # Print workflow results summary
    if result_state.get("all_workflow_results"):
        print("\n✓ Workflow Execution Results:")
        for task_id, result in result_state["all_workflow_results"].items():
            status = result.get("status", "unknown")
            workflow_name = result.get("workflow_name", "unknown")
            exec_time = result.get("execution_time_seconds", 0)
            status_emoji = "✓" if status == "success" else "✗" if status == "failure" else "⚠"
            print(f"  {status_emoji} {task_id} ({workflow_name}): {status} ({exec_time:.2f}s)")

    # Print execution log
    if result_state.get("execution_log"):
        print(f"\n✓ Execution Log ({len(result_state['execution_log'])} entries)")

    print("\n" + "=" * 80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute the Agentic Workflow Framework"
    )
    parser.add_argument(
        "story",
        nargs="?",
        help="Path to story markdown file (if not provided, reads from stdin)",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory to save results (default: outputs)",
    )

    args = parser.parse_args()

    try:
        # Load story
        story = load_story(args.story)

        if not story.strip():
            raise ValueError("Story is empty")

        logger.info(f"Story loaded ({len(story)} characters)")

        # Setup registry
        registry = setup_registry()

        # Run workflow
        result_state = await run_workflow(story, registry)

        # Save results
        save_results(result_state, args.output_dir)

        # Print summary
        print_summary(result_state)

        logger.info("Workflow execution completed successfully")

        return 0

    except KeyboardInterrupt:
        logger.info("Workflow execution interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
