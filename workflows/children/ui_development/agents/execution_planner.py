"""
UI Planner Agent for UI Development workflow.

This agent uses the LLM to analyze UI requirements and create a detailed plan
for UI development including component definitions, pages, and architecture.
"""

import json
import logging
from typing import Dict, Any, Optional

from core.llm import get_default_llm_client
from workflows.children.ui_development.prompts import PLAN_UI_PROMPT

logger = logging.getLogger(__name__)


class UIPlannerAgent:
    """
    Agent that plans UI development based on requirements.

    Uses LLM to analyze UI requirements and create a comprehensive plan including:
    - List of components needed
    - Page structure
    - Framework selection
    - State management approach
    - Accessibility requirements
    """

    def __init__(self):
        """Initialize the UI planner agent."""
        self.llm_client = get_default_llm_client()

    async def plan_ui_development(
        self,
        story_requirements: Dict[str, Any],
        framework_preference: str = "React",
        typescript_enabled: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a comprehensive UI development plan using LLM.

        Args:
            story_requirements: Requirements extracted from the story
            framework_preference: Preferred framework (React, Vue, Angular)
            typescript_enabled: Whether to use TypeScript

        Returns:
            Dictionary containing the UI plan with components, pages, dependencies, etc.
        """
        logger.info("Planning UI development")

        try:
            # Format the prompt
            prompt = PLAN_UI_PROMPT.format(
                story_requirements=json.dumps(story_requirements, indent=2),
                framework_preference=framework_preference,
                typescript=typescript_enabled,
            )

            # Call the LLM
            logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            # Parse the JSON response
            try:
                plan = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                logger.warning("Failed to parse JSON directly, attempting extraction")
                plan = self._extract_json(response_text)

            logger.info("UI development plan created successfully")
            return {
                "ui_plan": plan,
                "errors": [],
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error creating UI plan: {str(e)}")
            return {
                "ui_plan": self._generate_fallback_plan(
                    story_requirements, framework_preference, typescript_enabled
                ),
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
        # Find the first { and last }
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

    def _generate_fallback_plan(
        self,
        story_requirements: Dict[str, Any],
        framework_preference: str,
        typescript_enabled: bool,
    ) -> Dict[str, Any]:
        """
        Generate a fallback UI plan if LLM fails.

        Args:
            story_requirements: Requirements from the story
            framework_preference: Preferred framework
            typescript_enabled: Whether to use TypeScript

        Returns:
            A basic UI plan structure
        """
        logger.info("Generating fallback UI plan")

        components = [
            {
                "name": "Layout",
                "description": "Main layout component with header and navigation",
                "key_props": ["children"],
                "states": ["desktop", "mobile"],
                "events": [],
            },
            {
                "name": "Header",
                "description": "Header component with navigation",
                "key_props": ["title", "navigation_items"],
                "states": ["expanded", "collapsed"],
                "events": ["onClick"],
            },
            {
                "name": "Footer",
                "description": "Footer component",
                "key_props": ["content"],
                "states": [],
                "events": [],
            },
            {
                "name": "Card",
                "description": "Reusable card component",
                "key_props": ["title", "content", "actions"],
                "states": ["default", "hover"],
                "events": ["onClick"],
            },
            {
                "name": "Button",
                "description": "Reusable button component",
                "key_props": ["label", "onClick", "variant"],
                "states": ["default", "hover", "active", "disabled"],
                "events": ["onClick"],
            },
        ]

        return {
            "project_name": story_requirements.get("title", "UI Project"),
            "description": story_requirements.get("description", ""),
            "target_framework": framework_preference,
            "typescript_enabled": typescript_enabled,
            "components": components,
            "pages": ["Home", "NotFound"],
            "required_dependencies": [
                "react" if framework_preference == "React" else framework_preference.lower(),
                "typescript" if typescript_enabled else "javascript",
            ],
            "design_system_needed": True,
            "responsive_design": True,
            "accessibility_level": "AA",
            "state_management": "React Context" if framework_preference == "React" else "Store",
            "architecture_notes": "Standard component-based architecture",
        }
