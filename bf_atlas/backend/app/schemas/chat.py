"""Pydantic models for the multi-agent /chat endpoint."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["What are my best opportunities this week?"])
    region: Optional[str] = Field(None, examples=["EU-West"])


class AgentStep(BaseModel):
    agent: str
    action: str
    detail: str = ""
    data: Optional[Any] = None


class ChatResponse(BaseModel):
    question: str
    region: Optional[str] = None
    intent: Optional[str] = None
    answer: str
    sql: Optional[str] = None
    columns: list = []
    rows: list = []
    structured: Optional[Any] = None
    clarification: Optional[str] = None
    error: Optional[str] = None
    trace: list[AgentStep] = []
