"""
API Development child workflow implementation.

This workflow handles the complete API development lifecycle:
1. Planning: Analyzes requirements and creates API plan
2. Design: Creates OpenAPI specification
3. Code Generation: Generates Python code
4. Testing: Generates test cases
5. Documentation: Creates API documentation
"""

import json
import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from workflows.children.base import BaseChildWorkflow
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode
from workflows.children.api_development.state import (
    ApiDevelopmentState,
    create_initial_api_state,
)
from workflows.children.api_development.agents.execution_planner import ApiPlannerAgent
from core.llm import get_default_llm_client
from workflows.children.api_development.prompts import (
    DESIGN_API_PROMPT,
    GENERATE_CODE_PROMPT,
    GENERATE_TESTS_PROMPT,
    GENERATE_DOCS_PROMPT,
)

logger = logging.getLogger(__name__)


class ApiDevelopmentWorkflow(BaseChildWorkflow):
    """
    Child workflow for API development.

    This workflow takes API requirements from the parent workflow and generates
    a complete, production-ready API implementation including:
    - Detailed API plan
    - OpenAPI specification
    - FastAPI/Flask application code
    - Unit tests
    - API documentation

    Internal phases:
    - planning_node: Creates detailed API plan
    - design_node: Creates OpenAPI specification
    - code_generation_node: Generates application code
    - testing_node: Generates unit tests
    - documentation_node: Generates API documentation
    """

    def __init__(self):
        """Initialize the API Development workflow."""
        super().__init__()
        self.planner_agent = ApiPlannerAgent()
        self.llm_client = get_default_llm_client()

    def get_metadata(self) -> WorkflowMetadata:
        """Return metadata about this workflow for the registry."""
        return WorkflowMetadata(
            name="api_development",
            workflow_type="api_development",
            description="Develops complete RESTful APIs from requirements including design, code generation, testing, and documentation",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.children.api_development.workflow",
            tags=["api", "development", "rest", "fastapi"],
        )

    async def create_graph(self) -> Any:
        """
        Create and pre-compile the LangGraph for API development.

        Returns:
            Compiled StateGraph ready for invocation
        """
        logger.info("Creating API development workflow graph")

        # Create the state graph
        graph = StateGraph(ApiDevelopmentState)

        # Add nodes for each phase
        graph.add_node("planning", self._planning_node)
        graph.add_node("design", self._design_node)
        graph.add_node("code_generation", self._code_generation_node)
        graph.add_node("testing", self._testing_node)
        graph.add_node("documentation", self._documentation_node)

        # Set entry point
        graph.set_entry_point("planning")

        # Create the pipeline
        graph.add_edge("planning", "design")
        graph.add_edge("design", "code_generation")
        graph.add_edge("code_generation", "testing")
        graph.add_edge("testing", "documentation")
        graph.set_finish_point("documentation")

        logger.info("API development workflow graph created successfully")
        return graph.compile()

    async def validate_input(self, state: EnhancedWorkflowState) -> bool:
        """
        Validate that the parent workflow state has required inputs.

        Args:
            state: Parent workflow state

        Returns:
            True if state has required API development inputs, False otherwise
        """
        try:
            # Check for required preprocessor output
            if not state.get("preprocessor_output"):
                logger.warning("Missing preprocessor_output in parent state")
                return False

            preprocessor_output = state["preprocessor_output"]

            # Check that extracted_data field exists (can be empty dict)
            if "extracted_data" not in preprocessor_output:
                logger.warning("Missing extracted_data field in preprocessor output")
                return False

            logger.info("Input validation passed for API development workflow")
            return True

        except Exception as e:
            logger.error(f"Error validating input: {str(e)}", exc_info=True)
            return False

    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """
        Execute the API development workflow.

        Args:
            state: Parent workflow state

        Returns:
            Dict with status, output, artifacts, and execution_time_seconds
        """
        try:
            import time
            start_time = time.time()

            # Validate input
            if not await self.validate_input(state):
                raise ValueError("Parent state validation failed")

            logger.info("Starting API development workflow execution")

            # Get the compiled graph
            graph = await self.get_compiled_graph()

            # Extract input story and requirements from parent state
            input_story = state.get("input_story", "")
            preprocessor_output = state.get("preprocessor_output", {})
            story_requirements = preprocessor_output.get("extracted_data", {})

            # Create initial child workflow state
            child_state = create_initial_api_state(
                input_story=input_story,
                story_requirements=story_requirements,
                parent_context=state.get("context", {}),
            )

            # Invoke the graph asynchronously
            result_state = await graph.ainvoke(child_state)

            # Collect artifacts
            artifacts = result_state.get("all_artifacts", [])

            execution_time = time.time() - start_time

            logger.info(
                f"API development workflow completed in {execution_time:.2f}s "
                f"with status: {result_state.get('status')}"
            )

            return {
                "status": "success" if result_state.get("status") == "success" else "partial",
                "output": {
                    "api_plan": result_state.get("api_plan"),
                    "api_design": result_state.get("api_design"),
                    "code_output": result_state.get("code_output"),
                    "test_output": result_state.get("test_output"),
                    "docs_output": result_state.get("docs_output"),
                    "execution_notes": result_state.get("execution_notes"),
                },
                "artifacts": artifacts,
                "execution_time_seconds": execution_time,
            }

        except Exception as e:
            logger.error(
                f"Error executing API development workflow: {str(e)}", exc_info=True
            )
            return {
                "status": "failure",
                "output": {"error": str(e)},
                "artifacts": [],
                "execution_time_seconds": 0.0,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    # ========== Helper Methods ==========

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response, handling various formats.

        Handles:
        - Pure JSON responses
        - JSON wrapped in markdown code blocks (```json {...}```)
        - JSON with surrounding text

        Args:
            response_text: Raw response from LLM

        Returns:
            Parsed JSON dictionary, or empty dict if extraction fails
        """
        if not response_text or not response_text.strip():
            logger.debug("Response text is empty")
            return {}

        # Try direct JSON parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        import re
        markdown_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        matches = re.findall(markdown_pattern, response_text)
        if matches:
            for match in matches:
                try:
                    logger.debug("Found JSON in markdown code block")
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # Try to extract JSON by finding braces
        start = response_text.find("{")
        end = response_text.rfind("}") + 1

        if start != -1 and end > start:
            try:
                json_str = response_text[start:end]
                logger.debug("Extracted JSON from response text")
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not extract valid JSON from response (first 200 chars): {response_text[:200]}")
        return {}

    # ========== Internal Node Functions ==========

    async def _planning_node(self, state: ApiDevelopmentState) -> ApiDevelopmentState:
        """Plan the API development."""
        try:
            logger.info("Planning API development")

            # Validate requirements
            is_valid, validation_msg = await self.planner_agent.validate_requirements(
                state["input_story"], state["story_requirements"]
            )

            if not is_valid:
                logger.warning(f"Input validation warning: {validation_msg}")

            # Create API plan
            api_plan = await self.planner_agent.plan_api(
                state["input_story"], state["story_requirements"]
            )

            if not api_plan:
                state["planning_errors"].append("Failed to create API plan")
                logger.error("API planning failed")
            else:
                state["api_plan"] = api_plan
                state["planning_completed"] = True
                logger.info(
                    f"API planning completed: {api_plan.get('api_name')} "
                    f"with {len(api_plan.get('requirements', []))} endpoints"
                )

            return state

        except Exception as e:
            logger.error(f"Error in planning node: {str(e)}", exc_info=True)
            state["planning_errors"].append(str(e))
            return state

    async def _design_node(self, state: ApiDevelopmentState) -> ApiDevelopmentState:
        """Design the API with OpenAPI specification."""
        try:
            if not state.get("api_plan"):
                logger.warning("Skipping design node: no API plan available")
                return state

            logger.info("Designing API with OpenAPI specification")

            prompt = DESIGN_API_PROMPT.format(
                plan=json.dumps(state["api_plan"], indent=2)
            )

            response = await self.llm_client.invoke(
                [
                    {
                        "role": "system",
                        "content": "You are an expert in OpenAPI specification design. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            logger.debug(f"Design response (first 300 chars): {response[:300]}")

            design_dict = self._extract_json_from_response(response)

            if design_dict:
                state["api_design"] = design_dict
                state["design_completed"] = True
                logger.info("API design completed")
            else:
                logger.warning("Design response did not contain valid JSON")
                state["design_errors"].append("Failed to extract valid JSON from design response")

            return state

        except Exception as e:
            logger.error(f"Error in design node: {str(e)}", exc_info=True)
            state["design_errors"].append(str(e))
            return state

    async def _code_generation_node(
        self, state: ApiDevelopmentState
    ) -> ApiDevelopmentState:
        """Generate code for the API."""
        try:
            if not state.get("api_plan"):
                logger.warning("Skipping code generation: no API plan available")
                return state

            logger.info("Generating API code")

            framework = state["api_plan"].get("framework", "FastAPI")
            design_str = (
                json.dumps(state.get("api_design", {}), indent=2)
                if state.get("api_design")
                else "{}"
            )

            prompt = GENERATE_CODE_PROMPT.format(
                framework=framework,
                plan=json.dumps(state["api_plan"], indent=2),
                design=design_str,
            )

            response = await self.llm_client.invoke(
                [
                    {
                        "role": "system",
                        "content": f"You are an expert {framework} developer. Generate production-ready code. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            logger.debug(f"Code generation response (first 300 chars): {response[:300]}")

            code_dict = self._extract_json_from_response(response)

            if code_dict:
                # Store the generated code (in production, would write to files)
                state["code_output"] = code_dict
                state["code_generation_completed"] = True
                state["all_artifacts"].extend(code_dict.get("generated_files", []))
                logger.info("Code generation completed")
            else:
                logger.warning("Code generation response did not contain valid JSON")
                state["code_generation_errors"].append("Failed to extract valid JSON from code generation response")

            return state

        except Exception as e:
            logger.error(f"Error in code generation node: {str(e)}", exc_info=True)
            state["code_generation_errors"].append(str(e))
            return state

    async def _testing_node(self, state: ApiDevelopmentState) -> ApiDevelopmentState:
        """Generate tests for the API."""
        try:
            if not state.get("code_output"):
                logger.warning("Skipping testing: no code output available")
                return state

            logger.info("Generating API tests")

            code_summary = json.dumps(
                {
                    "main_file": state["code_output"].get("main_file", "")[: 200],
                    "has_models": bool(state["code_output"].get("models_file")),
                    "has_schemas": bool(state["code_output"].get("schemas_file")),
                },
                indent=2,
            )

            prompt = GENERATE_TESTS_PROMPT.format(
                plan=json.dumps(state.get("api_plan", {}), indent=2),
                code=code_summary,
            )

            response = await self.llm_client.invoke(
                [
                    {
                        "role": "system",
                        "content": "You are an expert test engineer. Generate comprehensive tests. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            logger.debug(f"Test generation response (first 300 chars): {response[:300]}")

            test_dict = self._extract_json_from_response(response)

            if test_dict:
                state["test_output"] = test_dict
                state["testing_completed"] = True
                state["all_artifacts"].extend(test_dict.get("generated_tests", []))
                logger.info("Test generation completed")
            else:
                logger.warning("Test generation response did not contain valid JSON")
                state["testing_errors"].append("Failed to extract valid JSON from test generation response")

            return state

        except Exception as e:
            logger.error(f"Error in testing node: {str(e)}", exc_info=True)
            state["testing_errors"].append(str(e))
            return state

    async def _documentation_node(
        self, state: ApiDevelopmentState
    ) -> ApiDevelopmentState:
        """Generate documentation for the API."""
        try:
            if not state.get("api_plan"):
                logger.warning("Skipping documentation: no API plan available")
                return state

            logger.info("Generating API documentation")

            design_summary = (
                json.dumps(state.get("api_design", {}), indent=2)[: 500]
                if state.get("api_design")
                else "Not yet designed"
            )
            code_summary = (
                "Code generated" if state.get("code_output") else "Code not yet generated"
            )

            prompt = GENERATE_DOCS_PROMPT.format(
                plan=json.dumps(state["api_plan"], indent=2),
                design=design_summary,
                code_summary=code_summary,
            )

            response = await self.llm_client.invoke(
                [
                    {
                        "role": "system",
                        "content": "You are an expert technical writer. Generate comprehensive API documentation. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            logger.debug(f"Documentation response (first 300 chars): {response[:300]}")

            docs_dict = self._extract_json_from_response(response)

            if docs_dict:
                state["docs_output"] = docs_dict
                state["documentation_completed"] = True
                state["all_artifacts"].extend(docs_dict.get("generated_docs", []))
                logger.info("Documentation generation completed")
            else:
                logger.warning("Documentation response did not contain valid JSON")
                state["documentation_errors"].append("Failed to extract valid JSON from documentation response")

            return state

        except Exception as e:
            logger.error(f"Error in documentation node: {str(e)}", exc_info=True)
            state["documentation_errors"].append(str(e))
            return state
