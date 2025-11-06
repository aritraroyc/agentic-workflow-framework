# Agentic Workflow Framework - Development Guide

## Project Overview
This is a LangGraph-based agentic workflow orchestration framework for software development tasks (API development, UI MFE development, etc.). The framework follows a parent-child architecture where a common parent workflow routes requests to specialized child workflows.

## Architecture
- **Parent Workflow**: Common orchestration with Preprocessor → Planner → Coordinator → Aggregator
- **Child Workflows**: Specialized workflows (API dev, API enhancement, UI dev, UI enhancement)
- **Registry System**: Dynamic workflow registration supporting embedded and A2A service modes

## Development Commands
```bash
# Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py

# Test
pytest tests/
```

## Code Style
- Use Python 3.11+
- Follow PEP 8
- Use type hints extensively
- Async/await for all I/O operations
- Comprehensive docstrings for all classes and functions

## Key Technologies
- LangGraph for workflow orchestration
- LangChain for LLM interactions
- OpenAI, Anthropic Claude for LLM (Use ChatOpenAI interface in code)
- Pydantic for data validation
- FastAPI for A2A services

## Project Structure
```
agentic-workflow-framework/
├── workflows/
│   ├── parent/          # Parent workflow with agents
│   └── children/        # Child workflows
├── core/                # Core utilities
├── config/             # Configuration files
└── tests/              # Test files
```

## Important Notes
- All state management uses TypedDict for LangGraph compatibility
- Agents are separate classes for better maintainability
- Child workflows must inherit from BaseChildWorkflow
- All LLM calls should be async and include error handling
```

---

## **PHASE 1: Foundation (Iterative Approach)**

For complex implementations, asking Claude to research and plan first significantly improves performance for problems requiring deeper thinking upfront .

### **Task 1.1: Project Structure & Dependencies**

**Prompt to Claude Code:**
```
Think hard about the best project structure for our agentic workflow framework. 

Please:
1. Create the complete directory structure as outlined in CLAUDE.md
2. Initialize a Python project with uv
3. Create requirements.txt with these dependencies:
   - langgraph
   - langchain
   - langchain-anthropic
   - openai
   - anthropic
   - pydantic
   - pyyaml
   - aiohttp
   - fastapi
   - uvicorn
   - pytest
   - pytest-asyncio
4. Create __init__.py files in all necessary directories
5. Create a .gitignore file for Python projects
6. Commit these changes with message "Initial project structure"

Do NOT implement any business logic yet - just the scaffolding.
```

### **Task 1.2: Core State Schemas**

**Prompt to Claude Code:**
```
Think about the state management design.

Implement the state schemas in workflows/parent/state.py:
1. EnhancedWorkflowState (main state)
2. PreprocessorOutput
3. PlannerOutput
4. WorkflowTask
5. WorkflowExecutionResult

Use TypedDict for LangGraph compatibility. Include comprehensive type hints and docstrings.

After implementation:
- Run type checking (mypy if configured)
- Commit with message "Add parent workflow state schemas"
```

### **Task 1.3: Workflow Registry**

**Prompt to Claude Code:**
```
Ultrathink the registry pattern design.

Implement the workflow registry system:
1. Create workflows/registry/registry.py with:
   - WorkflowMetadata dataclass
   - DeploymentMode enum
   - WorkflowRegistry class with register/get/list methods

2. Create workflows/registry/loader.py with:
   - load_registry() function that reads config/workflows.yaml
   - Auto-discovery of embedded workflows

3. Create config/workflows.yaml with empty structure

4. Write unit tests in tests/unit/test_registry.py

5. Run tests: pytest tests/unit/test_registry.py

6. Commit with message "Implement workflow registry system"
```

---

## **PHASE 2: Parent Workflow Agents**

Using the word "think" triggers extended thinking mode, with "think hard", "think harder", and "ultrathink" allocating progressively more thinking budget .

### **Task 2.1: Preprocessor Agent**

**Prompt to Claude Code:**
```
Ultrathink the preprocessor agent implementation.

Create workflows/parent/agents/preprocessor.py implementing the PreprocessorAgent class with:

1. Markdown parsing (_parse_markdown_sections)
2. Structure validation (_validate_structure)
3. LLM-based data extraction (_extract_structured_data)
4. Metadata generation (_extract_metadata)

Requirements:
- Use async/await throughout
- Comprehensive error handling
- Return PreprocessorOutput TypedDict
- Include detailed docstrings

Also create:
- config/validation_rules.yaml with validation config
- tests/unit/test_preprocessor.py with test cases
- examples/stories/api_development.md as sample input

Test with: pytest tests/unit/test_preprocessor.py -v

Commit with: "Implement preprocessor agent"
```

### **Task 2.2: Planner Agent**

**Prompt to Claude Code:**
```
Think harder about the planning logic.

Create workflows/parent/agents/planner.py implementing the PlannerAgent class.

Key methods:
1. _analyze_story_scope() - LLM-based analysis
2. _identify_required_workflows() - Workflow selection
3. _create_workflow_tasks() - Task generation with responsibilities
4. _define_workflow_responsibilities() - LLM-based responsibility assignment
5. _determine_dependencies() - Dependency resolution
6. _determine_execution_strategy() - Sequential vs parallel
7. _identify_risk_factors() - Risk assessment

Include:
- Comprehensive prompts for each LLM call
- JSON parsing with error handling
- Unit tests in tests/unit/test_planner.py

Test and commit: "Implement planner agent"
```

### **Task 2.3: Coordinator Agent**

**Prompt to Claude Code:**
```
Think hard about orchestration patterns.

Create workflows/parent/agents/coordinator.py implementing WorkflowCoordinator.

Features:
1. Sequential execution (_execute_sequential)
2. Parallel execution (_execute_parallel) 
3. Dependency tracking (_dependencies_satisfied)
4. Level-based grouping (_group_by_dependency_level)
5. Single workflow execution (_execute_single_workflow)
6. Status aggregation (_determine_overall_status)

Requirements:
- Use asyncio.gather() for parallel execution
- Handle exceptions gracefully
- Track execution times
- Comprehensive logging

Include tests and commit: "Implement coordinator agent"
```

---

## **PHASE 3: Parent Workflow Graph**

### **Task 3.1: Parent Nodes**

**Prompt to Claude Code:**
```
Create workflows/parent/nodes.py with these node functions:

1. preprocessor_node - Uses PreprocessorAgent
2. planner_node - Uses PlannerAgent  
3. coordinator_node - Uses WorkflowCoordinator
4. aggregator_node - Aggregates all results

Each node should:
- Take EnhancedWorkflowState as input
- Return updated EnhancedWorkflowState
- Add entries to execution_log
- Handle errors properly

Also create core/llm.py with LLM client wrapper.

Commit: "Implement parent workflow nodes"
```

### **Task 3.2: Parent Graph Assembly**

**Prompt to Claude Code:**
```
Think about the graph flow design.

Create workflows/parent/graph.py:

1. Implement create_enhanced_parent_workflow()
2. Add all nodes to StateGraph
3. Create conditional edges for error handling
4. Set up checkpointing
5. Return compiled graph

Include integration test in tests/integration/test_parent_workflow.py

Test and commit: "Implement parent workflow graph"
```

---

## **PHASE 4: Base Child Workflow**

### **Task 4.1: Child Workflow Interface**

**Prompt to Claude Code:**
```
Design the child workflow base class.

Create workflows/children/base.py:

1. BaseChildWorkflow abstract class with:
   - get_metadata() -> WorkflowMetadata
   - create_graph() -> StateGraph
   - execute() -> Dict[str, Any]
   - validate_input() -> bool

2. Document the interface clearly for future implementations

Commit: "Add base child workflow interface"
```

---

## **PHASE 5: First Complete Child Workflow**

### **Task 5.1: API Development Workflow**

**Prompt to Claude Code:**
```
Ultrathink the API development workflow implementation.

Create workflows/children/api_development/ with:

1. workflow.py:
   - ApiDevelopmentState TypedDict
   - ApiDevelopmentWorkflow class
   - Internal planner node
   - Design, code generation, testing, docs nodes

2. agents/planner.py - Detailed implementation planner

3. prompts.py - All LLM prompts as templates

Structure it for:
- Full TDD workflow
- OpenAPI spec generation
- Unit test generation
- README generation

Test standalone execution.

Commit: "Implement API development child workflow"
```

### **Task 5.2: Workflow Invoker**

**Prompt to Claude Code:**
```
Think about the invocation abstraction.

Create workflows/registry/invoker.py:

1. WorkflowInvoker class
2. Support embedded (_invoke_embedded) and A2A (_invoke_a2a)
3. Lazy loading for embedded workflows
4. HTTP client for A2A services
5. Error handling and retries

Test both modes.

Commit: "Implement workflow invoker"
```

---

## **PHASE 6: End-to-End Integration**

### **Task 6.1: Main Entry Point**

**Prompt to Claude Code:**
```
Create main.py for end-to-end execution:

1. Load registry from config
2. Initialize parent workflow
3. Read input markdown
4. Execute complete flow
5. Display results with rich formatting
6. Save artifacts to outputs/

Make it user-friendly with progress indicators.

Commit: "Add main entry point"
```

### **Task 6.2: Example Stories**

**Prompt to Claude Code:**
```
Create comprehensive example stories in examples/stories/:

1. api_development.md - Complete API story
2. api_enhancement.md - Enhancement story
3. ui_mfe_development.md - UI story
4. complex_multi_workflow.md - Multi-workflow story

Make them realistic and detailed.

Commit: "Add example story files"
```

### **Task 6.3: Integration Testing**

**Prompt to Claude Code:**
```
Think hard about end-to-end testing.

Create tests/integration/test_e2e.py:

1. Test complete flow with each story type
2. Validate state transitions
3. Check artifact generation
4. Verify error handling

Run full test suite: pytest tests/ -v

Fix any issues found.

Commit: "Add end-to-end integration tests"
```

---

## **PHASE 7: Additional Child Workflows**

For each remaining workflow, use this pattern:

**Prompt to Claude Code:**
```
Using the API Development workflow as a reference, create:

workflows/children/[workflow_name]/
- workflow.py (with internal planner)
- agents/planner.py
- prompts.py

Implement for: [workflow_type]
Responsibilities: [specific responsibilities]

Follow the same structure and testing approach.

Commit: "Implement [workflow_name] child workflow"
```

---

## **PHASE 8: A2A Service Mode**

### **Task 8.1: FastAPI Service Template**

**Prompt to Claude Code:**
```
Think about the A2A service pattern.

Create workflows/children/api_enhancement/service.py:

1. FastAPI app with /execute endpoint
2. /metadata endpoint
3. /health endpoint
4. Request/response models
5. Error handling

Create Dockerfile for containerization.

Test locally: uvicorn service:app --reload

Commit: "Add A2A service for API enhancement workflow"
```

---

## **PHASE 9: Polish & Documentation**

### **Task 9.1: README & Documentation**

**Prompt to Claude Code:**
```
Create comprehensive documentation:

1. README.md - Overview, installation, usage examples
2. docs/architecture.md - Detailed architecture
3. docs/adding_workflows.md - Guide for new workflows
4. docs/configuration.md - Config reference
5. docs/api_reference.md - API docs

Make it professional and complete.

Commit: "Add comprehensive documentation"
```

### **Task 9.2: Docker Compose**

**Prompt to Claude Code:**
```
Create deployment/docker-compose.yaml:

1. Parent workflow service
2. Each A2A child workflow service
3. PostgreSQL for checkpointing
4. Proper networking

Test: docker-compose up

Commit: "Add Docker Compose configuration"
```

---

## **BEST PRACTICES FOR USING CLAUDE CODE**

### **1. Iterative Development Pattern**

The recommended workflow is: ask Claude to research and understand the problem, ask Claude to form a plan for solving it, ask Claude to implement its solution in code, and ask Claude to commit the result .

Use this for EVERY task:
```
1. "Think hard about [problem]"
2. "Create a plan for [implementation]"
3. "Implement [specific component]"
4. "Test the implementation"
5. "Commit with message '[description]'"
```

### **2. Trigger Extended Thinking**

Using specific phrases like "think", "think hard", "think harder", and "ultrathink" triggers progressively more thinking budget for Claude to evaluate alternatives more thoroughly .

- **Simple tasks**: "think"
- **Complex logic**: "think hard"
- **Architectural decisions**: "think harder"
- **Critical implementations**: "ultrathink"

### **3. Provide Context Incrementally**

Don't dump the entire plan at once. Instead:
```
Phase 1, Task 1: [details]
After this works, ask me for the next task.
```

### **4. Test Frequently**

After each component:
```
Run the tests for this component.
If tests fail, debug and fix.
Show me the test results.
```

### **5. Use Git Commits as Checkpoints**

Commit after every working piece:
```
If everything works correctly, commit with message: "[description]"
```

### **6. Leverage CLAUDE.md**

Update it as you go:
```
Update CLAUDE.md with the new [component] details.
Document any gotchas or special considerations.