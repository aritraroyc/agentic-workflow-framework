# Configuration Guide

## Overview

The Agentic Workflow Framework uses YAML-based configuration for workflow registry and environment variables for sensitive data and runtime settings.

## Configuration Files

### 1. config/workflows.yaml

Defines all available workflows and their metadata.

#### Structure

```yaml
workflows:
  - name: workflow_name                    # Unique identifier
    workflow_type: workflow_type_category  # Category/type
    description: "Human-readable description"
    version: "1.0.0"                      # Semantic versioning
    deployment_mode: embedded|a2a         # Execution mode
    module_path: path.to.workflow          # Python module (embedded only)
    service_url: http://host              # Service URL (A2A only)
    service_port: 8001                    # Port number (A2A only)
    dependencies:                         # Required packages
      - langgraph
      - langchain
    tags:                                 # Categorization tags
      - tag1
      - tag2
    is_active: true                       # Availability flag
    author: "Team Name"                   # Creator
    input_schema:                         # JSON schema for validation
      type: object
      properties:
        field: { type: string }
    output_schema:                        # JSON schema for outputs
      type: object
      properties:
        field: { type: object }
```

#### Embedded Workflow Example

```yaml
- name: api_development
  workflow_type: api_development
  description: "Develops complete RESTful APIs from requirements"
  version: "1.0.0"
  deployment_mode: embedded
  module_path: workflows.children.api_development.workflow
  dependencies:
    - langgraph
    - langchain
    - langchain-anthropic
  tags:
    - api
    - development
    - rest
  is_active: true
  author: "Framework Team"
  input_schema:
    type: object
    properties:
      api_requirements: { type: string }
      preferred_framework: { type: string }
  output_schema:
    type: object
    properties:
      api_plan: { type: object }
      api_design: { type: object }
      code_output: { type: object }
```

#### A2A Service Example

```yaml
- name: api_enhancement_service
  workflow_type: api_enhancement
  description: "Enhances existing APIs (A2A service mode)"
  version: "1.0.0"
  deployment_mode: a2a
  service_url: http://localhost
  service_port: 8001
  dependencies:
    - docker
  tags:
    - api
    - enhancement
    - service
  is_active: true
  author: "Framework Team"
```

### 2. .env File

Environment variables for runtime configuration.

#### Create .env

```bash
# At project root
touch .env
```

#### LLM Configuration

```env
# Anthropic Claude (Default)
ANTHROPIC_API_KEY=sk-ant-v3-...
LLM_MODEL=claude-3-5-sonnet-20241022

# OpenAI (Fallback)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4-turbo-preview
```

#### Service Configuration

```env
# API Enhancement Service
API_ENHANCEMENT_SERVICE_HOST=localhost
API_ENHANCEMENT_SERVICE_PORT=8001

# Coordinator settings
COORDINATOR_TIMEOUT=300  # seconds
COORDINATOR_RETRY_ATTEMPTS=3
COORDINATOR_RETRY_DELAY=5  # seconds

# Invoker settings
INVOKER_TIMEOUT=60  # seconds
INVOKER_RETRY_ATTEMPTS=3
INVOKER_CACHE_SIZE=100
```

#### Execution Configuration

```env
# Execution strategy
EXECUTION_STRATEGY=adaptive  # adaptive, sequential, parallel

# Output configuration
OUTPUT_DIR=./outputs
OUTPUT_FORMAT=json  # json, yaml, markdown

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json, text
```

#### Development Configuration

```env
# Testing
TEST_ENV=local
SKIP_LLM_CALLS=false  # For testing without API calls

# Debug
DEBUG=false
VERBOSE=false
```

## Configuration Loading

### Priority Order

1. Environment variables (`.env` file)
2. System environment variables
3. Configuration files
4. Default values

### Loading Configuration

```python
from workflows.registry.loader import load_registry
from core.llm import get_default_llm_client

# Load workflow registry
registry = load_registry()  # From config/workflows.yaml

# Get LLM client
llm = get_default_llm_client()  # Uses ANTHROPIC_API_KEY or OPENAI_API_KEY
```

## Workflow Configuration

### Deployment Modes

#### Embedded Mode

Workflows run in the same process as the parent:

```yaml
deployment_mode: embedded
module_path: workflows.children.api_development.workflow
```

**Characteristics**:
- Fast (no network calls)
- Direct state passing
- Easier to debug
- Best for local development

#### A2A (Agent-to-Agent) Mode

Workflows run as separate services:

```yaml
deployment_mode: a2a
service_url: http://api-service.example.com
service_port: 8001
```

**Characteristics**:
- Scalable
- Independent deployment
- Service isolation
- Remote execution

### Workflow Tagging

Tags enable filtering and categorization:

```yaml
tags:
  - api              # API-related
  - development      # Development phase
  - rest             # REST architecture
  - fastapi          # Specific framework
```

**Common Tags**:
- Phase: `development`, `enhancement`, `migration`, `testing`
- Domain: `api`, `ui`, `database`, `infrastructure`
- Technology: `fastapi`, `react`, `postgresql`, `docker`
- Status: `stable`, `experimental`, `deprecated`

### Schema Validation

#### Input Schema

Validates workflow input:

```yaml
input_schema:
  type: object
  required:
    - api_requirements
  properties:
    api_requirements:
      type: string
      description: "API requirements and specifications"
      minLength: 10
    preferred_framework:
      type: string
      enum: ["fastapi", "flask", "django"]
```

#### Output Schema

Documents workflow output:

```yaml
output_schema:
  type: object
  properties:
    api_plan:
      type: object
      description: "API planning and analysis"
    api_design:
      type: object
      description: "API design specifications"
    code_output:
      type: object
      description: "Generated code artifacts"
    test_output:
      type: object
      description: "Test specifications"
    docs_output:
      type: object
      description: "API documentation"
```

## Runtime Configuration

### LLM Client Configuration

#### Anthropic Claude

```python
# Automatic (from ANTHROPIC_API_KEY)
from core.llm import get_default_llm_client
client = get_default_llm_client()

# Manual configuration
from langchain_anthropic import ChatAnthropic
client = ChatAnthropic(
    api_key="your-api-key",
    model="claude-3-5-sonnet-20241022",
    temperature=0.7,
    max_tokens=4096,
)
```

#### OpenAI

```python
from langchain_openai import ChatOpenAI
client = ChatOpenAI(
    api_key="your-api-key",
    model="gpt-4-turbo-preview",
    temperature=0.7,
    max_tokens=4096,
)
```

### Timeout Configuration

```python
# In coordinator execution
WORKFLOW_TIMEOUT = 180  # seconds per workflow
COORDINATOR_TIMEOUT = 300  # total coordinator timeout
INVOKER_TIMEOUT = 60  # A2A service timeout
```

### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# Set specific logger levels
logging.getLogger('workflows').setLevel(logging.DEBUG)
logging.getLogger('langgraph').setLevel(logging.INFO)
```

## Configuration Examples

### Minimal Configuration

Simplest working configuration:

```yaml
workflows:
  - name: api_development
    workflow_type: api_development
    version: "1.0.0"
    deployment_mode: embedded
    module_path: workflows.children.api_development.workflow
```

```env
ANTHROPIC_API_KEY=your-key
```

### Production Configuration

Comprehensive production setup:

```yaml
workflows:
  - name: api_development
    workflow_type: api_development
    version: "1.0.0"
    deployment_mode: embedded
    module_path: workflows.children.api_development.workflow
    is_active: true
    author: "Platform Team"
    tags: [api, development, production]
    dependencies: [langgraph, langchain, langchain-anthropic]

  - name: api_enhancement_service
    workflow_type: api_enhancement
    version: "1.0.0"
    deployment_mode: a2a
    service_url: https://api-enhancement.internal.company.com
    service_port: 443
    is_active: true
    author: "Platform Team"
    tags: [api, enhancement, production]
```

```env
# Production LLM
ANTHROPIC_API_KEY=sk-ant-v3-prod-key-...
LLM_MODEL=claude-3-5-sonnet-20241022

# Production service URLs
API_ENHANCEMENT_SERVICE_HOST=api-enhancement.internal.company.com
API_ENHANCEMENT_SERVICE_PORT=443

# Timeouts (production-safe)
COORDINATOR_TIMEOUT=600
INVOKER_TIMEOUT=120

# Output
OUTPUT_DIR=/var/workflow-outputs
OUTPUT_FORMAT=json

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

### Local Development Configuration

```yaml
workflows:
  - name: api_development
    workflow_type: api_development
    version: "1.0.0"
    deployment_mode: embedded
    module_path: workflows.children.api_development.workflow
    is_active: true

  - name: api_enhancement_service
    workflow_type: api_enhancement
    version: "1.0.0"
    deployment_mode: a2a
    service_url: http://localhost
    service_port: 8001
    is_active: true
```

```env
# Development LLM
ANTHROPIC_API_KEY=your-dev-key
LLM_MODEL=claude-3-5-sonnet-20241022

# Local services
API_ENHANCEMENT_SERVICE_HOST=localhost
API_ENHANCEMENT_SERVICE_PORT=8001

# Generous timeouts for debugging
COORDINATOR_TIMEOUT=3600
INVOKER_TIMEOUT=300

# Output
OUTPUT_DIR=./outputs

# Debugging
LOG_LEVEL=DEBUG
DEBUG=true
VERBOSE=true
```

## Validation

### Validate Configuration

```bash
# Check if workflows.yaml is valid YAML
python -c "import yaml; yaml.safe_load(open('config/workflows.yaml'))"

# Load and verify registry
python -c "from workflows.registry.loader import load_registry; r = load_registry(); print(f'Loaded {len(r.list())} workflows')"
```

### Configuration Checks

- All required fields present
- YAML syntax valid
- Module paths importable (for embedded)
- Service URLs reachable (for A2A)
- Environment variables set
- File permissions correct

## Troubleshooting

### Configuration Issues

| Issue | Solution |
|-------|----------|
| `KeyError: ANTHROPIC_API_KEY` | Set in `.env` or environment |
| `ModuleNotFoundError` | Verify `module_path` in workflows.yaml |
| `Connection refused` | Check service URL and port for A2A workflows |
| `Timeout errors` | Increase `COORDINATOR_TIMEOUT` and `INVOKER_TIMEOUT` |
| `Invalid YAML` | Use YAML validator or `python -m yaml` |

### Debugging Configuration

```bash
# View environment variables
python -c "import os; print(os.environ.get('ANTHROPIC_API_KEY', 'NOT SET'))"

# Test LLM client
python -c "from core.llm import get_default_llm_client; c = get_default_llm_client(); print(f'LLM ready: {c is not None}')"

# List loaded workflows
python -c "from workflows.registry.loader import load_registry; print([w.name for w in load_registry().list()])"
```

## Best Practices

1. **Use .env for development** - Keep secrets out of version control
2. **Set LOG_LEVEL=DEBUG during development** - Better debugging info
3. **Use reasonable timeouts** - Too short causes failures, too long wastes resources
4. **Tag workflows appropriately** - Enables filtering and organization
5. **Document schema changes** - Update input/output schemas when workflow changes
6. **Validate configuration at startup** - Catch issues early
7. **Use environment-specific configs** - Different settings for dev/staging/prod
8. **Keep workflows.yaml in sync** - Update when adding/removing workflows

---

For more information, see [Architecture Documentation](architecture.md) and [Adding Workflows Guide](adding_workflows.md).
