from fastapi import APIRouter

from app.data.agent import get_agent_logs

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/logs")
def agent_logs():
    return get_agent_logs()
