# API Reference

## Overview

This document describes the API endpoints for the Agentic Workflow Framework, including:
- Parent workflow state and execution
- A2A service endpoints
- Data models and schemas

## Parent Workflow

### Execution Input State

The parent workflow accepts an `EnhancedWorkflowState`:

```python
{
    "input_story": str,                    # Main requirement description
    "story_requirements": dict,            # Structured requirements (optional)
    "story_type": str,                     # Workflow type (optional)
    "preprocessor_output": dict,           # Preprocessor output (internal)
    "planner_output": dict,                # Planner output (internal)
    "workflow_tasks": list[WorkflowTask],  # Task list (internal)
    "task_results": list[dict],            # Task results (internal)
    "execution_log": list[dict],           # Execution log (internal)
    "registry": Optional[Any],             # Workflow registry (internal)
}
```

### Execution Output

The parent workflow returns:

```python
{
    "status": str,                  # "success", "failure", "partial"
    "output": {
        "aggregated_results": dict, # Results from all workflows
        "artifacts": list[str],     # Generated artifact paths
    },
    "execution_log": list[dict],    # Detailed execution log
    "execution_summary": {
        "workflows_executed": int,
        "workflows_successful": int,
        "total_duration": float,
    }
}
```

### Python API

```python
import asyncio
from workflows.parent.graph import create_enhanced_parent_workflow
from workflows.registry.loader import load_registry
from workflows.registry.invoker import WorkflowInvoker

async def execute_workflow():
    # Load registry
    registry = load_registry()
    invoker = WorkflowInvoker()

    # Create parent workflow
    parent = create_enhanced_parent_workflow(registry, invoker)

    # Execute
    result = await parent.ainvoke({
        "input_story": "# API Development\nCreate a User Management API with JWT auth..."
    })

    return result

# Run
result = asyncio.run(execute_workflow())
print(result["status"])
```

## A2A Service Endpoints

### API Enhancement Service

Base URL: `http://localhost:8001` (default)

#### Execute Workflow

**Endpoint**: `POST /execute`

**Purpose**: Execute API enhancement workflow

**Request**:

```json
{
    "input_story": "Add batch processing and webhooks to existing API",
    "story_requirements": {
        "title": "Batch Processing Feature",
        "description": "Enable batch operations for performance",
        "current_api_structure": "FastAPI with PostgreSQL"
    },
    "story_type": "api_enhancement",
    "preprocessor_output": {},
    "planner_output": {}
}
```

**Response** (200 OK):

```json
{
    "status": "success",
    "output": {
        "enhancement_analysis": {
            "current_structure": "FastAPI REST API",
            "recommended_enhancements": [
                "Batch processing with job queues",
                "Webhook infrastructure"
            ]
        },
        "enhancement_design": {
            "batch_processing": {
                "architecture": "Queue-based with Celery",
                "endpoints": ["/api/batch/submit", "/api/batch/status"]
            },
            "webhooks": {
                "architecture": "Event-driven",
                "delivery_mechanism": "HTTP callbacks"
            }
        },
        "enhancement_code": {
            "batch_module": "# Generated code for batch processing",
            "webhook_module": "# Generated code for webhooks"
        },
        "enhancement_tests": {
            "batch_tests": "# Test specifications",
            "webhook_tests": "# Test specifications"
        },
        "monitoring_setup": {
            "metrics": "Prometheus metrics configuration",
            "tracing": "Distributed tracing setup"
        }
    },
    "timestamp": "2024-11-06T10:30:00.000000"
}
```

**Error Response** (503 Service Unavailable):

```json
{
    "detail": "Workflow service not ready"
}
```

**cURL Example**:

```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "story": "Add batch processing and webhooks",
    "story_requirements": {
      "title": "Performance Enhancement"
    }
  }'
```

#### Get Metadata

**Endpoint**: `GET /metadata`

**Purpose**: Get workflow metadata

**Response** (200 OK):

```json
{
    "name": "api_enhancement",
    "workflow_type": "api_enhancement",
    "description": "Enhances existing APIs with new features including batch processing, webhooks, advanced filtering, and monitoring",
    "version": "1.0.0",
    "deployment_mode": "a2a",
    "tags": ["api", "enhancement", "optimization", "monitoring"]
}
```

**cURL Example**:

```bash
curl -X GET http://localhost:8001/metadata
```

#### Health Check

**Endpoint**: `GET /health`

**Purpose**: Check service health and readiness

**Response** (200 OK):

```json
{
    "status": "healthy",
    "timestamp": "2024-11-06T10:30:00.000000",
    "version": "1.0.0",
    "workflow_loaded": true
}
```

**Response** (200 OK, Unhealthy):

```json
{
    "status": "unhealthy",
    "timestamp": "2024-11-06T10:30:00.000000",
    "version": "1.0.0",
    "workflow_loaded": false
}
```

**cURL Example**:

```bash
curl -X GET http://localhost:8001/health
```

## Data Models

### ExecuteRequest

```python
class ExecuteRequest:
    story: str                          # Required: main requirements
    story_requirements: dict = {}       # Structured requirements
    story_type: str = "api_enhancement" # Workflow type
    preprocessor_output: dict = {}      # Preprocessor output
    planner_output: dict = {}           # Planner output
```

### ExecuteResponse

```python
class ExecuteResponse:
    status: str                         # "success", "failure", "partial"
    output: dict                        # Workflow output
    error: str | None                   # Error message if failed
    execution_notes: str | None         # Execution notes
    timestamp: str                      # ISO timestamp
```

### MetadataResponse

```python
class MetadataResponse:
    name: str                           # Workflow name
    workflow_type: str                  # Workflow type
    description: str                    # Description
    version: str                        # Semantic version
    deployment_mode: str                # "a2a", "embedded"
    tags: list[str]                     # Categorization tags
```

### HealthResponse

```python
class HealthResponse:
    status: str                         # "healthy", "unhealthy"
    timestamp: str                      # ISO timestamp
    version: str                        # Service version
    workflow_loaded: bool               # Workflow initialized
```

## Workflow Types

### API Development

**Type**: `api_development`

**Input**:
- `api_requirements` (str): API requirements and specifications
- `preferred_framework` (str): FastAPI, Flask, Django

**Output**:
- `api_plan`: Detailed API planning
- `api_design`: OpenAPI 3.0 specification
- `code_output`: Generated code
- `test_output`: Test suite
- `docs_output`: API documentation

**Phases**: Planning → Design → Code → Testing → Documentation

### UI Development

**Type**: `ui_development`

**Input**:
- `ui_requirements` (str): UI requirements
- `target_framework` (str): React, Vue, Angular, etc.

**Output**:
- `ui_plan`: UI planning and analysis
- `ui_design`: Design specifications
- `code_output`: Component code
- `styling_output`: CSS/styling
- `test_output`: Test suite
- `docs_output`: Documentation

**Phases**: Planning → Design → Code → Styling → Testing → Documentation

### API Enhancement

**Type**: `api_enhancement`

**Input**:
- `enhancement_requirements` (str): Enhancement specifications
- `current_api_structure` (dict): Current API details

**Output**:
- `enhancement_analysis`: Analysis and recommendations
- `enhancement_design`: Design for enhancements
- `enhancement_code`: Generated code
- `enhancement_tests`: Test specifications
- `monitoring_setup`: Monitoring configuration

**Phases**: Analysis → Design → Code → Testing → Monitoring

### UI Enhancement

**Type**: `ui_enhancement`

**Input**:
- `enhancement_requirements` (str): Enhancement specifications
- `current_ui_structure` (dict): Current UI details

**Output**:
- `enhancement_analysis`: Analysis and recommendations
- `enhancement_design`: Design for enhancements
- `enhancement_code`: Generated code
- `enhancement_tests`: Test specifications
- `a11y_improvements`: Accessibility improvements

**Phases**: Analysis → Design → Code → Testing → Accessibility → Documentation

## Status Codes

### Success Responses

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |

### Client Error Responses

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 422 | Unprocessable Entity - Validation error |
| 404 | Not Found - Endpoint not found |

### Server Error Responses

| Code | Meaning |
|------|---------|
| 500 | Internal Server Error |
| 503 | Service Unavailable - Workflow not initialized |

## Error Handling

### Error Response Format

```json
{
    "detail": "Error description",
    "type": "ExceptionClassName"
}
```

### Common Errors

**Missing Required Field**:
```json
{
    "detail": "1 validation error for ExecuteRequest\nstory\n  Field required (type=value_error.missing)"
}
```

**Service Not Ready**:
```json
{
    "detail": "Workflow service not ready. Please try again later."
}
```

**Execution Failed**:
```json
{
    "detail": "Workflow execution failed: error description"
}
```

## Rate Limiting

Currently, no rate limiting is enforced. For production deployments, consider:
- Implementing rate limiting at load balancer level
- Using API gateway with throttling
- Adding request queuing for long-running tasks

## Timeouts

### Recommended Timeout Configuration

```
POST /execute
├─ Workflow execution: 180 seconds (default)
└─ Network timeout: 30 seconds

GET /metadata
└─ Response timeout: 5 seconds

GET /health
└─ Response timeout: 5 seconds
```

**Python requests example**:

```python
import requests

# Execute workflow with timeout
response = requests.post(
    "http://localhost:8001/execute",
    json={...},
    timeout=(5, 180)  # (connect, read)
)
```

**cURL example**:

```bash
curl --max-time 180 http://localhost:8001/execute
```

## Authentication

Currently, services do not require authentication. For production:

1. **API Key Authentication**:
   ```python
   headers = {"X-API-Key": "your-api-key"}
   ```

2. **Bearer Token**:
   ```python
   headers = {"Authorization": "Bearer {token}"}
   ```

3. **mTLS (mutual TLS)**:
   - Use HTTPS with client certificates

## Examples

### Execute API Development Workflow

```bash
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "story": "# User Management API\n\nCreate a RESTful API for user management with:\n- Authentication (JWT)\n- CRUD operations\n- Role-based access control",
    "story_requirements": {
      "title": "User Management API",
      "authentication": "JWT",
      "database": "PostgreSQL"
    }
  }'
```

### Execute API Enhancement Workflow

```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "story": "# Batch Processing\n\nAdd batch operation support to the existing API for improved performance",
    "story_requirements": {
      "enhancement_type": "batch_processing",
      "performance_goal": "Handle 1000 items per request"
    }
  }'
```

### Check Service Health

```bash
#!/bin/bash
services=("8001")  # Port numbers

for port in "${services[@]}"; do
    response=$(curl -s http://localhost:$port/health)
    status=$(echo "$response" | jq -r '.status')
    echo "Service on port $port: $status"
done
```

### Poll for Completion

```python
import time
import requests
import json

# Execute workflow
response = requests.post(
    "http://localhost:8001/execute",
    json={"story": "..."}
)

if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Output keys: {list(result['output'].keys())}")
```

## Versioning

API versions follow semantic versioning in responses:

```json
{
    "version": "1.0.0"
}
```

### Version Support Policy

- Major: Breaking changes require new major version
- Minor: Backwards-compatible features
- Patch: Bug fixes and improvements

## OpenAPI Documentation

When FastAPI services are running, OpenAPI documentation is available at:

```
GET /docs                   # Swagger UI
GET /redoc                  # ReDoc
GET /openapi.json          # OpenAPI schema
```

**Example**:
```bash
open http://localhost:8001/docs
```

---

For more information:
- [Configuration Guide](configuration.md)
- [Architecture Documentation](architecture.md)
- [Adding Workflows Guide](adding_workflows.md)
