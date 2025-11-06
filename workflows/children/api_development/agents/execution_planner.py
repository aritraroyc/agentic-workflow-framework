"""
API Planning Agent for the API Development workflow.

This agent analyzes the input story and creates a detailed API development plan
including endpoint definitions, framework choice, authentication method, etc.
"""

import json
import logging
from typing import Dict, Any, Optional

from core.llm import get_default_llm_client
from workflows.children.api_development.prompts import (
    VALIDATE_REQUIREMENTS_PROMPT,
    PLAN_API_PROMPT,
)
from workflows.children.api_development.state import ApiPlanOutput

logger = logging.getLogger(__name__)


class ApiPlannerAgent:
    """
    Agent responsible for planning the API development.

    This agent:
    1. Validates that the input story has sufficient API information
    2. Creates a detailed API plan including endpoints, framework, authentication, etc.
    3. Identifies required dependencies and architecture decisions
    """

    def __init__(self):
        """Initialize the API planner agent."""
        self.llm_client = get_default_llm_client()

    async def validate_requirements(
        self, story: str, requirements: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Validate that the story has sufficient information for API development.

        Args:
            story: The input markdown story
            requirements: Extracted requirements from preprocessor

        Returns:
            Tuple of (is_valid, assessment_message)
        """
        try:
            logger.info("Validating API requirements")

            prompt = VALIDATE_REQUIREMENTS_PROMPT.format(story=story)

            response = await self.llm_client.invoke(
                [{"role": "system", "content": "You are an API requirements validator."},
                 {"role": "user", "content": prompt}]
            )

            # Try to parse as JSON
            try:
                validation_result = json.loads(response)
                is_valid = validation_result.get("is_valid", False)
                summary = validation_result.get("summary", "Validation completed")
                missing = validation_result.get("missing_elements", [])

                if missing:
                    logger.warning(f"Missing elements in story: {missing}")

                return is_valid, summary
            except json.JSONDecodeError:
                # If not JSON, make a basic decision
                has_endpoints = "endpoint" in story.lower() or "api" in story.lower()
                has_methods = any(
                    method in story.upper() for method in ["GET", "POST", "PUT", "DELETE"]
                )
                is_valid = has_endpoints or has_methods

                return is_valid, response

        except Exception as e:
            logger.error(f"Error validating requirements: {str(e)}", exc_info=True)
            return False, f"Error validating requirements: {str(e)}"

    async def plan_api(
        self, story: str, requirements: Dict[str, Any]
    ) -> Optional[ApiPlanOutput]:
        """
        Create a detailed API development plan.

        Args:
            story: The input markdown story
            requirements: Extracted requirements from preprocessor

        Returns:
            ApiPlanOutput with detailed plan, or None if planning fails
        """
        try:
            logger.info("Planning API development")

            prompt = PLAN_API_PROMPT.format(
                story=story, requirements=json.dumps(requirements, indent=2)
            )

            response = await self.llm_client.invoke(
                [
                    {
                        "role": "system",
                        "content": "You are an expert API architect. Return ONLY valid JSON, no additional text.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            # Parse the JSON response
            try:
                plan_dict = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse plan JSON: {str(e)}")
                logger.debug(f"Response was: {response[:500]}")
                # Provide a minimal fallback plan
                plan_dict = self._create_fallback_plan(story, requirements)

            # Validate and structure the plan
            plan_output: ApiPlanOutput = {
                "api_name": plan_dict.get("api_name", "Generated API"),
                "api_description": plan_dict.get(
                    "api_description", "REST API generated from story"
                ),
                "base_path": plan_dict.get("base_path", "/api/v1"),
                "framework": plan_dict.get("framework", "FastAPI"),
                "authentication_method": plan_dict.get("authentication_method", "None"),
                "database_type": plan_dict.get("database_type"),
                "has_database": plan_dict.get("has_database", False),
                "required_dependencies": plan_dict.get(
                    "required_dependencies", ["fastapi", "uvicorn", "pydantic"]
                ),
                "requirements": plan_dict.get("requirements", []),
                "architecture_notes": plan_dict.get("architecture_notes", ""),
                "design_decisions": plan_dict.get("design_decisions", ""),
            }

            logger.info(
                f"API plan created: {plan_output['api_name']} "
                f"({len(plan_output.get('requirements', []))} endpoints)"
            )

            return plan_output

        except Exception as e:
            logger.error(f"Error planning API: {str(e)}", exc_info=True)
            return None

    def _create_fallback_plan(
        self, story: str, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a fallback plan when LLM fails or returns invalid JSON.

        Args:
            story: The input story
            requirements: Extracted requirements

        Returns:
            A minimal but valid API plan
        """
        logger.info("Creating fallback API plan")

        # Extract basic info from story
        api_name = requirements.get("title", "Generated API")
        api_description = requirements.get("description", story.split("\n")[0])

        # Default endpoints
        endpoints = [
            {
                "endpoint": "/health",
                "method": "GET",
                "description": "Health check endpoint",
                "authentication_required": False,
                "tags": ["health"],
                "status_codes": [200],
            }
        ]

        return {
            "api_name": api_name,
            "api_description": api_description,
            "base_path": "/api/v1",
            "framework": "FastAPI",
            "authentication_method": "None",
            "database_type": None,
            "has_database": False,
            "required_dependencies": ["fastapi", "uvicorn", "pydantic"],
            "requirements": endpoints,
            "architecture_notes": "Basic REST API with minimal features",
            "design_decisions": "Created with fallback plan due to insufficient input details",
        }
