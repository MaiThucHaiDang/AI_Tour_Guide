"""Service for managing the Citadel Quiz Room multiplayer game state and LLM-based trivia generation."""

from __future__ import annotations
import logging
import random
import string
import time
import json
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import async_session_factory
from models.artifact import Artifact
from models.graph import KnowledgeFact
from core.dependencies import get_llm_provider

logger = logging.getLogger(__name__)

# Game time limit per question in seconds
QUESTION_TIME_LIMIT = 25

class GameRoom:
    def __init__(
        self,
        room_code: str,
        questions: List[Dict[str, Any]],
        visited_artifacts_summary: str,
        lang: str,
        host_nickname: str | None = None,
    ):
        self.room_code = room_code
        self.status = "lobby" # lobby, playing, scoreboard, finished
        self.questions = questions
        self.visited_artifacts_summary = visited_artifacts_summary
        self.lang = lang
        self.host_nickname = (host_nickname or "").strip()
        self.current_question_index = 0
        self.question_start_time = 0.0
        self.players: Dict[str, Dict[str, Any]] = {} # nickname -> {score, answers: dict}
        self.created_at = time.time()
        self.ai_praise_speech: Optional[str] = None

        if self.host_nickname:
            self.players[self.host_nickname] = {
                "score": 0,
                "answers": {},
                "is_host": True,
            }

    def to_dict(self, include_answers: bool = False) -> Dict[str, Any]:
        """Serialize room state for API response."""
        player_list = []
        for name, p_data in self.players.items():
            player_list.append({
                "nickname": name,
                "score": p_data["score"],
                "answers_count": len(p_data["answers"]),
                "is_host": bool(p_data.get("is_host", False)),
            })
        
        # Sort players by score descending
        player_list.sort(key=lambda x: x["score"], reverse=True)

        current_q = None
        if self.status == "playing" and 0 <= self.current_question_index < len(self.questions):
            q = self.questions[self.current_question_index]
            current_q = {
                "question_text": q["question_text"],
                "options": q["options"],
                "question_index": self.current_question_index,
                "total_questions": len(self.questions),
                "time_limit": QUESTION_TIME_LIMIT,
                "seconds_remaining": max(0.0, QUESTION_TIME_LIMIT - (time.time() - self.question_start_time)) if self.question_start_time > 0 else QUESTION_TIME_LIMIT
            }
        elif self.status == "scoreboard" and 0 <= self.current_question_index < len(self.questions):
            # Show correct answer and explanation during scoreboard step
            q = self.questions[self.current_question_index]
            current_q = {
                "question_text": q["question_text"],
                "options": q["options"],
                "correct_option_index": q["correct_option_index"],
                "explanation": q.get("explanation", ""),
                "question_index": self.current_question_index,
                "total_questions": len(self.questions)
            }

        return {
            "room_code": self.room_code,
            "status": self.status,
            "players": player_list,
            "current_question": current_q,
            "current_question_index": self.current_question_index,
            "total_questions": len(self.questions),
            "lang": self.lang,
            "host_nickname": self.host_nickname,
            "ai_praise_speech": self.ai_praise_speech
        }

class GameService:
    def __init__(self):
        self.active_rooms: Dict[str, GameRoom] = {}
        self.lock = asyncio.Lock()

    def generate_room_code(self) -> str:
        """Generate a unique 4-character uppercase room code."""
        while True:
            code = "".join(random.choices(string.ascii_uppercase, k=4))
            if code not in self.active_rooms:
                return code

    async def create_room(self, visited_ids: List[int], lang: str = "vi", host_nickname: str | None = None) -> str:
        """Create a new game room and generate quiz questions via Gemini."""
        if not visited_ids:
            raise ValueError("Danh sách địa điểm đã đi qua không được rỗng.")
        if host_nickname is not None:
            host_nickname = host_nickname.strip()
            if not host_nickname:
                raise ValueError("Tên chủ phòng không được để trống.")
            if len(host_nickname) > 20:
                raise ValueError("Tên chủ phòng quá dài (tối đa 20 ký tự).")

        # 1. Fetch artifacts and their facts from Database
        artifacts_data = []
        async with async_session_factory() as session:
            # Query Artifacts
            stmt = select(Artifact).where(Artifact.art_id.in_(visited_ids))
            res = await session.execute(stmt)
            artifacts = res.scalars().all()
            
            # Query Facts
            facts_stmt = select(KnowledgeFact).where(KnowledgeFact.artifact_id.in_(visited_ids))
            facts_res = await session.execute(facts_stmt)
            facts = facts_res.scalars().all()
            
            # Group facts by artifact_id
            facts_by_art_id = {}
            for f in facts:
                facts_by_art_id.setdefault(f.artifact_id, []).append(f.fact_text)
            
            for art in artifacts:
                art_name = art.name_vi if lang == "vi" else art.name_en
                history_text = art.history_text_vi if lang == "vi" else art.history_text_en
                art_facts = facts_by_art_id.get(art.art_id, [])
                artifacts_data.append({
                    "name": art_name,
                    "history": history_text[:800],
                    "facts": art_facts
                })

        if not artifacts_data:
            raise ValueError("Không tìm thấy thông tin địa điểm trong cơ sở dữ liệu.")

        # 2. Build Gemini prompt
        context_str = json.dumps(artifacts_data, ensure_ascii=False, indent=2)
        lang_name = "Tiếng Việt" if lang == "vi" else "English"
        
        prompt = (
            f"Bạn là hướng dẫn viên du lịch AI chuyên nghiệp tại Kinh thành Huế. "
            f"Dưới đây là dữ liệu về các địa điểm di tích lịch sử nhóm bạn này vừa trực tiếp tham quan: \n"
            f"{context_str}\n\n"
            f"Hãy thiết kế một bộ gồm đúng 5 câu hỏi trắc nghiệm khách quan bằng {lang_name} dựa trên thông tin trên. "
            f"Yêu cầu các câu hỏi cần tập trung vào các sự kiện lịch sử, nhân vật, kiến trúc đặc sắc để khơi gợi trí nhớ của họ.\n"
            f"Mỗi câu hỏi PHẢI tuân thủ cấu trúc JSON sau:\n"
            f"- question_text: Nội dung câu hỏi.\n"
            f"- options: Mảng chứa đúng 4 đáp án lựa chọn dạng chuỗi văn bản.\n"
            f"- correct_option_index: Chỉ số của đáp án đúng trong mảng (từ 0 đến 3).\n"
            f"- explanation: Lời giải thích ngắn gọn, bổ ích giải thích tại sao đáp án đó đúng.\n\n"
            f"Hãy trả về kết quả định dạng JSON thuần túy theo cấu trúc:\n"
            f"{{\n"
            f"  \"questions\": [\n"
            f"    {{\n"
            f"      \"question_text\": \"...\",\n"
            f"      \"options\": [\"...\", \"...\", \"...\", \"...\"],\n"
            f"      \"correct_option_index\": 0,\n"
            f"      \"explanation\": \"...\"\n"
            f"    }}\n"
            f"  ]\n"
            f"}}\n"
            f"Chú ý: Chỉ trả về nội dung JSON, không thêm bất cứ từ dẫn nhập nào khác."
        )

        # 3. Call LLM to generate questions
        llm = get_llm_provider()
        response = await llm.generate_response(prompt, context_data="", lang=lang)
        
        # Clean LLM markdown codeblock wrapping
        clean_resp = response.strip()
        if clean_resp.startswith("```"):
            lines = clean_resp.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_resp = "\n".join(lines).strip()

        try:
            quiz_data = json.loads(clean_resp)
            questions = quiz_data.get("questions", [])
            if not questions or len(questions) == 0:
                raise ValueError("Bộ câu hỏi trống.")
        except Exception as e:
            logger.error("Failed to parse Gemini generated quiz JSON: %s. Raw response: %s", e, response)
            # Fallback hardcoded questions if JSON generation fails entirely
            questions = self._get_fallback_questions(artifacts_data, lang)

        # 4. Save Room State
        visited_summary = ", ".join([art["name"] for art in artifacts_data])
        async with self.lock:
            room_code = self.generate_room_code()
            self.active_rooms[room_code] = GameRoom(
                room_code=room_code,
                questions=questions,
                visited_artifacts_summary=visited_summary,
                lang=lang,
                host_nickname=host_nickname,
            )
            
        logger.info("Created game room %s with %d questions.", room_code, len(questions))
        return room_code

    def _get_fallback_questions(self, artifacts_data: List[Dict], lang: str) -> List[Dict[str, Any]]:
        """Return fallback questions in case LLM parsing fails."""
        is_vi = lang == "vi"
        questions = []
        for i, art in enumerate(artifacts_data[:5]):
            art_name = art["name"]
            questions.append({
                "question_text": f"Địa điểm tham quan '{art_name}' có tên gọi tiếng Anh là gì?" if is_vi else f"What is the official Vietnamese name of '{art_name}'?",
                "options": [art_name, f"Đại Nội {i}", f"Kinh Thành {i}", "Ngọ Môn"],
                "correct_option_index": 0,
                "explanation": f"Đây là câu hỏi cơ bản giúp bạn nhớ tên địa điểm vừa ghé thăm."
            })
        return questions

    async def join_room(self, room_code: str, nickname: str) -> Dict[str, Any]:
        """Join a player to a lobby."""
        room_code = room_code.upper().strip()
        nickname = nickname.strip()
        
        if not nickname:
            raise ValueError("Biệt danh không được để trống.")
        if len(nickname) > 20:
            raise ValueError("Biệt danh quá dài (tối đa 20 ký tự).")

        async with self.lock:
            room = self.active_rooms.get(room_code)
            if not room:
                raise ValueError("Không tìm thấy phòng chơi này.")
            if room.status != "lobby":
                raise ValueError("Phòng chơi này đã bắt đầu hoặc kết thúc.")
            if nickname in room.players:
                raise ValueError("Biệt danh này đã có người sử dụng trong phòng.")

            room.players[nickname] = {
                "score": 0,
                "answers": {},
                "is_host": False,
            }

        return {"room_code": room_code, "nickname": nickname}

    async def start_game(self, room_code: str) -> Dict[str, Any]:
        """Start the game, moving from lobby to question 0."""
        room_code = room_code.upper().strip()
        async with self.lock:
            room = self.active_rooms.get(room_code)
            if not room:
                raise ValueError("Không tìm thấy phòng chơi này.")
            if room.status != "lobby":
                raise ValueError("Phòng chơi đã bắt đầu.")
            if not room.players:
                raise ValueError("Cần ít nhất 1 người chơi để bắt đầu.")

            room.status = "playing"
            room.current_question_index = 0
            room.question_start_time = time.time()

        return room.to_dict()

    async def submit_answer(self, room_code: str, nickname: str, question_idx: int, selected_option: int) -> Dict[str, Any]:
        """Process player answer submission, calculate score with speed bonus."""
        room_code = room_code.upper().strip()
        nickname = nickname.strip()
        
        async with self.lock:
            room = self.active_rooms.get(room_code)
            if not room:
                raise ValueError("Không tìm thấy phòng chơi.")
            if room.status != "playing":
                raise ValueError("Không ở trạng thái trả lời câu hỏi.")
            if room.current_question_index != question_idx:
                raise ValueError("Câu hỏi này đã trôi qua hoặc chưa bắt đầu.")
            if nickname not in room.players:
                raise ValueError("Người chơi không tồn tại trong phòng.")
            
            player = room.players[nickname]
            if question_idx in player["answers"]:
                raise ValueError("Bạn đã nộp đáp án cho câu hỏi này rồi.")

            # Calculate score
            elapsed_time = time.time() - room.question_start_time
            is_correct = room.questions[question_idx]["correct_option_index"] == selected_option
            
            score_awarded = 0
            if is_correct and elapsed_time <= QUESTION_TIME_LIMIT:
                # Base score: 500, Speed bonus: up to 500 points
                time_ratio = max(0.0, 1.0 - (elapsed_time / float(QUESTION_TIME_LIMIT)))
                speed_bonus = int(500 * time_ratio)
                score_awarded = 500 + speed_bonus
                player["score"] += score_awarded

            player["answers"][question_idx] = {
                "selected_option": selected_option,
                "is_correct": is_correct,
                "score_awarded": score_awarded,
                "elapsed_time": elapsed_time
            }
            if room.players and all(question_idx in p_data["answers"] for p_data in room.players.values()):
                room.status = "scoreboard"

        return {
            "nickname": nickname,
            "is_correct": is_correct,
            "score_awarded": score_awarded,
            "total_score": player["score"]
        }

    async def next_question(self, room_code: str) -> Dict[str, Any]:
        """Move from playing to scoreboard, or from scoreboard to next question/finish."""
        room_code = room_code.upper().strip()
        async with self.lock:
            room = self.active_rooms.get(room_code)
            if not room:
                raise ValueError("Không tìm thấy phòng chơi.")

            if room.status == "playing":
                # Move to scoreboard of the current question
                room.status = "scoreboard"
            elif room.status == "scoreboard":
                # Advance index
                room.current_question_index += 1
                if room.current_question_index >= len(room.questions):
                    room.status = "finished"
                else:
                    room.status = "playing"
                    room.question_start_time = time.time()
            elif room.status == "finished":
                pass # Already ended

        return room.to_dict()

    async def end_game(self, room_code: str) -> Dict[str, Any]:
        """End the game immediately and move to finished state."""
        room_code = room_code.upper().strip()
        async with self.lock:
            room = self.active_rooms.get(room_code)
            if not room:
                raise ValueError("Không tìm thấy phòng chơi.")
            
            room.status = "finished"
            
        return room.to_dict()

    async def get_room_status(self, room_code: str) -> Dict[str, Any]:
        """Get the current room state."""
        room_code = room_code.upper().strip()
        room = self.active_rooms.get(room_code)
        if not room:
            raise ValueError("Không tìm thấy phòng chơi.")
        
        # Auto-advance playing status if timer expires and players haven't advanced
        if room.status == "playing" and room.question_start_time > 0:
            if time.time() - room.question_start_time > QUESTION_TIME_LIMIT + 1:
                # Force move to scoreboard state
                async with self.lock:
                    if room.status == "playing":
                        room.status = "scoreboard"

        return room.to_dict()

    async def generate_ai_praise(self, room_code: str) -> str:
        """Call Gemini to generate a custom victory praise for the winner."""
        room_code = room_code.upper().strip()
        room = self.active_rooms.get(room_code)
        if not room:
            raise ValueError("Không tìm thấy phòng chơi.")
        if room.status != "finished":
            raise ValueError("Trò chơi chưa kết thúc.")
        
        if room.ai_praise_speech:
            return room.ai_praise_speech

        # Find the winner
        player_list = []
        for name, p_data in room.players.items():
            player_list.append((name, p_data["score"]))
        
        if not player_list:
            return "Kính thưa quý bằng hữu, không có ai tham gia cuộc thi trắc nghiệm này cả!"

        player_list.sort(key=lambda x: x[1], reverse=True)
        winner_name, winner_score = player_list[0]
        
        others_summary = ", ".join([f"{name} ({score} điểm)" for name, score in player_list[1:]])
        if not others_summary:
            others_summary = "không có người chơi khác"

        prompt = (
            f"Bạn là hướng dẫn viên du lịch AI dí dỏm, mang phong cách hoàng gia cung đình Huế. "
            f"Hãy viết một bài phát biểu ngắn gọn (khoảng 100 đến 130 từ) bằng tiếng Việt để chúc mừng người chiến thắng trò chơi Đấu trí nhóm:\n"
            f"- Người thắng cuộc: {winner_name} với điểm số xuất sắc {winner_score} điểm.\n"
            f"- Các người chơi khác trong nhóm: {others_summary}.\n"
            f"- Các địa điểm họ đã tham quan trong Đại Nội: {room.visited_artifacts_summary}.\n\n"
            f"Lời chúc mừng cần hài hước, mang đậm sắc thái cổ kính của xứ Huế (ví dụ dùng các từ ngữ như: Dạ, thưa, trẫm, khanh, thánh chỉ, ngự ban, bằng hữu, tài trí hơn người...). "
            f"Hãy pha trò nhẹ nhàng để tạo không khí vui vẻ cho nhóm bạn. Chỉ trả về nội dung bài phát biểu chúc mừng, không thêm lời dẫn."
        )

        llm = get_llm_provider()
        response = await llm.generate_response(prompt, context_data="", lang=room.lang)
        room.ai_praise_speech = response.strip()
        
        return room.ai_praise_speech

# Singleton service instance
game_service = GameService()
