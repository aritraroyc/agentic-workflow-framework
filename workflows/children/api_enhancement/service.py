"""
FastAPI service for API Enhancement workflow (A2A deployment mode).

This service exposes the APIEnhancementWorkflow as a remote service with:
- /execute endpoint for workflow invocation
- /metadata endpoint for workflow information
- /health endpoint for service health checks
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from workflows.children.api_enhancement.workflow import APIEnhancementWorkflow
from workflows.parent.state import EnhancedWorkflowState
from core.llm import get_default_llm_client

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="API Enhancement Workflow Service",
    description="A2A service for enhancing existing APIs",
    version="1.0.0",
)

# Initialize workflow instance
workflow_instance: Optional[APIEnhancementWorkflow] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class ExecuteRequest(BaseModel):
    """Request model for workflow execution."""

    story: str = Field(..., description="The enhancement story/requirements")
    story_requirements: Dict[str, Any] = Field(
        default_factory=dict, description="Structured requirements"
    )
    story_type: str = Field(default="api_enhancement", description="Type of story")
    preprocessor_output: Dict[str, Any] = Field(
        default_factory=dict, description="Preprocessor output from parent workflow"
    )
    planner_output: Dict[str, Any] = Field(
        default_factory=dict, description="Planner output from parent workflow"
    )


class ExecuteResponse(BaseModel):
    """Response model for workflow execution."""

    status: str = Field(..., description="Execution status: success, failure, partial")
    output: Dict[str, Any] = Field(..., description="Workflow output")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_notes: Optional[str] = Field(
        None, description="Notes about execution"
    )
    timestamp: str = Field(..., description="Execution timestamp")


class MetadataResponse(BaseModel):
    """Response model for metadata endpoint."""

    name: str = Field(..., description="Workflow name")
    workflow_type: str = Field(..., description="Workflow type")
    description: str = Field(..., description="Workflow description")
    version: str = Field(..., description="Workflow version")
    deployment_mode: str = Field(..., description="Deployment mode (a2a)")
    tags: list = Field(..., description="Workflow tags")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status: healthy, unhealthy")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    workflow_loaded: bool = Field(
        ..., description="Whether workflow instance is loaded"
    )


# ============================================================================
# Service Initialization
# ============================================================================


async def initialize_workflow():
    """Initialize the workflow instance."""
    global workflow_instance
    try:
        logger.info("Initializing API Enhancement workflow instance")
        workflow_instance = APIEnhancementWorkflow()
        logger.info("API Enhancement workflow initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize workflow: {str(e)}")
        raise


# ============================================================================
# API Endpoints
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    await initialize_workflow()


async def ensure_workflow_initialized():
    """Ensure workflow is initialized, initializing if necessary."""
    global workflow_instance
    if not workflow_instance:
        await initialize_workflow()


@app.post(
    "/execute",
    response_model=ExecuteResponse,
    summary="Execute API Enhancement Workflow",
    description="Execute the API enhancement workflow with provided requirements",
)
async def execute(request: ExecuteRequest) -> ExecuteResponse:
    """
    Execute the API Enhancement workflow.

    Args:
        request: ExecuteRequest with workflow input

    Returns:
        ExecuteResponse with execution results

    Raises:
        HTTPException: If workflow is not initialized or execution fails
    """
    await ensure_workflow_initialized()

    if not workflow_instance:
        logger.error("Workflow instance not initialized")
        raise HTTPException(
            status_code=503,
            detail="Workflow service not ready. Please try again later.",
        )

    logger.info(f"Received execution request for: {request.story_type}")

    try:
        # Construct parent state for the workflow
        state: EnhancedWorkflowState = {
            "story": request.story,
            "story_requirements": request.story_requirements,
            "story_type": request.story_type,
            "preprocessor_output": request.preprocessor_output,
            "planner_output": request.planner_output,
            "workflow_tasks": [],
            "task_results": [],
            "execution_log": [],
        }

        # Execute workflow
        result = await workflow_instance.execute(state)

        logger.info(f"Workflow execution completed with status: {result['status']}")

        return ExecuteResponse(
            status=result.get("status", "success"),
            output=result.get("output", {}),
            error=result.get("error"),
            execution_notes=result.get("execution_notes", ""),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@app.get(
    "/metadata",
    response_model=MetadataResponse,
    summary="Get Workflow Metadata",
    description="Retrieve metadata about the API Enhancement workflow",
)
async def get_metadata() -> MetadataResponse:
    """
    Get workflow metadata.

    Returns:
        MetadataResponse with workflow information
    """
    await ensure_workflow_initialized()

    if not workflow_instance:
        raise HTTPException(
            status_code=503, detail="Workflow service not ready"
        )

    try:
        metadata = workflow_instance.get_metadata()

        return MetadataResponse(
            name=metadata.name,
            workflow_type=metadata.workflow_type,
            description=metadata.description,
            version=metadata.version,
            deployment_mode="a2a",
            tags=metadata.tags,
        )

    except Exception as e:
        logger.error(f"Error retrieving metadata: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metadata")


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check service health and readiness",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse with service status
    """
    try:
        # Check if LLM client is available
        llm_client = get_default_llm_client()
        llm_ready = llm_client is not None

        status = "healthy" if workflow_instance and llm_ready else "unhealthy"

        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            workflow_loaded=workflow_instance is not None,
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            workflow_loaded=False,
        )


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get(
    "/",
    summary="Service Root",
    description="Get service information",
)
async def root():
    """Service root endpoint."""
    return {
        "service": "API Enhancement Workflow",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "execute": "/execute (POST)",
            "metadata": "/metadata (GET)",
            "health": "/health (GET)",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
    )
