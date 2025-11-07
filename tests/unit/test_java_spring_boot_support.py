"""
Tests for Java/Spring Boot support in API Development and Enhancement workflows.

This module tests:
1. Java framework detection in planning agents
2. Fallback plan generation with Spring Boot configuration
3. State schema compatibility with Java/Spring Boot fields
4. Framework-specific output structure
"""

import pytest
import asyncio
from typing import Dict, Any

from workflows.children.api_development.agents.execution_planner import ApiPlannerAgent
from workflows.children.api_enhancement.agents.execution_planner import APIEnhancementPlannerAgent
from workflows.children.api_development.state import create_initial_api_state
from workflows.children.api_enhancement.state import create_initial_enhancement_state


class TestApiDevelopmentJavaDetection:
    """Test Java framework detection in API Development planning."""

    def test_java_keyword_detection_simple(self):
        """Test detection with simple Java mention."""
        agent = ApiPlannerAgent()

        story = "Build a Java REST API using Spring Boot"
        assert agent._is_python_framework(story) is False

    def test_spring_boot_keyword_detection(self):
        """Test detection with Spring Boot mention."""
        agent = ApiPlannerAgent()

        story = "Create a Spring Boot application with REST endpoints"
        assert agent._is_python_framework(story) is False

    def test_maven_gradle_detection(self):
        """Test detection with build tool mentions."""
        agent = ApiPlannerAgent()

        maven_story = "Use Maven to build the Java API"
        gradle_story = "Use Gradle for the Spring Boot project"

        assert agent._is_python_framework(maven_story) is False
        assert agent._is_python_framework(gradle_story) is False

    def test_python_not_detected_as_java(self):
        """Test that Python frameworks are detected as Python."""
        agent = ApiPlannerAgent()

        story = "Create a FastAPI Python application"
        assert agent._is_python_framework(story) is True

    def test_java_fallback_plan_structure(self):
        """Test fallback plan includes Spring Boot configuration."""
        agent = ApiPlannerAgent()

        story = "Build an enterprise Java API using Spring Boot 3.x and JPA"
        requirements: Dict[str, Any] = {
            "title": "Transaction API",
            "description": "Java Spring Boot API for transactions"
        }

        plan = agent._create_fallback_plan(story, requirements)

        # Verify Spring Boot framework is selected
        assert plan["framework"] == "Spring Boot"
        assert plan["java_version"] == "21"
        assert plan["build_tool"] == "Maven"

        # Verify Spring Boot specific fields
        assert "spring_boot_starters" in plan
        assert "spring-boot-starter-web" in plan["spring_boot_starters"]
        assert "spring-boot-starter-data-jpa" in plan["spring_boot_starters"]
        assert "spring_security_config" in plan

    def test_python_fallback_plan_structure(self):
        """Test fallback plan uses FastAPI for Python stories."""
        agent = ApiPlannerAgent()

        story = "Create a FastAPI REST API with async endpoints"
        requirements: Dict[str, Any] = {
            "title": "User API",
            "description": "Python FastAPI for user management"
        }

        plan = agent._create_fallback_plan(story, requirements)

        # Verify FastAPI framework is selected
        assert plan["framework"] == "FastAPI"
        assert "fastapi" in plan["required_dependencies"]
        assert "spring_boot_starters" not in plan


class TestApiEnhancementJavaDetection:
    """Test Java framework detection in API Enhancement planning."""

    def test_java_keyword_detection_simple(self):
        """Test detection with simple Java mention."""
        agent = APIEnhancementPlannerAgent()

        story = "Enhance a Java REST API"
        assert agent._is_python_framework(story) is False

    def test_spring_framework_detection(self):
        """Test detection with Spring Framework mention."""
        agent = APIEnhancementPlannerAgent()

        story = "Add new features to Spring Framework application"
        assert agent._is_python_framework(story) is False

    def test_jpa_hibernate_detection(self):
        """Test detection with ORM framework mentions."""
        agent = APIEnhancementPlannerAgent()

        jpa_story = "Enhance the API using JPA entities"
        hibernate_story = "Upgrade the Hibernate-based API"

        assert agent._is_python_framework(jpa_story) is False
        assert agent._is_python_framework(hibernate_story) is False

    def test_java_enhancement_fallback_analysis(self):
        """Test fallback analysis includes Java/Spring Boot configuration."""
        agent = APIEnhancementPlannerAgent()

        story_requirements: Dict[str, Any] = {
            "description": "Enhance Java Spring Boot API with batch processing and webhooks"
        }
        story_text = "Add batch processing to existing Java Spring Boot API"

        analysis = agent._generate_fallback_analysis(story_requirements, story_text)

        # Verify language/framework detection
        assert analysis.get("current_language") == "Java"
        assert analysis.get("current_framework") == "Spring Boot"

        # Verify Java/Spring Boot specific fields
        assert analysis.get("java_version") == "21"
        assert analysis.get("build_tool") == "Maven"
        assert "spring_boot_starters" in analysis
        assert "spring-boot-starter-web" in analysis["spring_boot_starters"]

    def test_python_enhancement_fallback_analysis(self):
        """Test fallback analysis uses Python for Python stories."""
        agent = APIEnhancementPlannerAgent()

        story_requirements: Dict[str, Any] = {
            "description": "Enhance FastAPI with async webhooks"
        }
        story_text = "Add webhook support to FastAPI application"

        analysis = agent._generate_fallback_analysis(story_requirements, story_text)

        # Verify Python framework is selected
        assert analysis.get("current_language") == "Python"
        assert analysis.get("current_framework") == "FastAPI"
        assert "spring_boot_starters" not in analysis


class TestStateSchemaJavaSupport:
    """Test state schema support for Java/Spring Boot fields."""

    def test_api_development_state_with_java_fields(self):
        """Test ApiDevelopmentState supports Java/Spring Boot fields."""
        state = create_initial_api_state(
            input_story="Build a Java Spring Boot API",
            story_requirements={},
            parent_context={}
        )

        # Verify state structure is correct
        assert "input_story" in state
        assert "planning_completed" in state
        assert "api_plan" in state

        # Java fields are optional in total=False TypedDict, so we can add them
        state["api_plan"] = {
            "api_name": "Test API",
            "framework": "Spring Boot",
            "java_version": "21",
            "build_tool": "Maven",
            "spring_boot_starters": ["spring-boot-starter-web"],
            "spring_security_config": "JWT"
        }

        assert state["api_plan"]["framework"] == "Spring Boot"
        assert state["api_plan"]["java_version"] == "21"

    def test_api_enhancement_state_with_java_fields(self):
        """Test ApiEnhancementState supports Java/Spring Boot fields."""
        state = create_initial_enhancement_state(
            input_story="Enhance Java API",
            story_requirements={},
            parent_context={}
        )

        # Verify state structure is correct
        assert "input_story" in state
        assert "analysis_completed" in state
        assert "enhancement_analysis" in state

        # Java fields are optional in total=False TypedDict, so we can add them
        state["enhancement_analysis"] = {
            "current_api_structure": {},
            "current_language": "Java",
            "current_framework": "Spring Boot",
            "java_version": "21",
            "build_tool": "Maven"
        }

        assert state["enhancement_analysis"]["current_language"] == "Java"
        assert state["enhancement_analysis"]["java_version"] == "21"


class TestFrameworkConsistency:
    """Test framework consistency across API Development and Enhancement."""

    def test_java_api_development_consistency(self):
        """Test Java API development uses consistent Spring Boot configuration."""
        dev_agent = ApiPlannerAgent()

        java_story = "Build a Java 21 REST API with Maven"
        requirements = {"title": "Test API"}

        dev_plan = dev_agent._create_fallback_plan(java_story, requirements)

        # Verify consistent Java/Spring Boot configuration
        assert dev_plan["framework"] == "Spring Boot"
        assert dev_plan["java_version"] == "21"
        assert dev_plan["build_tool"] == "Maven"

    def test_java_api_enhancement_consistency(self):
        """Test Java API enhancement maintains framework consistency."""
        enhancement_agent = APIEnhancementPlannerAgent()

        java_story = "Enhance existing Java Spring Boot API"
        requirements = {"description": java_story}

        analysis = enhancement_agent._generate_fallback_analysis(requirements, java_story)

        # Verify consistent Java/Spring Boot configuration
        assert analysis["current_framework"] == "Spring Boot"
        assert analysis["java_version"] == "21"
        assert analysis["build_tool"] == "Maven"

    def test_python_framework_consistency(self):
        """Test Python framework consistency across both workflows."""
        dev_agent = ApiPlannerAgent()
        enhancement_agent = APIEnhancementPlannerAgent()

        python_story = "Create a FastAPI microservice"
        requirements = {"title": "Test API", "description": python_story}

        dev_plan = dev_agent._create_fallback_plan(python_story, requirements)
        analysis = enhancement_agent._generate_fallback_analysis(requirements, python_story)

        # Verify consistent Python/FastAPI configuration
        assert dev_plan["framework"] == "FastAPI"
        assert analysis["current_framework"] == "FastAPI"


class TestMixedScenarios:
    """Test handling of edge cases and mixed scenarios."""

    def test_kotlin_detected_as_java(self):
        """Test Kotlin (Java ecosystem) is not detected as Python."""
        agent = ApiPlannerAgent()

        story = "Create a Kotlin REST API with Spring Boot"
        assert agent._is_python_framework(story) is False

    def test_enterprise_java_detected(self):
        """Test enterprise Java keywords are not detected as Python."""
        agent = ApiPlannerAgent()

        story = "Build enterprise Java application with J2EE patterns"
        assert agent._is_python_framework(story) is False

    def test_jakarta_namespace_detected(self):
        """Test Jakarta namespace (Java EE) is not detected as Python."""
        agent = APIEnhancementPlannerAgent()

        story = "Migrate from javax to jakarta namespace in Java API"
        assert agent._is_python_framework(story) is False

    def test_case_insensitive_detection(self):
        """Test framework detection is case insensitive."""
        agent = ApiPlannerAgent()

        upper_story = "BUILD A JAVA SPRING BOOT API"
        mixed_case_story = "Build a Java Spring Boot Api"

        assert agent._is_python_framework(upper_story) is False
        assert agent._is_python_framework(mixed_case_story) is False
