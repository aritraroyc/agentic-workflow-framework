"""
UI Development child workflow implementation.

This workflow handles the complete UI development lifecycle:
1. Planning: Analyzes requirements and creates UI plan
2. Design: Creates design system and component specifications
3. Code Generation: Generates React/TypeScript code
4. Styling: Generates CSS/Tailwind styling
5. Testing: Generates component tests
6. Documentation: Creates component library documentation
"""

import json
import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from workflows.children.base import BaseChildWorkflow
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode
from workflows.children.ui_development.state import (
    UIDevState,
    create_initial_ui_state,
)
from workflows.children.ui_development.agents.execution_planner import UIPlannerAgent
from core.llm import get_default_llm_client
from workflows.children.ui_development.prompts import (
    DESIGN_UI_PROMPT,
    GENERATE_UI_CODE_PROMPT,
    GENERATE_STYLING_PROMPT,
    GENERATE_TESTS_PROMPT,
    GENERATE_DOCS_PROMPT,
)

logger = logging.getLogger(__name__)


class UIDevWorkflow(BaseChildWorkflow):
    """
    Child workflow for UI development.

    This workflow takes UI requirements from the parent workflow and generates
    a complete, production-ready UI implementation including:
    - Detailed UI plan
    - Design system specifications
    - React/TypeScript application code
    - Styling (Tailwind/CSS)
    - Component tests
    - Component library documentation

    Internal phases:
    - planning_node: Creates detailed UI plan
    - design_node: Creates design system specifications
    - code_generation_node: Generates application code
    - styling_node: Generates styling approach and theme
    - testing_node: Generates unit tests
    - documentation_node: Generates component documentation
    """

    def __init__(self):
        """Initialize the UI Development workflow."""
        super().__init__()
        self.planner_agent = UIPlannerAgent()
        self.llm_client = get_default_llm_client()

    def get_metadata(self) -> WorkflowMetadata:
        """Return metadata about this workflow for the registry."""
        return WorkflowMetadata(
            name="ui_development",
            workflow_type="ui_development",
            description="Develops complete web UIs from requirements including design, code generation, styling, testing, and documentation",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.children.ui_development.workflow",
            tags=["ui", "development", "react", "frontend"],
        )

    async def create_graph(self) -> Any:
        """
        Create and pre-compile the LangGraph for UI development.

        Returns:
            Compiled StateGraph ready for invocation
        """
        logger.info("Creating UI development workflow graph")

        # Create the state graph
        graph = StateGraph(UIDevState)

        # Add nodes for each phase
        graph.add_node("planning", self._planning_node)
        graph.add_node("design", self._design_node)
        graph.add_node("code_generation", self._code_generation_node)
        graph.add_node("styling", self._styling_node)
        graph.add_node("testing", self._testing_node)
        graph.add_node("documentation", self._documentation_node)

        # Set entry point
        graph.set_entry_point("planning")

        # Create the pipeline
        graph.add_edge("planning", "design")
        graph.add_edge("design", "code_generation")
        graph.add_edge("code_generation", "styling")
        graph.add_edge("styling", "testing")
        graph.add_edge("testing", "documentation")
        graph.add_edge("documentation", END)

        return graph.compile()

    async def validate_input(self, state: EnhancedWorkflowState) -> bool:
        """
        Validate that the parent workflow state contains required UI development inputs.

        Args:
            state: The parent workflow state

        Returns:
            True if state is valid for UI development, False otherwise
        """
        # Check for required parent workflow state fields
        if not state.get("input_story"):
            logger.warning("UI Development: Missing input_story from parent state")
            return False

        if not state.get("preprocessor_output"):
            logger.warning("UI Development: Missing preprocessor_output from parent state")
            return False

        logger.info("UI Development input validation passed")
        return True

    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """
        Execute the UI development workflow.

        Args:
            state: The parent workflow state

        Returns:
            Dict with status, output, artifacts, and execution_time_seconds
        """
        import time
        start_time = time.time()

        logger.info("Executing UI Development workflow")

        try:
            # Validate input
            if not await self.validate_input(state):
                execution_time = time.time() - start_time
                return {
                    "status": "failure",
                    "error": "Invalid input state for UI development",
                    "output": {},
                    "artifacts": [],
                    "execution_time_seconds": execution_time,
                }

            # Extract input story and requirements from parent state
            input_story = state.get("input_story", "")
            preprocessor_output = state.get("preprocessor_output", {})
            story_requirements = preprocessor_output.get("extracted_data", {})

            # Create initial internal state
            internal_state = create_initial_ui_state(
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
                f"UI Development workflow completed in {execution_time:.2f}s "
                f"with status: {final_state.get('status')}"
            )

            return {
                "status": "success" if final_state.get("status") == "success" else "partial",
                "output": {
                    "ui_plan": final_state.get("ui_plan"),
                    "ui_design": final_state.get("ui_design"),
                    "code_output": final_state.get("code_output"),
                    "styling_output": final_state.get("styling_output"),
                    "test_output": final_state.get("test_output"),
                    "docs_output": final_state.get("docs_output"),
                },
                "artifacts": artifacts,
                "execution_time_seconds": execution_time,
            }

        except Exception as e:
            logger.error(f"Error executing UI Development workflow: {str(e)}", exc_info=True)
            execution_time = time.time() - start_time
            return {
                "status": "failure",
                "output": {"error": str(e)},
                "artifacts": [],
                "execution_time_seconds": execution_time,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def _planning_node(self, state: UIDevState) -> UIDevState:
        """
        Planning phase: Create detailed UI plan.

        Analyzes UI requirements and generates a plan including:
        - Component definitions
        - Page structure
        - Framework selection
        - State management approach
        """
        logger.info("UI Development: Planning phase")
        state = state.copy()

        try:
            # Extract framework preference from story if available
            framework_preference = "React"
            if "framework" in state.get("story_requirements", {}):
                framework_preference = state["story_requirements"]["framework"]

            # Call the planner agent
            result = await self.planner_agent.plan_ui_development(
                story_requirements=state.get("story_requirements", {}),
                framework_preference=framework_preference,
                typescript_enabled=True,
            )

            if result["success"]:
                state["ui_plan"] = result["ui_plan"]
                state["planning_completed"] = True
                state["execution_notes"] += "Planning completed successfully. "
                logger.info("UI Planning completed")
            else:
                state["planning_errors"] = result["errors"]
                state["ui_plan"] = result["ui_plan"]
                state["planning_completed"] = True
                state["execution_notes"] += f"Planning completed with errors: {', '.join(result['errors'])}. "
                logger.warning(f"UI Planning completed with errors: {result['errors']}")

        except Exception as e:
            logger.error(f"Error in planning phase: {str(e)}")
            state["planning_errors"].append(str(e))
            state["planning_completed"] = True
            state["status"] = "failure"

        return state

    async def _design_node(self, state: UIDevState) -> UIDevState:
        """
        Design phase: Create design system and component specifications.

        Generates design tokens, color system, typography, component specs.
        """
        logger.info("UI Development: Design phase")
        state = state.copy()

        if not state.get("planning_completed") or not state.get("ui_plan"):
            logger.warning("Skipping design phase: planning not completed")
            return state

        try:
            prompt = DESIGN_UI_PROMPT.format(
                ui_plan=json.dumps(state["ui_plan"], indent=2)
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                design = json.loads(response_text)
            except json.JSONDecodeError:
                design = self._extract_json(response_text)

            state["ui_design"] = design
            state["design_completed"] = True
            state["execution_notes"] += "Design phase completed. "
            logger.info("UI Design completed")

        except Exception as e:
            logger.error(f"Error in design phase: {str(e)}")
            state["design_errors"].append(str(e))
            state["design_completed"] = True

        return state

    async def _code_generation_node(self, state: UIDevState) -> UIDevState:
        """
        Code generation phase: Generate React/TypeScript code.

        Creates component structure, page files, hooks, and utilities.
        """
        logger.info("UI Development: Code generation phase")
        state = state.copy()

        if not state.get("design_completed"):
            logger.warning("Skipping code generation: design not completed")
            return state

        try:
            prompt = GENERATE_UI_CODE_PROMPT.format(
                design_specs=json.dumps(state.get("ui_design", {}), indent=2),
                ui_plan=json.dumps(state.get("ui_plan", {}), indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                code_output = json.loads(response_text)
            except json.JSONDecodeError:
                code_output = self._extract_json(response_text)

            state["code_output"] = code_output
            state["code_generation_completed"] = True
            state["execution_notes"] += "Code generation completed. "
            logger.info("Code generation completed")

        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            state["code_generation_errors"].append(str(e))
            state["code_generation_completed"] = True

        return state

    async def _styling_node(self, state: UIDevState) -> UIDevState:
        """
        Styling phase: Generate CSS/Tailwind styling approach.

        Creates theme configuration, responsive utilities, and styling patterns.
        """
        logger.info("UI Development: Styling phase")
        state = state.copy()

        if not state.get("code_generation_completed"):
            logger.warning("Skipping styling: code generation not completed")
            return state

        try:
            framework = state.get("ui_plan", {}).get("target_framework", "React")
            prompt = GENERATE_STYLING_PROMPT.format(
                design_system=json.dumps(
                    state.get("ui_design", {}).get("design_system", {}), indent=2
                ),
                component_specs=json.dumps(
                    state.get("ui_design", {}).get("component_specs", {}), indent=2
                ),
                framework=framework,
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                styling_output = json.loads(response_text)
            except json.JSONDecodeError:
                styling_output = self._extract_json(response_text)

            state["styling_output"] = styling_output
            state["styling_completed"] = True
            state["execution_notes"] += "Styling phase completed. "
            logger.info("Styling phase completed")

        except Exception as e:
            logger.error(f"Error in styling phase: {str(e)}")
            state["styling_errors"].append(str(e))
            state["styling_completed"] = True

        return state

    async def _testing_node(self, state: UIDevState) -> UIDevState:
        """
        Testing phase: Generate component tests.

        Creates unit tests, integration tests, accessibility tests.
        """
        logger.info("UI Development: Testing phase")
        state = state.copy()

        if not state.get("styling_completed"):
            logger.warning("Skipping testing: styling not completed")
            return state

        try:
            prompt = GENERATE_TESTS_PROMPT.format(
                component_specs=json.dumps(
                    state.get("ui_design", {}).get("component_specs", {}), indent=2
                ),
                pages=json.dumps(state.get("ui_plan", {}).get("pages", []), indent=2),
                testing_framework="Jest",
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                test_output = json.loads(response_text)
            except json.JSONDecodeError:
                test_output = self._extract_json(response_text)

            state["test_output"] = test_output
            state["testing_completed"] = True
            state["execution_notes"] += "Testing phase completed. "
            logger.info("Testing phase completed")

        except Exception as e:
            logger.error(f"Error in testing phase: {str(e)}")
            state["testing_errors"].append(str(e))
            state["testing_completed"] = True

        return state

    async def _documentation_node(self, state: UIDevState) -> UIDevState:
        """
        Documentation phase: Generate component library documentation.

        Creates component docs, design system docs, setup guides.
        """
        logger.info("UI Development: Documentation phase")
        state = state.copy()

        if not state.get("testing_completed"):
            logger.warning("Skipping documentation: testing not completed")
            return state

        try:
            prompt = GENERATE_DOCS_PROMPT.format(
                component_specs=json.dumps(
                    state.get("ui_design", {}).get("component_specs", {}), indent=2
                ),
                design_system=json.dumps(
                    state.get("ui_design", {}).get("design_system", {}), indent=2
                ),
                pages=json.dumps(state.get("ui_plan", {}).get("pages", []), indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                docs_output = json.loads(response_text)
            except json.JSONDecodeError:
                docs_output = self._extract_json(response_text)

            state["docs_output"] = docs_output
            state["documentation_completed"] = True
            state["execution_notes"] += "Documentation phase completed. "
            state["status"] = "success"
            logger.info("Documentation phase completed")

        except Exception as e:
            logger.error(f"Error in documentation phase: {str(e)}")
            state["documentation_errors"].append(str(e))
            state["documentation_completed"] = True
            state["status"] = "partial"

        return state

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from text response.

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON or empty dict
        """
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
