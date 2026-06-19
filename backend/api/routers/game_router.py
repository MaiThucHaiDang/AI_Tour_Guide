"""Router for Citadel Quiz Room multiplayer game endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from services.map.game_service import game_service

router = APIRouter(
    prefix="/api/v1/game",
    tags=["game"]
)

# ─── Pydantic Request Schemas ───────────────────────────────────────────────

class CreateRoomRequest(BaseModel):
    visited_ids: List[int] = Field(..., description="List of visited artifact IDs to generate questions from.")
    lang: str = Field("vi", description="Language code: vi or en")
    host_nickname: Optional[str] = Field(default=None, description="Nickname of the room creator/player", max_length=20)

class JoinRoomRequest(BaseModel):
    room_code: str = Field(..., description="4-character room code")
    nickname: str = Field(..., description="Player's nickname (max 20 characters)")

class StartGameRequest(BaseModel):
    room_code: str = Field(..., description="4-character room code")

class SubmitAnswerRequest(BaseModel):
    room_code: str = Field(..., description="4-character room code")
    nickname: str = Field(..., description="Player's nickname")
    question_index: int = Field(..., description="Index of the question being answered")
    selected_option: int = Field(..., description="Selected option index (0 to 3)")

class NextQuestionRequest(BaseModel):
    room_code: str = Field(..., description="4-character room code")

class EndGameRequest(BaseModel):
    room_code: str = Field(..., description="4-character room code")


# ─── Router Endpoints ────────────────────────────────────────────────────────

@router.post("/create")
async def create_room(req: CreateRoomRequest):
    """Create a new quiz room with AI-generated trivia questions."""
    try:
        room_code = await game_service.create_room(req.visited_ids, req.lang, req.host_nickname)
        room = await game_service.get_room_status(room_code)
        return {
            "success": True,
            "room_code": room_code,
            "host_nickname": req.host_nickname,
            "room": room,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Error creating game room")
        raise HTTPException(status_code=500, detail=f"Không thể tạo phòng chơi: {str(e)}")

@router.post("/join")
async def join_room(req: JoinRoomRequest):
    """Join a player to a lobby."""
    try:
        result = await game_service.join_room(req.room_code, req.nickname)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_game(req: StartGameRequest):
    """Start the game (host only)."""
    try:
        result = await game_service.start_game(req.room_code)
        return {"success": True, "room": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/answer")
async def submit_answer(req: SubmitAnswerRequest):
    """Submit a player's answer for scoring."""
    try:
        result = await game_service.submit_answer(
            room_code=req.room_code,
            nickname=req.nickname,
            question_idx=req.question_index,
            selected_option=req.selected_option
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/next")
async def next_question(req: NextQuestionRequest):
    """Advance to scoreboard or next question (host only)."""
    try:
        result = await game_service.next_question(req.room_code)
        return {"success": True, "room": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end")
async def end_game(req: EndGameRequest):
    """End the game immediately (host only)."""
    try:
        result = await game_service.end_game(req.room_code)
        return {"success": True, "room": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/room/{room_code}/status")
async def get_room_status(room_code: str):
    """Poll the room's current state."""
    try:
        result = await game_service.get_room_status(room_code)
        return {"success": True, "room": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/room/{room_code}/praise")
async def get_room_praise(room_code: str):
    """Get the AI praise speech for the winner (host only, after game finishes)."""
    try:
        praise_text = await game_service.generate_ai_praise(room_code)
        return {"success": True, "praise": praise_text}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@router.get("/local-ip")
async def get_room_local_ip():
    """Discover host machine local LAN IP address."""
    try:
        ip = get_local_ip()
        return {"success": True, "local_ip": ip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
