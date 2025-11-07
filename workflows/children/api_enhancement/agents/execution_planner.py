"""
API Enhancement Planner Agent.

This agent uses the LLM to analyze API enhancement requirements and create
a detailed plan for implementing the enhancements.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional

from core.llm import get_default_llm_client
from workflows.children.api_enhancement.prompts import ANALYZE_ENHANCEMENT_PROMPT

logger = logging.getLogger(__name__)


class APIEnhancementPlannerAgent:
    """
    Agent that plans API enhancements based on requirements.

    Uses LLM to analyze enhancement requirements and create a comprehensive plan including:
    - Enhancement scope analysis
    - Impact assessment
    - Versioning strategy
    - Migration approach
    """

    def __init__(self):
        """Initialize the API enhancement planner agent."""
        self.llm_client = get_default_llm_client()

    async def analyze_enhancement_requirements(
        self,
        story_requirements: Dict[str, Any],
        api_structure: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze API enhancement requirements using LLM.

        Args:
            story_requirements: Requirements extracted from the story
            api_structure: Current API structure (if available)

        Returns:
            Dictionary containing the enhancement analysis
        """
        logger.info("Analyzing API enhancement requirements")

        try:
            # Format the prompt
            prompt = ANALYZE_ENHANCEMENT_PROMPT.format(
                story_requirements=json.dumps(story_requirements, indent=2),
                api_structure=json.dumps(api_structure or {}, indent=2),
            )

            # Call the LLM
            logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
            response = await asyncio.to_thread(
                self.llm_client.invoke,
                [{
                    "role": "system",
                    "content": "You are an expert API architect analyzing enhancement requirements. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt}]
            )
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Parse the JSON response
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON directly, attempting extraction")
                analysis = self._extract_json(response_text)

            logger.info("Enhancement analysis created successfully")
            return {
                "analysis": analysis,
                "errors": [],
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error analyzing enhancements: {str(e)}")
            story_text = story_requirements.get("description", "")
            return {
                "analysis": self._generate_fallback_analysis(story_requirements, story_text),
                "errors": [str(e)],
                "success": False,
            }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from text that may contain additional content.

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON as dictionary
        """
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == 0:
            return {}

        json_str = text[start:end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Could not extract valid JSON from response")
            return {}

    def _is_python_framework(self, text: str) -> bool:
        """
        Detect if the text explicitly mentions Python framework.

        Args:
            text: The text to analyze

        Returns:
            True if Python/Python frameworks explicitly mentioned, False otherwise
        """
        python_keywords = [
            "python", "fastapi", "flask", "django", "async", "asyncio",
            "pip", "requirements.txt", "poetry", "uvicorn", "gunicorn",
            "pytest", "pydantic", "sqlalchemy"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in python_keywords)

    def _generate_fallback_analysis(
        self, story_requirements: Dict[str, Any], story_text: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a fallback analysis if LLM fails.

        Defaults to Java/Spring Boot unless Python is explicitly mentioned.

        Args:
            story_requirements: Requirements from the story
            story_text: Raw story text for framework detection

        Returns:
            A basic analysis structure
        """
        logger.info("Generating fallback enhancement analysis")

        # Detect if Python is explicitly mentioned (prefer Python if mentioned)
        is_python = self._is_python_framework(story_text) or \
                   self._is_python_framework(str(story_requirements.get("description", "")))

        base_analysis = {
            "current_api_summary": "Existing RESTful API",
            "enhancements": [
                {
                    "name": "New Filtering Capabilities",
                    "type": "filtering",
                    "description": "Add advanced filtering options",
                    "affected_endpoints": ["/api/resources"],
                    "complexity": "medium",
                    "effort": "2-3 days",
                    "breaking_change": False,
                },
                {
                    "name": "Batch Processing",
                    "type": "batch_processing",
                    "description": "Add batch processing endpoint",
                    "affected_endpoints": [],
                    "complexity": "high",
                    "effort": "1 week",
                    "breaking_change": False,
                },
                {
                    "name": "Webhooks",
                    "type": "webhooks",
                    "description": "Add webhook support for events",
                    "affected_endpoints": [],
                    "complexity": "high",
                    "effort": "1 week",
                    "breaking_change": False,
                },
            ],
            "architectural_impact": "Will require new services for webhooks and batch processing",
            "versioning_approach": "semantic versioning with URL versioning",
            "backward_compatibility": "Full backward compatibility maintained, new features optional",
            "timeline_estimate": "3-4 weeks",
            "dependencies": ["Redis for caching", "Message queue for webhooks"],
        }

        # Default to Java/Spring Boot unless Python is explicitly mentioned
        if is_python:
            logger.info("Detected Python framework explicitly in enhancement story")
            base_analysis["current_language"] = "Python"
            base_analysis["current_framework"] = "FastAPI"
        else:
            logger.info("Defaulting to Java/Spring Boot framework (no explicit Python mention)")
            base_analysis["current_language"] = "Java"
            base_analysis["current_framework"] = "Spring Boot"
            base_analysis["java_version"] = "21"
            base_analysis["build_tool"] = "Maven"
            base_analysis["spring_boot_starters"] = [
                "spring-boot-starter-web",
                "spring-boot-starter-data-jpa",
                "spring-boot-starter-security"
            ]
            base_analysis["spring_security_config"] = "JWT with Spring Security 6.x"

        return base_analysis
