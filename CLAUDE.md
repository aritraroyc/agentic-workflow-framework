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
- All LLM calls must use `asyncio.to_thread()` wrapper with message dict format (CRITICAL)
- State field is `input_story`, not `story` (CRITICAL)

## CRITICAL LLM Invocation Pattern

**All LLM calls must follow this exact pattern** (not `ainvoke()`):

```python
import asyncio

# Correct pattern - ALWAYS use asyncio.to_thread with message dict format
response = await asyncio.to_thread(
    self.llm_client.invoke,
    [
        {"role": "system", "content": "You are an expert..."},
        {"role": "user", "content": prompt_text},
    ]
)

# Extract response
response_text = response.content if hasattr(response, 'content') else str(response)
```

**Why?** LLM client is synchronous (no `ainvoke()` method), and it requires message dicts with role assignments.

**Anti-patterns to avoid:**
- ❌ `await self.llm_client.ainvoke(prompt)` - AttributeError
- ❌ `await asyncio.to_thread(self.llm_client.invoke, "plain string")` - Empty responses
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

## **PHASE 4: Base Child Workflow** ✅ COMPLETED

### **Task 4.1: Child Workflow Interface** ✅ COMPLETED

**Implementation Details:**
- **Created**: workflows/children/base.py (212 lines)
- **Abstract Methods**:
  1. get_metadata() -> WorkflowMetadata
  2. create_graph() -> Any (compiled StateGraph)
  3. validate_input() -> bool
  4. execute() -> Dict[str, Any]
  5. get_compiled_graph() (implemented with lazy loading and caching)

- **Key Features**:
  - Lazy-load-once caching pattern for compiled graphs
  - Async/await throughout
  - Comprehensive docstrings
  - Type hints with Python 3.11+ features

- **Test Results**:
  - 19 unit tests in test_base_workflow.py
  - 100% test coverage of abstract interface
  - MockChildWorkflow demonstrates correct implementation pattern

**Status**: Base class defines the contract for all child workflows. ApiDevelopmentWorkflow successfully extends it.

---

## **PHASE 5: First Complete Child Workflow** ✅ COMPLETED

### **Task 5.1: API Development Workflow** ✅ COMPLETED

**Implementation Details:**
- **Created**: workflows/children/api_development/ (full directory structure)
  1. workflow.py (580 lines) - ApiDevelopmentWorkflow class with 5-phase pipeline
  2. state.py (150 lines) - ApiDevelopmentState TypedDict and helper functions
  3. agents/planner.py (180 lines) - ApiPlannerAgent for API planning
  4. prompts.py (200 lines) - LLM prompt templates for all phases

- **5-Phase Pipeline**:
  1. Planning: Validate requirements and create detailed API plan
  2. Design: Generate OpenAPI 3.0 specification
  3. Code Generation: Generate FastAPI/Flask/Django code
  4. Testing: Generate comprehensive pytest test suite
  5. Documentation: Generate API documentation and README

- **Key Features**:
  - Pre-compiled StateGraph with lazy loading and caching
  - Input validation ensures required preprocessor output
  - Error handling with graceful fallbacks
  - LLM-based planning with JSON parsing
  - Fallback plan generation if LLM fails

- **Test Results**:
  - 18 unit tests in test_api_development.py
  - Coverage includes instantiation, validation, graph creation, execution, state schema, planner agent
  - All tests passing

**Task 5.2: Workflow Invoker** ✅ COMPLETED

**Implementation Details:**
- **Created**: workflows/registry/invoker.py (470 lines)
- **Unified Invocation Interface**:
  1. invoke() - Delegates to embedded or A2A mode
  2. _invoke_embedded() - Loads and executes local workflows
  3. _invoke_a2a() - Makes HTTP POST to remote services

- **Key Features**:
  1. Dynamic module loading via importlib
  2. Class name inference (snake_case → CamelCase)
  3. Workflow instance caching for performance
  4. Retry logic with exponential backoff (1s delay)
  5. Timeout handling (asyncio.wait_for for embedded, aiohttp.ClientTimeout for A2A)
  6. Result validation and normalization
  7. Comprehensive error handling with error results

- **A2A Support**:
  - HTTP POST to service endpoint with JSON payload
  - Service URL construction with optional port
  - Timeout and retry configuration per invocation

- **Test Results**:
  - 24 unit tests in test_invoker.py
  - Coverage includes both embedded and A2A modes, timeouts, retries, caching, validation
  - All tests passing (185 total unit tests after Phase 5)

**Status**: API Development workflow fully implemented and tested. Invoker ready for use by Coordinator.

---

## **PHASE 6: End-to-End Integration**

### **Task 6.1: Main Entry Point** ✅ COMPLETED

**Implementation Details:**
- **Created**: main.py with complete CLI interface
- **Features**:
  1. Loads workflow registry from config/workflows.yaml
  2. Initializes parent workflow with all agents
  3. Accepts story input from file or stdin
  4. Executes complete workflow pipeline
  5. Saves results to outputs/ (full state, logs, workflow results)
  6. Displays user-friendly summary with execution statistics
  7. Proper error handling and logging throughout

- **Coordinator Integration**:
  1. Modified WorkflowCoordinator to accept WorkflowRegistry and WorkflowInvoker
  2. Replaced simulation with actual workflow invocation via registry lookup
  3. Parent state properly passed to child workflows
  4. Falls back to simulation if registry unavailable

- **Configuration**:
  - Updated config/workflows.yaml to activate api_development workflow
  - Workflow registry now fully functional for dynamic workflow loading

- **Test Results**:
  - 10 new integration tests in test_coordinator_invoker.py
  - All 235 total tests passing
  - Coverage includes registry lookup, execution strategies, error handling

**Status**: Framework now supports end-to-end execution with actual workflow invocation

### **Task 6.2: Example Stories & E2E Testing** ✅ COMPLETED

**Implementation Details:**

**Example Stories Created** (4 realistic markdown files):
1. **api_development.md** - User Management API
   - Full REST API with JWT authentication
   - CRUD operations, role-based access control
   - Email verification, audit logging, rate limiting
   - Success criteria and acceptance criteria defined

2. **ui_development.md** - Customer Dashboard MFE
   - React 18+ with TypeScript
   - Material-UI components with theme switching
   - Real-time notifications, multi-language support
   - Core Web Vitals targets and WCAG compliance

3. **api_enhancement.md** - Transaction Processing API Enhancement
   - Batch processing, webhooks, advanced filtering
   - Performance optimization with caching
   - Monitoring with Prometheus, distributed tracing
   - Versioning and backward compatibility

4. **complex_ecommerce_platform.md** - Multi-Workflow Project
   - 8 interdependent development workflows
   - Product Catalog, Shopping Cart, Payments
   - Customer & Admin Dashboards, Analytics
   - Complete technical specifications and timeline

**Manual E2E Testing Guide** (test_e2e_workflows.md):
- 10 comprehensive test scenarios with step-by-step instructions
- Covers all story types and execution paths
- Performance testing procedures (response times, file sizes)
- Regression test checklist for release preparation
- Debugging commands and troubleshooting guide
- Test result tracking matrix

**Automated E2E Test Suite** (test_e2e_complete.py):
- **5 test classes** with 18 integration tests
- TestWorkflowInitialization - Workflow creation and registry loading
- TestWorkflowStateManagement - State creation and structure validation
- TestWorkflowExecution - Workflow invocation and input validation
- TestStoryProcessing - Story validation and content structure
- TestErrorHandling - Empty/invalid story handling
- TestRegistryIntegration - Registry metadata validation
- TestOutputFormatting - JSON serialization and execution logs

**Test Results**:
- **255 total tests passing** ✅ (from 235)
- 18 new E2E integration tests
- 2 skipped tests (optional workflows)
- Full coverage of initialization, state management, execution, error handling

**Status**: Framework now has complete example stories and comprehensive testing procedures. Ready for real-world usage with diverse scenario types.

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