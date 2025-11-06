"""
UI Enhancement Planner Agent.

This agent uses the LLM to analyze UI enhancement requirements and create
a detailed plan for implementing the enhancements.
"""

import json
import logging
from typing import Dict, Any, Optional

from core.llm import get_default_llm_client
from workflows.children.ui_enhancement.prompts import ANALYZE_UI_ENHANCEMENT_PROMPT

logger = logging.getLogger(__name__)


class UIEnhancementPlannerAgent:
    """
    Agent that plans UI enhancements based on requirements.

    Uses LLM to analyze enhancement requirements and create a comprehensive plan including:
    - Enhancement scope analysis
    - Design impact assessment
    - Component refactoring strategy
    - Accessibility improvement plan
    """

    def __init__(self):
        """Initialize the UI enhancement planner agent."""
        self.llm_client = get_default_llm_client()

    async def analyze_enhancement_requirements(
        self,
        story_requirements: Dict[str, Any],
        ui_structure: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze UI enhancement requirements using LLM.

        Args:
            story_requirements: Requirements extracted from the story
            ui_structure: Current UI structure (if available)

        Returns:
            Dictionary containing the enhancement analysis
        """
        logger.info("Analyzing UI enhancement requirements")

        try:
            # Format the prompt
            prompt = ANALYZE_UI_ENHANCEMENT_PROMPT.format(
                story_requirements=json.dumps(story_requirements, indent=2),
                ui_structure=json.dumps(ui_structure or {}, indent=2),
            )

            # Call the LLM
            logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            # Parse the JSON response
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON directly, attempting extraction")
                analysis = self._extract_json(response_text)

            logger.info("UI enhancement analysis created successfully")
            return {
                "analysis": analysis,
                "errors": [],
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error analyzing UI enhancements: {str(e)}")
            return {
                "analysis": self._generate_fallback_analysis(story_requirements),
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

    def _generate_fallback_analysis(
        self, story_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a fallback analysis if LLM fails.

        Args:
            story_requirements: Requirements from the story

        Returns:
            A basic analysis structure
        """
        logger.info("Generating fallback UI enhancement analysis")

        return {
            "current_ui_summary": "Existing React component library",
            "total_components": 20,
            "enhancements": [
                {
                    "name": "Accessibility Improvements",
                    "type": "accessibility",
                    "description": "Improve WCAG AA compliance",
                    "affected_components": ["Button", "Card", "Modal", "Form"],
                    "complexity": "medium",
                    "effort": "1 week",
                    "wcag_target": "AA",
                },
                {
                    "name": "Performance Optimization",
                    "type": "performance",
                    "description": "Optimize component rendering",
                    "affected_components": ["List", "Table", "Grid"],
                    "complexity": "medium",
                    "effort": "1 week",
                    "wcag_target": "AA",
                },
                {
                    "name": "UX Improvements",
                    "type": "ux_improvement",
                    "description": "Improve user experience",
                    "affected_components": ["Navigation", "Form", "Dropdown"],
                    "complexity": "low",
                    "effort": "3-5 days",
                    "wcag_target": "AA",
                },
            ],
            "design_impact": "Moderate refactoring of existing components",
            "migration_strategy": "Backward compatible changes with deprecation notices",
            "components_to_update": ["Button", "Card", "Form", "Modal", "Navigation"],
            "timeline_estimate": "2-3 weeks",
        }
