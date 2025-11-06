"""
UI Enhancement child workflow implementation.

This workflow handles UI enhancement lifecycle:
1. Analysis: Analyzes UI enhancement requirements
2. Design: Creates design for enhancements
3. Code Generation: Generates enhancement code
4. Testing: Generates tests for enhancements
5. Accessibility: Improves accessibility and WCAG compliance
"""

import json
import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from workflows.children.base import BaseChildWorkflow
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode
from workflows.children.ui_enhancement.state import (
    UIEnhancementState,
    create_initial_ui_enhancement_state,
)
from workflows.children.ui_enhancement.agents.execution_planner import UIEnhancementPlannerAgent
from core.llm import get_default_llm_client
from workflows.children.ui_enhancement.prompts import (
    DESIGN_UI_ENHANCEMENT_PROMPT,
    GENERATE_UI_ENHANCEMENT_CODE_PROMPT,
    GENERATE_UI_ENHANCEMENT_TESTS_PROMPT,
    IMPROVE_ACCESSIBILITY_PROMPT,
    GENERATE_UI_ENHANCEMENT_DOCS_PROMPT,
)

logger = logging.getLogger(__name__)


class UIEnhancementWorkflow(BaseChildWorkflow):
    """
    Child workflow for UI enhancement.

    This workflow takes UI enhancement requirements and generates:
    - Detailed enhancement plan and analysis
    - Design specifications for enhancements
    - Code implementations
    - Test specifications
    - Accessibility improvements

    Internal phases:
    - analysis_node: Analyzes enhancement requirements
    - design_node: Designs enhancement specifications
    - code_generation_node: Generates enhancement code
    - testing_node: Generates test specifications
    - a11y_node: Improves accessibility and WCAG compliance
    - documentation_node: Generates enhancement documentation
    """

    def __init__(self):
        """Initialize the UI Enhancement workflow."""
        super().__init__()
        self.planner_agent = UIEnhancementPlannerAgent()
        self.llm_client = get_default_llm_client()

    def get_metadata(self) -> WorkflowMetadata:
        """Return metadata about this workflow for the registry."""
        return WorkflowMetadata(
            name="ui_enhancement",
            workflow_type="ui_enhancement",
            description="Enhances existing UIs with new features, improved accessibility (WCAG), performance optimization, and better UX",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.children.ui_enhancement.workflow",
            tags=["ui", "enhancement", "accessibility", "wcag"],
        )

    async def create_graph(self) -> Any:
        """
        Create and pre-compile the LangGraph for UI enhancement.

        Returns:
            Compiled StateGraph ready for invocation
        """
        logger.info("Creating UI enhancement workflow graph")

        # Create the state graph
        graph = StateGraph(UIEnhancementState)

        # Add nodes for each phase
        graph.add_node("analysis", self._analysis_node)
        graph.add_node("design", self._design_node)
        graph.add_node("code_generation", self._code_generation_node)
        graph.add_node("testing", self._testing_node)
        graph.add_node("a11y", self._a11y_node)
        graph.add_node("documentation", self._documentation_node)

        # Set entry point
        graph.set_entry_point("analysis")

        # Create the pipeline
        graph.add_edge("analysis", "design")
        graph.add_edge("design", "code_generation")
        graph.add_edge("code_generation", "testing")
        graph.add_edge("testing", "a11y")
        graph.add_edge("a11y", "documentation")
        graph.add_edge("documentation", END)

        return graph.compile()

    async def validate_input(self, state: EnhancedWorkflowState) -> bool:
        """
        Validate that the parent workflow state contains required enhancement inputs.

        Args:
            state: The parent workflow state

        Returns:
            True if state is valid for enhancement, False otherwise
        """
        if not state.get("input_story"):
            logger.warning("UI Enhancement: Missing input_story from parent state")
            return False

        if not state.get("preprocessor_output"):
            logger.warning("UI Enhancement: Missing preprocessor_output from parent state")
            return False

        logger.info("UI Enhancement input validation passed")
        return True

    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """
        Execute the UI enhancement workflow.

        Args:
            state: The parent workflow state

        Returns:
            Dict with status, output, artifacts, and execution_time_seconds
        """
        import time
        start_time = time.time()

        logger.info("Executing UI Enhancement workflow")

        try:
            if not await self.validate_input(state):
                execution_time = time.time() - start_time
                return {
                    "status": "failure",
                    "error": "Invalid input state for UI enhancement",
                    "output": {},
                    "artifacts": [],
                    "execution_time_seconds": execution_time,
                }

            # Extract input story and requirements from parent state
            input_story = state.get("input_story", "")
            preprocessor_output = state.get("preprocessor_output", {})
            story_requirements = preprocessor_output.get("extracted_data", {})

            # Create initial internal state
            internal_state = create_initial_ui_enhancement_state(
                input_story=input_story,
                story_requirements=story_requirements,
                parent_context=state,
            )

            # Get the compiled graph
            graph = await self.get_compiled_graph()

            # Execute the graph
            final_state = await graph.ainvoke(internal_state)

            # Collect artifacts
            artifacts = final_state.get("all_artifacts", [])
            execution_time = time.time() - start_time

            logger.info(
                f"UI Enhancement workflow completed in {execution_time:.2f}s "
                f"with status: {final_state.get('status')}"
            )

            return {
                "status": "success" if final_state.get("status") == "success" else "partial",
                "output": {
                    "enhancement_analysis": final_state.get("enhancement_analysis"),
                    "enhancement_design": final_state.get("enhancement_design"),
                    "enhancement_code": final_state.get("enhancement_code"),
                    "enhancement_tests": final_state.get("enhancement_tests"),
                    "a11y_improvements": final_state.get("a11y_improvements"),
                },
                "artifacts": artifacts,
                "execution_time_seconds": execution_time,
            }

        except Exception as e:
            logger.error(f"Error executing UI Enhancement workflow: {str(e)}", exc_info=True)
            execution_time = time.time() - start_time
            return {
                "status": "failure",
                "output": {"error": str(e)},
                "artifacts": [],
                "execution_time_seconds": execution_time,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def _analysis_node(self, state: UIEnhancementState) -> UIEnhancementState:
        """
        Analysis phase: Analyze UI enhancement requirements.

        Evaluates scope, design impact, and strategy for enhancements.
        """
        logger.info("UI Enhancement: Analysis phase")
        state = state.copy()

        try:
            # Call the planner agent
            result = await self.planner_agent.analyze_enhancement_requirements(
                story_requirements=state.get("story_requirements", {}),
                ui_structure=state.get("parent_context", {}).get("ui_structure"),
            )

            if result["success"]:
                state["enhancement_analysis"] = result["analysis"]
                state["analysis_completed"] = True
                state["execution_notes"] += "Analysis completed successfully. "
                logger.info("UI enhancement analysis completed")
            else:
                state["analysis_errors"] = result["errors"]
                state["enhancement_analysis"] = result["analysis"]
                state["analysis_completed"] = True
                state["execution_notes"] += f"Analysis completed with errors: {', '.join(result['errors'])}. "

        except Exception as e:
            logger.error(f"Error in analysis phase: {str(e)}")
            state["analysis_errors"].append(str(e))
            state["analysis_completed"] = True
            state["status"] = "failure"

        return state

    async def _design_node(self, state: UIEnhancementState) -> UIEnhancementState:
        """Design phase: Design UI enhancement specifications."""
        logger.info("UI Enhancement: Design phase")
        state = state.copy()

        if not state.get("analysis_completed") or not state.get("enhancement_analysis"):
            logger.warning("Skipping design phase: analysis not completed")
            return state

        try:
            prompt = DESIGN_UI_ENHANCEMENT_PROMPT.format(
                enhancement_analysis=json.dumps(state["enhancement_analysis"], indent=2)
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                design = json.loads(response_text)
            except json.JSONDecodeError:
                design = self._extract_json(response_text)

            state["enhancement_design"] = design
            state["design_completed"] = True
            state["execution_notes"] += "Design phase completed. "
            logger.info("UI enhancement design completed")

        except Exception as e:
            logger.error(f"Error in design phase: {str(e)}")
            state["design_errors"].append(str(e))
            state["design_completed"] = True

        return state

    async def _code_generation_node(self, state: UIEnhancementState) -> UIEnhancementState:
        """Code generation phase: Generate UI enhancement code."""
        logger.info("UI Enhancement: Code generation phase")
        state = state.copy()

        if not state.get("design_completed"):
            logger.warning("Skipping code generation: design not completed")
            return state

        try:
            prompt = GENERATE_UI_ENHANCEMENT_CODE_PROMPT.format(
                enhancement_design=json.dumps(state.get("enhancement_design", {}), indent=2),
                enhancement_analysis=json.dumps(state.get("enhancement_analysis", {}), indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                code_output = json.loads(response_text)
            except json.JSONDecodeError:
                code_output = self._extract_json(response_text)

            state["enhancement_code"] = code_output
            state["code_generation_completed"] = True
            state["execution_notes"] += "Code generation completed. "
            logger.info("Code generation completed")

        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            state["code_generation_errors"].append(str(e))
            state["code_generation_completed"] = True

        return state

    async def _testing_node(self, state: UIEnhancementState) -> UIEnhancementState:
        """Testing phase: Generate test specifications."""
        logger.info("UI Enhancement: Testing phase")
        state = state.copy()

        if not state.get("code_generation_completed"):
            logger.warning("Skipping testing: code generation not completed")
            return state

        try:
            prompt = GENERATE_UI_ENHANCEMENT_TESTS_PROMPT.format(
                enhancement_design=json.dumps(state.get("enhancement_design", {}), indent=2),
                enhancement_analysis=json.dumps(state.get("enhancement_analysis", {}), indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                test_output = json.loads(response_text)
            except json.JSONDecodeError:
                test_output = self._extract_json(response_text)

            state["enhancement_tests"] = test_output
            state["testing_completed"] = True
            state["execution_notes"] += "Testing phase completed. "
            logger.info("Testing phase completed")

        except Exception as e:
            logger.error(f"Error in testing phase: {str(e)}")
            state["testing_errors"].append(str(e))
            state["testing_completed"] = True

        return state

    async def _a11y_node(self, state: UIEnhancementState) -> UIEnhancementState:
        """Accessibility phase: Improve accessibility and WCAG compliance."""
        logger.info("UI Enhancement: Accessibility improvement phase")
        state = state.copy()

        if not state.get("testing_completed"):
            logger.warning("Skipping accessibility: testing not completed")
            return state

        try:
            prompt = IMPROVE_ACCESSIBILITY_PROMPT.format(
                enhancement_design=json.dumps(state.get("enhancement_design", {}), indent=2),
                enhancement_analysis=json.dumps(state.get("enhancement_analysis", {}), indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                a11y_output = json.loads(response_text)
            except json.JSONDecodeError:
                a11y_output = self._extract_json(response_text)

            state["a11y_improvements"] = a11y_output
            state["a11y_completed"] = True
            state["execution_notes"] += "Accessibility improvements completed. "
            logger.info("Accessibility improvements completed")

        except Exception as e:
            logger.error(f"Error in accessibility phase: {str(e)}")
            state["a11y_errors"].append(str(e))
            state["a11y_completed"] = True

        return state

    async def _documentation_node(self, state: UIEnhancementState) -> UIEnhancementState:
        """Documentation phase: Generate documentation."""
        logger.info("UI Enhancement: Documentation phase")
        state = state.copy()

        if not state.get("a11y_completed"):
            logger.warning("Skipping documentation: accessibility not completed")
            return state

        try:
            prompt = GENERATE_UI_ENHANCEMENT_DOCS_PROMPT.format(
                enhancement_design=json.dumps(state.get("enhancement_design", {}), indent=2),
                enhancement_analysis=json.dumps(state.get("enhancement_analysis", {}), indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                docs_output = json.loads(response_text)
            except json.JSONDecodeError:
                docs_output = self._extract_json(response_text)

            state["execution_notes"] += "Documentation completed. "
            state["status"] = "success"
            logger.info("Documentation phase completed")

        except Exception as e:
            logger.error(f"Error in documentation phase: {str(e)}")
            state["status"] = "partial"

        return state

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1

            if start == -1 or end == 0:
                return {}

            json_str = text[start:end]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Could not extract JSON from response")
            return {}
