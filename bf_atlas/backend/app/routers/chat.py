"""POST /chat — the multi-agent (LangGraph) natural-language endpoint."""

from fastapi import APIRouter, Depends

from app.agents.graph import run_chat
from app.core.security import Session, get_session, resolve_region
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["AI / Agents"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, session: Session = Depends(get_session)) -> ChatResponse:
    # RBAC: the agent only ever queries the region this session may read.
    region = resolve_region(session, req.region)
    state = run_chat(req.question, region)
    return ChatResponse(
        question=req.question,
        region=region,
        intent=state.get("intent"),
        answer=state.get("answer", ""),
        sql=state.get("sql"),
        columns=state.get("columns", []),
        rows=state.get("rows", []),
        structured=state.get("structured"),
        clarification=state.get("clarification"),
        error=state.get("error"),
        trace=state.get("trace", []),
    )
