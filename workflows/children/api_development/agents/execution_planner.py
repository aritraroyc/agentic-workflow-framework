"""
API Planning Agent for the API Development workflow.

This agent analyzes the input story and creates a detailed API development plan
including endpoint definitions, framework choice, authentication method, etc.
"""

import json
import logging
import asyncio
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

            response = await asyncio.to_thread(
                self.llm_client.invoke,
                [{"role": "system", "content": "You are an API requirements validator."},
                 {"role": "user", "content": prompt}]
            )

            # Try to parse as JSON
            try:
                response_text = response.content if hasattr(response, 'content') else str(response)
                validation_result = json.loads(response_text)
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

                response_text = response.content if hasattr(response, 'content') else str(response)
                return is_valid, response_text

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

            response = await asyncio.to_thread(
                self.llm_client.invoke,
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
                response_text = response.content if hasattr(response, 'content') else str(response)
                plan_dict = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse plan JSON: {str(e)}")
                response_text = response.content if hasattr(response, 'content') else str(response)
                logger.debug(f"Response was: {response_text[:500]}")
                # Provide a minimal fallback plan
                plan_dict = self._create_fallback_plan(story, requirements)

            # Validate and structure the plan
            framework = plan_dict.get("framework", "FastAPI")
            plan_output: ApiPlanOutput = {
                "api_name": plan_dict.get("api_name", "Generated API"),
                "api_description": plan_dict.get(
                    "api_description", "REST API generated from story"
                ),
                "base_path": plan_dict.get("base_path", "/api/v1"),
                "framework": framework,
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

            # Add Java/Spring Boot specific fields if applicable
            if framework == "Spring Boot":
                plan_output["java_version"] = plan_dict.get("java_version", "21")
                plan_output["build_tool"] = plan_dict.get("build_tool", "Maven")
                plan_output["spring_boot_starters"] = plan_dict.get("spring_boot_starters", [
                    "spring-boot-starter-web",
                    "spring-boot-starter-data-jpa",
                    "spring-boot-starter-validation"
                ])
                plan_output["spring_security_config"] = plan_dict.get(
                    "spring_security_config", "JWT with Spring Security 6.x"
                )

            logger.info(
                f"API plan created: {plan_output['api_name']} "
                f"({len(plan_output.get('requirements', []))} endpoints)"
            )

            return plan_output

        except Exception as e:
            logger.error(f"Error planning API: {str(e)}", exc_info=True)
            return None

    def _is_python_framework(self, story: str) -> bool:
        """
        Detect if the story explicitly mentions Python framework.

        Args:
            story: The input story text

        Returns:
            True if Python/Python frameworks explicitly mentioned, False otherwise
        """
        python_keywords = [
            "python", "fastapi", "flask", "django", "async", "asyncio",
            "pip", "requirements.txt", "poetry", "uvicorn", "gunicorn",
            "pytest", "pydantic", "sqlalchemy"
        ]
        story_lower = story.lower()
        return any(keyword in story_lower for keyword in python_keywords)

    def _create_fallback_plan(
        self, story: str, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a fallback plan when LLM fails or returns invalid JSON.

        Defaults to Java/Spring Boot unless Python is explicitly mentioned.

        Args:
            story: The input story
            requirements: Extracted requirements

        Returns:
            A minimal but valid API plan
        """
        logger.info("Creating fallback API plan")

        # Detect if Python is explicitly mentioned (prefer Python if mentioned)
        is_python = self._is_python_framework(story)

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

        # Create plan based on detected framework
        # Default to Java/Spring Boot unless Python is explicitly mentioned
        if is_python:
            logger.info("Detected Python framework explicitly in story")
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
                "architecture_notes": "FastAPI REST API",
                "design_decisions": "Created with fallback plan using Python/FastAPI",
            }
        else:
            logger.info("Defaulting to Java/Spring Boot framework (no explicit Python mention)")
            return {
                "api_name": api_name,
                "api_description": api_description,
                "base_path": "/api/v1",
                "framework": "Spring Boot",
                "java_version": "21",
                "build_tool": "Maven",
                "authentication_method": "Spring Security",
                "database_type": "PostgreSQL",
                "has_database": True,
                "required_dependencies": ["spring-boot-starter-web", "spring-boot-starter-data-jpa"],
                "spring_boot_starters": [
                    "spring-boot-starter-web",
                    "spring-boot-starter-data-jpa",
                    "spring-boot-starter-security",
                    "spring-boot-starter-validation"
                ],
                "spring_security_config": "JWT with Spring Security 6.x",
                "requirements": endpoints,
                "architecture_notes": "Spring Boot REST API with JPA and Spring Security",
                "design_decisions": "Created with fallback plan defaulting to Java/Spring Boot framework",
            }
