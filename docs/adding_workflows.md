# Guide to Adding New Workflows

This guide walks you through creating a new child workflow for the Agentic Workflow Framework.

## Quick Summary

Creating a new workflow requires:
1. Define workflow state (TypedDict)
2. Create planner agent
3. Implement workflow class
4. Create prompts for LLM
5. Register in config/workflows.yaml
6. Add tests

**Time estimate**: 30-60 minutes for a complete workflow

## Step-by-Step Implementation

### Step 1: Plan Your Workflow

Before coding, define:

- **Workflow name** (snake_case): e.g., `database_migration`
- **Type classification**: e.g., `database_development`
- **Execution phases**: Sequential steps your workflow needs
- **Input requirements**: What data is required
- **Output artifacts**: What gets produced
- **LLM responsibilities**: Which phases need LLM assistance

Example:
```
Workflow: Database Migration
Type: database_development
Phases:
  1. Analysis: Analyze current schema
  2. Design: Design new schema
  3. Migration: Generate migration scripts
  4. Testing: Create test suite
  5. Documentation: Generate migration guide
```

### Step 2: Create Workflow Directory

```bash
mkdir -p workflows/children/database_migration
mkdir -p workflows/children/database_migration/agents
touch workflows/children/database_migration/__init__.py
touch workflows/children/database_migration/agents/__init__.py
```

### Step 3: Define Workflow State

Create `workflows/children/database_migration/state.py`:

```python
from typing import TypedDict, Optional
from typing_extensions import NotRequired

# Define output types for each phase
class SchemaAnalysis(TypedDict):
    current_schema: str
    schema_issues: list[str]
    migration_complexity: str

class MigrationDesign(TypedDict):
    new_schema: str
    breaking_changes: list[str]
    migration_strategy: str

class MigrationScript(TypedDict):
    sql_up: str
    sql_down: str
    migration_steps: list[str]

# Main state for the workflow
class DatabaseMigrationState(TypedDict):
    """Internal state for database migration workflow."""
    input_story: str
    story_requirements: dict

    # Phase outputs
    schema_analysis: NotRequired[SchemaAnalysis]
    migration_design: NotRequired[MigrationDesign]
    migration_script: NotRequired[MigrationScript]

    # Tracking
    analysis_completed: bool
    design_completed: bool
    migration_completed: bool
    testing_completed: bool
    documentation_completed: bool

    status: str  # in_progress, success, failure, partial
    execution_notes: str
    parent_context: dict


def create_initial_database_migration_state(
    input_story: str,
    story_requirements: Optional[dict] = None,
    parent_context: Optional[dict] = None,
) -> DatabaseMigrationState:
    """Create initial state for workflow."""
    return DatabaseMigrationState(
        input_story=input_story,
        story_requirements=story_requirements or {},
        analysis_completed=False,
        design_completed=False,
        migration_completed=False,
        testing_completed=False,
        documentation_completed=False,
        status="in_progress",
        execution_notes="",
        parent_context=parent_context or {},
    )
```

### Step 4: Create Prompts

Create `workflows/children/database_migration/prompts.py`:

```python
"""LLM prompts for database migration workflow."""

ANALYZE_SCHEMA_PROMPT = """
Analyze the current database schema and identify migration requirements:

Current Schema:
{current_schema}

Requirements:
{requirements}

Provide JSON output with:
- current_schema: Description of current schema
- schema_issues: List of issues or limitations
- migration_complexity: Low/Medium/High assessment
- migration_approach: Recommended approach
"""

DESIGN_MIGRATION_PROMPT = """
Design a database migration plan based on the analysis:

Analysis:
{schema_analysis}

Current Schema:
{current_schema}

Requirements:
{requirements}

Provide JSON output with:
- new_schema: New schema design
- breaking_changes: List of breaking changes
- migration_strategy: Step-by-step strategy
- rollback_plan: How to rollback if needed
- estimated_duration: Time estimate
"""

# Add more prompts for each phase
GENERATE_MIGRATION_SQL_PROMPT = """..."""
GENERATE_MIGRATION_TESTS_PROMPT = """..."""
GENERATE_MIGRATION_DOCS_PROMPT = """..."""
```

### Step 5: Create Planner Agent

Create `workflows/children/database_migration/agents/planner.py`:

```python
import json
import logging
from typing import Dict, Any

from core.llm import get_default_llm_client
from workflows.children.database_migration.prompts import ANALYZE_SCHEMA_PROMPT

logger = logging.getLogger(__name__)


class DatabaseMigrationPlannerAgent:
    """Agent for planning database migrations."""

    def __init__(self):
        """Initialize the planner agent."""
        self.llm_client = get_default_llm_client()

    async def analyze_current_schema(
        self,
        story_requirements: Dict[str, Any],
        current_schema: str = "",
    ) -> Dict[str, Any]:
        """
        Analyze current database schema.

        Args:
            story_requirements: Structured requirements
            current_schema: Current schema definition

        Returns:
            Dictionary with analysis, errors, and success status
        """
        try:
            prompt = ANALYZE_SCHEMA_PROMPT.format(
                current_schema=current_schema or "Not provided",
                requirements=json.dumps(story_requirements, indent=2),
            )

            response = await self.llm_client.ainvoke(prompt)
            response_text = response.content

            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                analysis = self._extract_json(response_text)

            return {
                "success": True,
                "analysis": analysis,
                "errors": [],
            }

        except Exception as e:
            logger.error(f"Error analyzing schema: {str(e)}")
            return {
                "success": False,
                "analysis": self._generate_fallback_analysis(story_requirements),
                "errors": [str(e)],
            }

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

    def _generate_fallback_analysis(self, requirements: Dict[str, Any]):
        """Generate fallback analysis when LLM fails."""
        return {
            "current_schema": requirements.get("current_schema", "Not specified"),
            "schema_issues": ["Schema analysis unavailable"],
            "migration_complexity": "Unknown",
            "migration_approach": "Manual review recommended",
        }
```

Update `workflows/children/database_migration/agents/__init__.py`:

```python
"""Database migration workflow agents."""

from workflows.children.database_migration.agents.planner import (
    DatabaseMigrationPlannerAgent,
)

__all__ = ["DatabaseMigrationPlannerAgent"]
```

### Step 6: Implement Main Workflow

Create `workflows/children/database_migration/workflow.py`:

```python
"""
Database Migration child workflow implementation.

Phases:
1. Analysis: Analyze current schema
2. Design: Design new schema
3. Migration: Generate migration scripts
4. Testing: Create test suite
5. Documentation: Generate migration guide
"""

import json
import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from workflows.children.base import BaseChildWorkflow
from workflows.parent.state import EnhancedWorkflowState
from workflows.registry.registry import WorkflowMetadata, DeploymentMode
from workflows.children.database_migration.state import (
    DatabaseMigrationState,
    create_initial_database_migration_state,
)
from workflows.children.database_migration.agents.planner import (
    DatabaseMigrationPlannerAgent,
)
from core.llm import get_default_llm_client
from workflows.children.database_migration.prompts import (
    DESIGN_MIGRATION_PROMPT,
    GENERATE_MIGRATION_SQL_PROMPT,
    GENERATE_MIGRATION_TESTS_PROMPT,
    GENERATE_MIGRATION_DOCS_PROMPT,
)

logger = logging.getLogger(__name__)


class DatabaseMigrationWorkflow(BaseChildWorkflow):
    """
    Child workflow for database migrations.

    5-phase workflow:
    1. Analysis - Analyze current schema
    2. Design - Design new schema
    3. Migration - Generate migration scripts
    4. Testing - Create test suite
    5. Documentation - Generate migration guide
    """

    def __init__(self):
        """Initialize the workflow."""
        super().__init__()
        self.planner_agent = DatabaseMigrationPlannerAgent()
        self.llm_client = get_default_llm_client()

    def get_metadata(self) -> WorkflowMetadata:
        """Return metadata about this workflow."""
        return WorkflowMetadata(
            name="database_migration",
            workflow_type="database_migration",
            description="Plans and generates database migration scripts with testing",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.children.database_migration.workflow",
            tags=["database", "migration", "sql"],
        )

    async def create_graph(self) -> Any:
        """Create and compile the LangGraph."""
        logger.info("Creating database migration workflow graph")

        graph = StateGraph(DatabaseMigrationState)

        # Add nodes
        graph.add_node("analysis", self._analysis_node)
        graph.add_node("design", self._design_node)
        graph.add_node("migration", self._migration_node)
        graph.add_node("testing", self._testing_node)
        graph.add_node("documentation", self._documentation_node)

        # Set entry point
        graph.set_entry_point("analysis")

        # Create pipeline
        graph.add_edge("analysis", "design")
        graph.add_edge("design", "migration")
        graph.add_edge("migration", "testing")
        graph.add_edge("testing", "documentation")
        graph.add_edge("documentation", END)

        return graph.compile()

    async def validate_input(self, state: EnhancedWorkflowState) -> bool:
        """Validate input state."""
        if not state.get("story"):
            logger.warning("Database Migration: Missing story")
            return False
        return True

    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]:
        """Execute the workflow."""
        logger.info("Executing Database Migration workflow")

        try:
            if not await self.validate_input(state):
                return {
                    "status": "failure",
                    "error": "Invalid input",
                    "output": {},
                }

            # Create internal state
            internal_state = create_initial_database_migration_state(
                input_story=state.get("story", ""),
                story_requirements=state.get("story_requirements", {}),
                parent_context={"parent_state": state},
            )

            # Execute graph
            graph = await self.get_compiled_graph()
            final_state = await graph.ainvoke(internal_state)

            return {
                "status": final_state.get("status", "success"),
                "output": {
                    "schema_analysis": final_state.get("schema_analysis"),
                    "migration_design": final_state.get("migration_design"),
                    "migration_script": final_state.get("migration_script"),
                },
                "execution_notes": final_state.get("execution_notes", ""),
            }

        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            return {
                "status": "failure",
                "error": str(e),
                "output": {},
            }

    async def _analysis_node(self, state: DatabaseMigrationState) -> DatabaseMigrationState:
        """Analysis phase."""
        logger.info("Database Migration: Analysis phase")
        state = state.copy()

        try:
            result = await self.planner_agent.analyze_current_schema(
                story_requirements=state.get("story_requirements", {}),
            )

            if result["success"]:
                state["schema_analysis"] = result["analysis"]
                state["analysis_completed"] = True
                state["execution_notes"] += "Analysis completed. "
            else:
                state["analysis_completed"] = True
                state["schema_analysis"] = result["analysis"]

        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            state["analysis_completed"] = True
            state["status"] = "failure"

        return state

    # Implement other node methods following the same pattern
    async def _design_node(self, state: DatabaseMigrationState) -> DatabaseMigrationState:
        """Design phase."""
        logger.info("Database Migration: Design phase")
        state = state.copy()

        if not state.get("analysis_completed"):
            logger.warning("Skipping design: analysis not completed")
            return state

        # Implementation similar to other workflows
        state["design_completed"] = True
        return state

    # ... implement remaining nodes (migration, testing, documentation)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text."""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                return {}
            json_str = text[start:end]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return {}
```

Update `workflows/children/database_migration/__init__.py`:

```python
"""Database migration workflow package."""

from workflows.children.database_migration.workflow import DatabaseMigrationWorkflow

__all__ = ["DatabaseMigrationWorkflow"]
```

### Step 7: Register Workflow

Update `config/workflows.yaml`:

```yaml
workflows:
  # ... existing workflows ...

  - name: database_migration
    workflow_type: database_migration
    description: "Plans and generates database migration scripts with testing"
    version: "1.0.0"
    deployment_mode: embedded
    module_path: workflows.children.database_migration.workflow
    dependencies:
      - langgraph
      - langchain
      - langchain-anthropic
    tags:
      - database
      - migration
      - sql
    is_active: true
    author: "Framework Team"
    input_schema:
      type: object
      properties:
        current_schema: { type: string }
        new_schema_requirements: { type: string }
    output_schema:
      type: object
      properties:
        schema_analysis: { type: object }
        migration_design: { type: object }
        migration_script: { type: object }
```

### Step 8: Write Tests

Create `tests/unit/test_database_migration.py`:

```python
"""Unit tests for database migration workflow."""

import pytest
from workflows.children.database_migration.workflow import DatabaseMigrationWorkflow
from workflows.children.database_migration.state import (
    DatabaseMigrationState,
    create_initial_database_migration_state,
)
from workflows.registry.registry import WorkflowMetadata, DeploymentMode


class TestDatabaseMigrationWorkflow:
    """Test suite for DatabaseMigrationWorkflow."""

    @pytest.fixture
    def workflow(self):
        """Create workflow instance."""
        return DatabaseMigrationWorkflow()

    def test_workflow_instantiation(self, workflow):
        """Test workflow creation."""
        assert workflow is not None
        assert isinstance(workflow, DatabaseMigrationWorkflow)

    def test_get_metadata(self, workflow):
        """Test metadata."""
        metadata = workflow.get_metadata()
        assert metadata.name == "database_migration"
        assert metadata.workflow_type == "database_migration"

    @pytest.mark.asyncio
    async def test_create_graph(self, workflow):
        """Test graph creation."""
        graph = await workflow.create_graph()
        assert graph is not None

    @pytest.mark.asyncio
    async def test_execute_with_valid_state(self, workflow):
        """Test execution."""
        from workflows.parent.state import EnhancedWorkflowState

        state: EnhancedWorkflowState = {
            "story": "# Database Migration\nMigrate to new schema",
            "story_requirements": {},
            "story_type": "database_migration",
            "preprocessor_output": {},
            "planner_output": {},
            "workflow_tasks": [],
            "task_results": [],
            "execution_log": [],
        }

        result = await workflow.execute(state)
        assert result is not None
        assert "status" in result


# Add more test classes as needed
```

### Step 9: Test Your Workflow

```bash
# Run tests for your workflow
pytest tests/unit/test_database_migration.py -v

# Run full test suite
pytest tests/ -v

# Check coverage
pytest tests/ --cov=workflows.children.database_migration
```

### Step 10: Verify Integration

Test end-to-end with a story file:

```bash
# Create example story
cat > example_story.md <<EOF
# Database Migration
Migrate from MySQL to PostgreSQL with schema improvements

## Current Schema
Table: users (id, name, email)

## New Schema Requirements
- Add created_at, updated_at timestamps
- Add indexes for performance
- Add foreign keys for referential integrity
EOF

# Run workflow
python main.py --story-file example_story.md
```

## Checklist

Before considering your workflow complete:

- [ ] State schema defined (TypedDict)
- [ ] Planner agent implemented
- [ ] Prompts created for each phase
- [ ] Main workflow class extends BaseChildWorkflow
- [ ] All nodes implemented
- [ ] Error handling with fallbacks
- [ ] Registered in config/workflows.yaml
- [ ] Unit tests written and passing
- [ ] Integration tests verify end-to-end
- [ ] Full test suite passes
- [ ] Metadata properly configured
- [ ] Documentation updated

## Common Patterns

### JSON Parsing with Fallback

```python
try:
    result = json.loads(response_text)
except json.JSONDecodeError:
    result = self._extract_json(response_text)
    if not result:
        result = self._generate_fallback_structure()
```

### State Copying Pattern

```python
async def _node(self, state: StateType) -> StateType:
    state = state.copy()  # Always copy state
    # ... modify state ...
    return state
```

### Conditional Node Execution

```python
if not state.get("previous_phase_completed"):
    logger.warning("Skipping phase: prerequisite not complete")
    return state

# Continue with phase logic
```

## Best Practices

1. **Always copy state** in node functions
2. **Use async/await** for all I/O operations
3. **Include comprehensive docstrings**
4. **Implement fallback generation** for LLM failures
5. **Log at each phase** for debugging
6. **Handle errors gracefully** without stopping execution
7. **Validate inputs** early
8. **Test edge cases** and error conditions

## Next Steps

- Review existing workflows (API Development, UI Development) for more examples
- Check architecture documentation for deeper understanding
- Run example workflows to see patterns in action
- Join development community for questions and feedback

---

For questions about specific implementation details, see the [Architecture Documentation](architecture.md).
