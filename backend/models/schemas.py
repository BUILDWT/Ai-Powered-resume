from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    query: str = Field(..., description="The user's question to the AI agent.")
    session_id: Optional[str] = Field(None, description="A unique identifier for the chat session.")

class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    answer: str = Field(..., description="The AI agent's answer.")
    source_chunks: List[str] = Field(..., description="List of source document chunks used to generate the answer.")

class HealthCheckResponse(BaseModel):
    """Response model for the health check endpoint."""
    status: str = "ok"

class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str
