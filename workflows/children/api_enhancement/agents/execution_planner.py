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

            # Call the LLM - invoke() is already async
            logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
            response_text = await self.llm_client.invoke(
                [{
                    "role": "system",
                    "content": "You are an expert API architect analyzing enhancement requirements. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt}]
            )

            logger.debug(f"Enhancement analysis response (first 300 chars): {response_text[:300]}")

            # Parse the JSON response using robust extraction
            analysis = self._extract_json_from_response(response_text)

            if analysis:
                logger.info("Enhancement analysis created successfully")
                return {
                    "analysis": analysis,
                    "errors": [],
                    "success": True,
                }
            else:
                logger.warning("Failed to extract valid JSON from response, using fallback")
                story_text = story_requirements.get("description", "")
                return {
                    "analysis": self._generate_fallback_analysis(story_requirements, story_text),
                    "errors": ["Failed to parse JSON response"],
                    "success": False,
                }

        except Exception as e:
            logger.error(f"Error analyzing enhancements: {str(e)}")
            story_text = story_requirements.get("description", "")
            return {
                "analysis": self._generate_fallback_analysis(story_requirements, story_text),
                "errors": [str(e)],
                "success": False,
            }

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
