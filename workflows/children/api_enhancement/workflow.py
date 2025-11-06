"""
API Enhancement child workflow implementation.

This workflow handles API enhancement lifecycle:
1. Analysis: Analyzes enhancement requirements
2. Design: Creates design for enhancements
3. Code Generation: Generates enhancement code
4. Testing: Generates tests for enhancements
5. Monitoring: Sets up monitoring for enhanced API
"""

import json
import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from workflows.children.base import BaseChildWorkflow
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode
from workflows.children.api_enhancement.state import (
    ApiEnhancementState,
    create_initial_enhancement_state,
)
from workflows.children.api_enhancement.agents.execution_planner import APIEnhancementPlannerAgent
from core.llm import get_default_llm_client
from workflows.children.api_enhancement.prompts import (
    DESIGN_ENHANCEMENT_PROMPT,
    GENERATE_ENHANCEMENT_CODE_PROMPT,
    GENERATE_ENHANCEMENT_TESTS_PROMPT,
    SETUP_MONITORING_PROMPT,
    GENERATE_ENHANCEMENT_DOCS_PROMPT,
)

logger = logging.getLogger(__name__)


class APIEnhancementWorkflow(BaseChildWorkflow):
    """
    Child workflow for API enhancement.

    This workflow takes API enhancement requirements and generates:
    - Detailed enhancement plan and analysis
    - Design specifications for enhancements
    - Code implementations
    - Test specifications
    - Monitoring setup

    Internal phases:
    - analysis_node: Analyzes enhancement requirements
    - design_node: Designs enhancement specifications
    - code_generation_node: Generates enhancement code
    - testing_node: Generates test specifications
    - monitoring_node: Sets up monitoring
    - documentation_node: Generates enhancement documentation
    """

    def __init__(self):
        """Initialize the API Enhancement workflow."""
        super().__init__()
        self.planner_agent = APIEnhancementPlannerAgent()
        self.llm_client = get_default_llm_client()

    def get_metadata(self) -> WorkflowMetadata:
        """Return metadata about this workflow for the registry."""
        return WorkflowMetadata(
            name="api_enhancement",
            workflow_type="api_enhancement",
            description="Enhances existing APIs with new features including batch processing, webhooks, advanced filtering, and monitoring",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.children.api_enhancement.workflow",
            tags=["api", "enhancement", "optimization", "monitoring"],
        )

    async def create_graph(self) -> Any:
        """
        Create and pre-compile the LangGraph for API enhancement.

        Returns:
            Compiled StateGraph ready for invocation
        """
        logger.info("Creating API enhancement workflow graph")

        # Create the state graph
        graph = StateGraph(ApiEnhancementState)

        # Add nodes for each phase
        graph.add_node("analysis", self._analysis_node)
        graph.add_node("design", self._design_node)
        graph.add_node("code_generation", self._code_generation_node)
        graph.add_node("testing", self._testing_node)
        graph.add_node("monitoring", self._monitoring_node)
        graph.add_node("documentation", self._documentation_node)

        # Set entry point
        graph.set_entry_point("analysis")

        # Create the pipeline
        graph.add_edge("analysis", "design")
        graph.add_edge("design", "code_generation")
        graph.add_edge("code_generation", "testing")
        graph.add_edge("testing", "monitoring")
        graph.add_edge("monitoring", "documentation")
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
            logger.warning("API Enhancement: Missing input_story from parent state")
            return False

        if not state.get("preprocessor_output"):
            logger.warning("API Enhancement: Missing preprocessor_output from parent state")
            return False

        logger.info("API Enhancement input validation passed")
        return True

    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """
        Execute the API enhancement workflow.

        Args:
            state: The parent workflow state

        Returns:
            Dict with status, output, artifacts, and execution_time_seconds
        """
        import time
        start_time = time.time()

        logger.info("Executing API Enhancement workflow")

        try:
            if not await self.validate_input(state):
                execution_time = time.time() - start_time
                return {
                    "status": "failure",
                    "error": "Invalid input state for API enhancement",
                    "output": {},
                    "artifacts": [],
                    "execution_time_seconds": execution_time,
                }

            # Extract input story and requirements from parent state
            input_story = state.get("input_story", "")
            preprocessor_output = state.get("preprocessor_output", {})
            story_requirements = preprocessor_output.get("extracted_data", {})

            # Create initial internal state
            internal_state = create_initial_enhancement_state(
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
                f"API Enhancement workflow completed in {execution_time:.2f}s "
                f"with status: {final_state.get('status')}"
            )

            return {
                "status": "success" if final_state.get("status") == "success" else "partial",
                "output": {
                    "enhancement_analysis": final_state.get("enhancement_analysis"),
                    "enhancement_design": final_state.get("enhancement_design"),
                    "enhancement_code": final_state.get("enhancement_code"),
                    "enhancement_tests": final_state.get("enhancement_tests"),
                    "monitoring_setup": final_state.get("monitoring_setup"),
                },
                "artifacts": artifacts,
                "execution_time_seconds": execution_time,
            }

        except Exception as e:
            logger.error(f"Error executing API Enhancement workflow: {str(e)}", exc_info=True)
            execution_time = time.time() - start_time
            return {
                "status": "failure",
                "output": {"error": str(e)},
                "artifacts": [],
                "execution_time_seconds": execution_time,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def _analysis_node(self, state: ApiEnhancementState) -> ApiEnhancementState:
        """
        Analysis phase: Analyze enhancement requirements.

        Evaluates scope, impact, and strategy for enhancements.
        """
        logger.info("API Enhancement: Analysis phase")
        state = state.copy()

        try:
            # Call the planner agent
            result = await self.planner_agent.analyze_enhancement_requirements(
                story_requirements=state.get("story_requirements", {}),
                api_structure=state.get("parent_context", {}).get("api_structure"),
            )

            if result["success"]:
                state["enhancement_analysis"] = result["analysis"]
                state["analysis_completed"] = True
                state["execution_notes"] += "Analysis completed successfully. "
                logger.info("Enhancement analysis completed")
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

    async def _design_node(self, state: ApiEnhancementState) -> ApiEnhancementState:
        """Design phase: Design enhancement specifications."""
        logger.info("API Enhancement: Design phase")
        state = state.copy()

        if not state.get("analysis_completed") or not state.get("enhancement_analysis"):
            logger.warning("Skipping design phase: analysis not completed")
            return state

        try:
            prompt = DESIGN_ENHANCEMENT_PROMPT.format(
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
            logger.info("Enhancement design completed")

        except Exception as e:
            logger.error(f"Error in design phase: {str(e)}")
            state["design_errors"].append(str(e))
            state["design_completed"] = True

        return state

    async def _code_generation_node(self, state: ApiEnhancementState) -> ApiEnhancementState:
        """Code generation phase: Generate enhancement code."""
        logger.info("API Enhancement: Code generation phase")
        state = state.copy()

        if not state.get("design_completed"):
            logger.warning("Skipping code generation: design not completed")
            return state

        try:
            prompt = GENERATE_ENHANCEMENT_CODE_PROMPT.format(
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

    async def _testing_node(self, state: ApiEnhancementState) -> ApiEnhancementState:
        """Testing phase: Generate test specifications."""
        logger.info("API Enhancement: Testing phase")
        state = state.copy()

        if not state.get("code_generation_completed"):
            logger.warning("Skipping testing: code generation not completed")
            return state

        try:
            prompt = GENERATE_ENHANCEMENT_TESTS_PROMPT.format(
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

    async def _monitoring_node(self, state: ApiEnhancementState) -> ApiEnhancementState:
        """Monitoring phase: Set up monitoring for enhancements."""
        logger.info("API Enhancement: Monitoring setup phase")
        state = state.copy()

        if not state.get("testing_completed"):
            logger.warning("Skipping monitoring: testing not completed")
            return state

        try:
            prompt = SETUP_MONITORING_PROMPT.format(
                enhancement_design=json.dumps(state.get("enhancement_design", {}), indent=2),
                enhancement_analysis=json.dumps(state.get("enhancement_analysis", {}), indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                monitoring_output = json.loads(response_text)
            except json.JSONDecodeError:
                monitoring_output = self._extract_json(response_text)

            state["monitoring_setup"] = monitoring_output
            state["monitoring_completed"] = True
            state["execution_notes"] += "Monitoring setup completed. "
            logger.info("Monitoring setup completed")

        except Exception as e:
            logger.error(f"Error in monitoring setup: {str(e)}")
            state["monitoring_errors"].append(str(e))
            state["monitoring_completed"] = True

        return state

    async def _documentation_node(self, state: ApiEnhancementState) -> ApiEnhancementState:
        """Documentation phase: Generate documentation."""
        logger.info("API Enhancement: Documentation phase")
        state = state.copy()

        if not state.get("monitoring_completed"):
            logger.warning("Skipping documentation: monitoring not completed")
            return state

        try:
            prompt = GENERATE_ENHANCEMENT_DOCS_PROMPT.format(
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
