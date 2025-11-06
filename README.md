# Agentic Workflow Framework

A LangGraph-based orchestration framework for intelligent agentic workflows in software development. The framework enables complex, multi-step development tasks (API development, UI development, API/UI enhancements) with autonomous agent coordination, adaptive planning, and intelligent workflow routing.

## 🎯 Key Features

- **Parent-Child Architecture**: Master workflow that intelligently routes tasks to specialized child workflows
- **Multi-Agent Orchestration**: Preprocessor, Planner, Coordinator, and Aggregator agents working in concert
- **Dynamic Workflow Registry**: Support for embedded and A2A (Agent-to-Agent) service deployments
- **Async-First Design**: Full async/await support for high-performance concurrent execution
- **Intelligent Planning**: LLM-powered analysis and workflow selection
- **Flexible Deployment**: Run locally or as distributed microservices via Docker
- **Comprehensive Error Handling**: Graceful fallbacks and robust error recovery

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Available Workflows](#available-workflows)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Deployment](#deployment)
- [Development](#development)
- [API Reference](#api-reference)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Git
- Docker (for containerized deployment)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic-workflow-framework

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run a workflow with a story file
python main.py --story-file examples/stories/api_development.md

# Or provide story via stdin
cat examples/stories/ui_development.md | python main.py

# View help
python main.py --help
```

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────┐
│         Parent Workflow                 │
│  ┌────────────────────────────────────┐ │
│  │ 1. Preprocessor Agent              │ │
│  │    (Parses & structures input)     │ │
│  └──────────────────┬─────────────────┘ │
│                     │                    │
│  ┌──────────────────▼─────────────────┐ │
│  │ 2. Planner Agent                   │ │
│  │    (Analyzes & plans tasks)        │ │
│  └──────────────────┬─────────────────┘ │
│                     │                    │
│  ┌──────────────────▼─────────────────┐ │
│  │ 3. Coordinator Agent               │ │
│  │    (Routes to child workflows)     │ │
│  └──────┬───────────────────────────┬─┘ │
└─────────┼───────────────────────────┼────┘
          │                           │
    ┌─────▼──────┐             ┌─────▼──────┐
    │ Child WF 1 │             │ Child WF N │
    │ (Embedded) │             │ (A2A Svc)  │
    └─────┬──────┘             └─────┬──────┘
          │                           │
    ┌─────▼─────────────────────────┬┘
    │                               │
    │  ┌──────────────────────────▼─┐
    │  │ 4. Aggregator Agent        │
    │  │    (Collects & formats)    │
    │  └────────────────────────────┘
    │
    └─► outputs/ (Results & artifacts)
```

### Workflow Execution Flow

1. **Preprocessor**: Validates input, extracts structure, generates metadata
2. **Planner**: Analyzes requirements, selects appropriate workflows, creates execution plan
3. **Coordinator**: Routes to child workflows, manages execution (sequential/parallel)
4. **Child Workflows**: Execute specialized tasks (development, enhancement, etc.)
5. **Aggregator**: Collects results, generates reports, formats outputs

For more details, see [Architecture Documentation](docs/architecture.md).

## 📚 Available Workflows

### Embedded Workflows (Local Execution)

| Workflow | Type | Description | Phases |
|----------|------|-------------|--------|
| **API Development** | `api_development` | Create complete RESTful APIs from scratch | Planning → Design → Code → Testing → Documentation |
| **UI Development** | `ui_development` | Develop web UIs with modern frameworks | Planning → Design → Code → Styling → Testing → Documentation |
| **API Enhancement** | `api_enhancement` | Add features to existing APIs | Analysis → Design → Code → Testing → Monitoring |
| **UI Enhancement** | `ui_enhancement` | Improve existing UIs with focus on accessibility | Analysis → Design → Code → Testing → A11y → Documentation |

### A2A Service Workflows (Remote Deployment)

- **API Enhancement Service** (Port 8001): Remote service version of API Enhancement workflow

## 💻 Installation

### From Source

```bash
# Clone repository
git clone <repository-url>
cd agentic-workflow-framework

# Setup Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pytest tests/ -v
```

### Docker Setup

```bash
# Build API Enhancement service image
docker build -f Dockerfile.api_enhancement -t api-enhancement-service:latest .

# Or use Docker Compose for full stack
docker-compose up
```

## ⚙️ Configuration

### Main Configuration

Primary configuration is defined in `config/workflows.yaml`:

```yaml
workflows:
  - name: api_development
    workflow_type: api_development
    description: "Develops complete RESTful APIs..."
    version: "1.0.0"
    deployment_mode: embedded
    module_path: workflows.children.api_development.workflow
    is_active: true
```

### Environment Variables

Create a `.env` file in the project root:

```env
# LLM Configuration
ANTHROPIC_API_KEY=your-api-key-here
LLM_MODEL=claude-3-5-sonnet-20241022

# Optional: OpenAI configuration
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4

# Service Configuration
API_ENHANCEMENT_SERVICE_PORT=8001
COORDINATOR_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
```

For detailed configuration options, see [Configuration Guide](docs/configuration.md).

## 📖 Usage

### Basic Workflow Execution

```python
import asyncio
from workflows.parent.graph import create_enhanced_parent_workflow
from workflows.registry.loader import load_registry
from workflows.registry.invoker import WorkflowInvoker

async def run_workflow():
    # Load registry and create parent workflow
    registry = load_registry()
    invoker = WorkflowInvoker()

    # Create parent workflow
    parent_workflow = create_enhanced_parent_workflow(registry, invoker)

    # Execute with a story
    result = await parent_workflow.ainvoke({
        "story": "# API Development\nCreate a User Management API..."
    })

    return result

# Run
result = asyncio.run(run_workflow())
```

### Using the CLI

```bash
# Run with story file
python main.py --story-file examples/stories/api_development.md

# Run with custom output directory
python main.py --story-file story.md --output-dir ./results

# View help
python main.py --help
```

### Example Stories

See the `examples/stories/` directory for example input files:

- `api_development.md` - Complete User Management API
- `ui_development.md` - Customer Dashboard UI
- `api_enhancement.md` - API Enhancement with Webhooks
- `complex_ecommerce_platform.md` - Multi-workflow project

## 🐳 Deployment

### Local Development

```bash
# Start parent workflow service
python main.py --story-file examples/stories/api_development.md

# Start API Enhancement A2A service (optional)
python -m uvicorn workflows.children.api_enhancement.service:app --port 8001
```

### Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See [Deployment Guide](docs/deployment.md) for more options.

## 🔧 Development

### Project Structure

```
agentic-workflow-framework/
├── workflows/
│   ├── parent/               # Parent workflow & agents
│   │   ├── agents/           # Preprocessor, Planner, Coordinator, Aggregator
│   │   ├── nodes.py          # LangGraph nodes
│   │   ├── graph.py          # Graph assembly
│   │   └── state.py          # State schemas
│   └── children/             # Child workflows
│       ├── base.py           # Abstract base class
│       ├── api_development/  # API development workflow
│       ├── ui_development/   # UI development workflow
│       ├── api_enhancement/  # API enhancement workflow
│       └── ui_enhancement/   # UI enhancement workflow
├── core/
│   └── llm.py               # LLM client wrapper
├── config/
│   └── workflows.yaml       # Workflow registry configuration
├── examples/
│   └── stories/             # Example input stories
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── main.py                  # CLI entry point
└── requirements.txt         # Python dependencies
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_api_development.py -v

# Run with coverage
pytest tests/ --cov=workflows --cov-report=html

# Run integration tests only
pytest tests/integration/ -v
```

### Adding a New Workflow

See [Adding New Workflows Guide](docs/adding_workflows.md) for step-by-step instructions to create a new child workflow.

## 📊 Test Coverage

Current test suite: **314 tests** across unit and integration tests

- Unit Tests: Core functionality validation
- Integration Tests: End-to-end workflow execution
- Coverage Areas: State management, agents, workflows, graph execution

Run tests with:
```bash
pytest tests/ -v --cov=workflows
```

## 🔌 API Reference

### Parent Workflow Input

```python
{
    "story": str,                          # Main requirement description
    "story_requirements": dict,            # Structured requirements
    "story_type": str,                     # Type: api_development, ui_development, etc.
    "preprocessor_output": dict,           # Preprocessor output
    "planner_output": dict,                # Planner output
}
```

### API Enhancement Service (A2A)

**Endpoint**: POST `/execute`

```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "story": "Add batch processing to existing API",
    "story_requirements": {
      "title": "Batch Processing"
    }
  }'
```

**Response**:
```json
{
    "status": "success",
    "output": {
        "enhancement_analysis": {},
        "enhancement_design": {},
        "enhancement_code": {},
        "enhancement_tests": {},
        "monitoring_setup": {}
    },
    "timestamp": "2024-11-06T10:30:00"
}
```

For complete API documentation, see [API Reference](docs/api_reference.md).

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run tests: `pytest tests/`
6. Commit with clear messages
7. Push to your fork
8. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🆘 Support

- Check the [documentation](docs/) for detailed guides
- Review [example stories](examples/stories/) for usage patterns
- Run tests to verify your setup: `pytest tests/`
- Check [API reference](docs/api_reference.md) for endpoint documentation

## 🗺️ Roadmap

- [ ] Multi-language support for generated code
- [ ] Advanced caching and checkpointing
- [ ] Custom workflow templating
- [ ] Web UI for workflow management
- [ ] Real-time execution monitoring
- [ ] Workflow analytics and reporting

---

**Built with LangGraph + Anthropic Claude** | [Documentation](docs/) | [Contributing](CONTRIBUTING.md)
