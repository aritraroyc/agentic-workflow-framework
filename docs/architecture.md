# Architecture Documentation

## Overview

The Agentic Workflow Framework is built on a hierarchical parent-child architecture using LangGraph for state management and orchestration. This document provides a detailed technical overview of the system architecture.

## System Architecture

### High-Level View

```
┌──────────────────────────────────────────────────────────────┐
│                   Parent Workflow                             │
│  (Orchestrates and routes to child workflows)                │
│                                                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Preprocessor    │→ │ Planner      │→ │ Coordinator    │  │
│  │ Agent           │  │ Agent        │  │ Agent          │  │
│  └─────────────────┘  └──────────────┘  └────────┬───────┘  │
│                                                    │          │
│                                      ┌─────────────┴────┐    │
│                                      │ Aggregator Agent │    │
│                                      └──────────────────┘    │
└──────────────────────────────────────────────────────────────┘
         ↓                                  ↓
    ┌─────────────┐  ┌────────────┐  ┌──────────────┐
    │ Child WF 1  │  │ Child WF 2 │  │ Child WF N   │
    │ (Embedded)  │  │ (Embedded) │  │ (A2A Service)│
    └─────────────┘  └────────────┘  └──────────────┘
         ↓                ↓                  ↓
    ┌─────────────────────────────────────────────┐
    │           Outputs Directory                 │
    │  (Results, artifacts, logs, state)         │
    └─────────────────────────────────────────────┘
```

## Core Components

### 1. Parent Workflow

The parent workflow orchestrates the entire process with four main agents:

#### Preprocessor Agent
- **Purpose**: Validates and structures input
- **Input**: Raw story/requirements
- **Output**: Structured metadata, requirements validation
- **Key Methods**:
  - `_parse_markdown_sections()` - Parses markdown structure
  - `_validate_structure()` - Validates against schema
  - `_extract_structured_data()` - Extracts JSON-structured data
  - `_extract_metadata()` - Generates metadata

#### Planner Agent
- **Purpose**: Analyzes scope and creates execution plan
- **Input**: Structured requirements from preprocessor
- **Output**: Workflow selection, task plan, execution strategy
- **Key Methods**:
  - `_analyze_story_scope()` - LLM-based analysis
  - `_identify_required_workflows()` - Selects child workflows
  - `_create_workflow_tasks()` - Breaks down into tasks
  - `_determine_execution_strategy()` - Sequential vs parallel

#### Coordinator Agent
- **Purpose**: Executes child workflows with dependency management
- **Input**: Execution plan from planner
- **Output**: Collected results from all child workflows
- **Key Methods**:
  - `_execute_sequential()` - Linear execution
  - `_execute_parallel()` - Concurrent execution
  - `_dependencies_satisfied()` - Dependency checking
  - `_group_by_dependency_level()` - Task grouping

#### Aggregator Agent
- **Purpose**: Collects and formats final results
- **Input**: Results from coordinator
- **Output**: Final report and artifacts
- **Key Methods**:
  - `_aggregate_results()` - Combines outputs
  - `_generate_summary()` - Creates summary
  - `_format_output()` - Formats for storage

### 2. Child Workflows

Each child workflow is a specialized LangGraph that handles a specific development task.

#### Base Child Workflow (`BaseChildWorkflow`)

All child workflows extend this abstract class:

```python
class BaseChildWorkflow:
    async def get_metadata(self) -> WorkflowMetadata: ...
    async def create_graph(self) -> Any: ...
    async def validate_input(self, state: EnhancedWorkflowState) -> bool: ...
    async def execute(self, state: EnhancedWorkflowState) -> Dict[str, Any]: ...
    async def get_compiled_graph(self) -> Any: ...
```

#### Available Child Workflows

**API Development Workflow**
- Phases: Planning → Design → Code → Testing → Documentation
- Input: API requirements
- Output: Complete API with code, tests, docs

**UI Development Workflow**
- Phases: Planning → Design → Code → Styling → Testing → Documentation
- Input: UI requirements
- Output: Complete UI component with styling and tests

**API Enhancement Workflow**
- Phases: Analysis → Design → Code → Testing → Monitoring
- Input: Existing API + Enhancement requirements
- Output: Enhancement code, tests, monitoring setup

**UI Enhancement Workflow**
- Phases: Analysis → Design → Code → Testing → A11y → Documentation
- Input: Existing UI + Enhancement requirements
- Output: Enhancement code, tests, accessibility improvements

### 3. State Management

The framework uses TypedDict for LangGraph compatibility:

```python
# Parent workflow state
EnhancedWorkflowState = TypedDict({
    "story": str,
    "story_requirements": dict,
    "story_type": str,
    "preprocessor_output": dict,
    "planner_output": dict,
    "workflow_tasks": list[WorkflowTask],
    "task_results": list[WorkflowExecutionResult],
    "execution_log": list[dict],
})

# Child workflow state (example: API Development)
ApiDevelopmentState = TypedDict({
    "input_story": str,
    "story_requirements": dict,
    "api_plan": dict,
    "api_design": dict,
    "api_code": dict,
    "api_tests": dict,
    "api_docs": dict,
    "status": str,
    "execution_notes": str,
    "parent_context": dict,
})
```

### 4. Registry System

The workflow registry enables dynamic discovery and invocation:

```python
# Loaded from config/workflows.yaml
class WorkflowRegistry:
    def register(workflow_metadata: WorkflowMetadata) -> None
    def get(name: str) -> WorkflowMetadata
    def list() -> List[WorkflowMetadata]
    def list_by_type(workflow_type: str) -> List[WorkflowMetadata]
```

### 5. Workflow Invoker

Unified interface for invoking embedded and A2A workflows:

```python
class WorkflowInvoker:
    async def invoke(
        name: str,
        state: EnhancedWorkflowState,
        registry: WorkflowRegistry
    ) -> Dict[str, Any]

    # Internal methods handle:
    # - Dynamic module loading (embedded)
    # - HTTP requests (A2A)
    # - Caching and performance
    # - Retry logic and timeouts
```

## Data Flow

### Execution Flow Diagram

```
Input Story
    ↓
[Preprocessor Agent]
    ├─ Parse markdown
    ├─ Validate structure
    ├─ Extract data
    └─ Generate metadata
    ↓
EnhancedWorkflowState
    ↓
[Planner Agent]
    ├─ Analyze scope
    ├─ Select workflows
    ├─ Create task plan
    └─ Plan execution strategy
    ↓
WorkflowTask[] + ExecutionStrategy
    ↓
[Coordinator Agent]
    ├─ Get child workflow from registry
    ├─ Invoke workflow (embedded or A2A)
    ├─ Manage dependencies
    └─ Collect results
    ↓
WorkflowExecutionResult[]
    ↓
[Aggregator Agent]
    ├─ Aggregate results
    ├─ Generate summary
    └─ Format output
    ↓
Final Report + Artifacts
    ↓
outputs/
```

### State Transformation Sequence

1. **Initial State**: Raw story as string
2. **After Preprocessor**: Structured metadata and requirements
3. **After Planner**: Task plan and workflow selection
4. **After Coordinator**: Intermediate results from child workflows
5. **After Aggregator**: Final formatted output

## LangGraph Integration

### Graph Structure

Each workflow builds a StateGraph:

```python
graph = StateGraph(StateType)

# Add nodes
graph.add_node("node_name", async_function)

# Add edges (sequential)
graph.add_edge("node1", "node2")

# Add conditional edges (branching)
graph.add_conditional_edges(
    "node",
    condition_func,
    {"path1": "node1", "path2": "node2"}
)

# Compile
compiled = graph.compile()

# Execute
result = await compiled.ainvoke(initial_state)
```

### Child Workflow Graph Example (API Development)

```
┌──────────────┐
│  START       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Planning    │ (Analyze requirements, create API plan)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Design      │ (Generate OpenAPI spec)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Code Gen    │ (Generate FastAPI/Flask/Django code)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Testing     │ (Generate pytest tests)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Documentation │ (Generate API docs)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  END         │
└──────────────┘
```

## LLM Integration

### Model Configuration

The framework uses Anthropic Claude (default) or OpenAI:

```python
# Default client
llm_client = get_default_llm_client()

# Uses:
# - ANTHROPIC_API_KEY for Claude
# - OPENAI_API_KEY for OpenAI (fallback)
```

### Prompt Structure

Each agent uses specialized prompts:

```python
# Example: API Planning Prompt
PLAN_API_PROMPT = """
Analyze these API requirements and create a comprehensive plan:
{requirements}

Provide JSON output with:
- api_overview
- endpoints
- data_models
- authentication
- error_handling
- scalability_considerations
"""
```

### JSON Parsing with Fallback

All LLM responses are parsed with fallback logic:

```python
try:
    result = json.loads(response_text)
except json.JSONDecodeError:
    # Extract JSON from text
    result = extract_json(response_text)

if not result:
    # Fallback to generated structure
    result = generate_fallback_structure()
```

## Error Handling

### Error Recovery Strategy

1. **Validation Phase**: Input validation with detailed error messages
2. **Execution Phase**: Try-catch with fallback generation
3. **Aggregation Phase**: Partial success handling

### Error Types Handled

- Missing required fields
- Invalid JSON responses
- Network timeouts (A2A)
- LLM API failures
- Workflow execution errors

## Deployment Modes

### Embedded Mode

Child workflows run in the same process as the parent:

```
Parent Process
├─ Parent Workflow
└─ Child Workflows (imported modules)
```

**Advantages**:
- No network overhead
- Direct state passing
- Easier debugging

### A2A (Agent-to-Agent) Mode

Child workflows run as separate services:

```
Parent Service        Child Service (API Enhancement)
├─ Parent Workflow    ├─ FastAPI app
├─ HTTP Client   ─────┤ /execute endpoint
└─ Response Handler   ├─ /metadata endpoint
                      └─ /health endpoint
```

**Advantages**:
- Scalability
- Service isolation
- Independent deployment
- Language-agnostic

### Hybrid Deployment

Mix of embedded and A2A workflows:

```yaml
workflows:
  - name: api_development
    deployment_mode: embedded      # Local execution

  - name: api_enhancement_service
    deployment_mode: a2a           # Remote service
    service_url: http://localhost
    service_port: 8001
```

## Performance Considerations

### Caching Strategy

1. **Graph Compilation**: Pre-compiled StateGraphs cached after first use
2. **Workflow Instances**: Singleton instances per workflow
3. **Registry**: Loaded once at startup

### Async/Await Usage

- All I/O operations are async
- LLM calls use `ainvoke()`
- Parallel task execution with `asyncio.gather()`

### Timeout Configuration

```python
# A2A service timeout
INVOKER_TIMEOUT = 60  # seconds

# Coordinator timeout
COORDINATOR_TIMEOUT = 300  # seconds

# Individual workflow timeout
WORKFLOW_TIMEOUT = 180  # seconds
```

## Security Considerations

### Input Validation

- All inputs validated against schemas
- Markdown structure validated
- JSON parsing with error handling

### API Security (A2A)

- Service endpoints use HTTP/HTTPS
- Consider authentication for production
- Input validation on service endpoints

### Environment Variables

Sensitive data (API keys) stored in `.env`:

```env
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
```

## Testing Strategy

### Test Levels

1. **Unit Tests**: Individual agent/workflow testing
2. **Integration Tests**: Parent-child workflow interaction
3. **E2E Tests**: Full workflow execution with sample stories

### Test Coverage

- State management
- Graph creation and execution
- Agent functionality
- Error handling
- Output formatting

## Future Architecture Improvements

1. **Event Streaming**: Real-time execution monitoring
2. **Checkpointing**: Resumable workflow execution
3. **Distributed State**: Shared state across services
4. **Analytics**: Execution metrics and insights
5. **Custom Workflow DSL**: User-defined workflow templates

---

For implementation details, see [Adding Workflows Guide](adding_workflows.md).
