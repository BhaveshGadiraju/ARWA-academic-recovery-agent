"""ARWA chat endpoints. The Groq key never leaves the server."""

from typing import List

from fastapi import APIRouter, Depends, Query, Response, status

from api.auth import get_insights
from backend.services.agent_service import ArwaAgent, chat_rate_limiter
from backend.services.insights_service import InsightsService
from models.schemas import ChatMessageResponse, ChatReplyResponse, ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/messages", response_model=List[ChatMessageResponse])
def list_messages(
    limit: int = Query(50, ge=1, le=200),
    insights: InsightsService = Depends(get_insights),
):
    """The conversation so far, oldest first."""
    return insights.repo.list_chat_messages(limit=limit)


@router.delete("/messages", status_code=status.HTTP_204_NO_CONTENT)
def clear_messages(insights: InsightsService = Depends(get_insights)):
    """Start a fresh conversation."""
    insights.repo.clear_chat()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("", response_model=ChatReplyResponse, status_code=status.HTTP_201_CREATED)
def send_message(body: ChatRequest, insights: InsightsService = Depends(get_insights)):
    """Ask ARWA a question. The answer is grounded in the student's data via tools."""
    repo = insights.repo
    chat_rate_limiter.check(repo.user_id)

    history = [{"role": m["role"], "content": m["content"]} for m in repo.list_chat_messages(limit=12)]
    repo.add_chat_message("user", body.message)

    reply = ArwaAgent(insights).reply(body.message, history)
    saved = repo.add_chat_message(
        "assistant",
        reply.content[:8000],
        metadata={"tools_used": reply.tools_used, "ai_powered": reply.ai_powered},
    )
    return ChatReplyResponse(message=saved, tools_used=reply.tools_used, ai_powered=reply.ai_powered)
