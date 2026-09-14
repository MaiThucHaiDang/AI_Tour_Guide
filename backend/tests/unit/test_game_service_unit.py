import pytest
import time
import json
from unittest.mock import AsyncMock, patch, MagicMock

from services.map.game_service import GameRoom, GameService, QUESTION_TIME_LIMIT

# Dummy models
class FakeArtifact:
    def __init__(self, art_id, vi, en):
        self.art_id = art_id
        self.name_vi = vi
        self.name_en = en
        self.history_text_vi = vi + " hist"
        self.history_text_en = en + " hist"

class FakeFact:
    def __init__(self, art_id, text):
        self.artifact_id = art_id
        self.fact_text = text

@pytest.fixture
def mock_db_session():
    with patch("services.map.game_service.async_session_factory") as mock_factory:
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        
        # Default mock returns 1 artifact and 1 fact
        res1 = MagicMock()
        res1.scalars.return_value.all.return_value = [FakeArtifact(1, "Ngọ Môn", "Ngo Mon Gate")]
        res2 = MagicMock()
        res2.scalars.return_value.all.return_value = [FakeFact(1, "Built in 1833")]
        mock_session.execute.side_effect = [res1, res2]
        
        yield mock_session

@pytest.fixture
def mock_llm():
    with patch("services.map.game_service.get_llm_provider") as mock_get_llm:
        mock_provider = AsyncMock()
        mock_get_llm.return_value = mock_provider
        
        # Default LLM response
        valid_json = json.dumps({
            "questions": [
                {
                    "question_text": "Q1",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0,
                    "explanation": "Exp 1"
                }
            ]
        })
        mock_provider.generate_response.return_value = valid_json
        yield mock_provider

# 1. GameRoom.__init__
def test_game_room_adds_host_player_when_host_nickname_present():
    room = GameRoom("ABCD", [], "Summary", "vi", "Host")
    assert "Host" in room.players
    assert room.players["Host"]["is_host"] is True

# 2. GameRoom.to_dict (hides answers)
def test_game_room_to_dict_hides_answers_in_playing():
    questions = [{"question_text": "Q1", "options": ["A", "B", "C", "D"], "correct_option_index": 0, "explanation": "Exp"}]
    room = GameRoom("ABCD", questions, "Summary", "vi")
    room.status = "playing"
    room.question_start_time = time.time()
    
    data = room.to_dict()
    assert data["status"] == "playing"
    assert "correct_option_index" not in data["current_question"]
    assert "explanation" not in data["current_question"]

# 3. GameRoom.to_dict (shows answers)
def test_game_room_to_dict_shows_answer_on_scoreboard():
    questions = [{"question_text": "Q1", "options": ["A", "B", "C", "D"], "correct_option_index": 0, "explanation": "Exp"}]
    room = GameRoom("ABCD", questions, "Summary", "vi")
    room.status = "scoreboard"
    
    data = room.to_dict()
    assert data["status"] == "scoreboard"
    assert data["current_question"]["correct_option_index"] == 0
    assert data["current_question"]["explanation"] == "Exp"

# 4. generate_room_code
def test_generate_room_code_unique_uppercase_four_chars():
    service = GameService()
    service.active_rooms["AAAA"] = "dummy"
    
    with patch("random.choices") as mock_choices:
        mock_choices.side_effect = [["A", "A", "A", "A"], ["B", "C", "D", "E"]]
        code = service.generate_room_code()
        
    assert code == "BCDE"
    assert code.isupper()
    assert len(code) == 4

# 5. create_room - empty visited
@pytest.mark.asyncio
async def test_create_room_rejects_empty_visited_ids():
    service = GameService()
    with pytest.raises(ValueError, match="Danh sách địa điểm đã đi qua không được rỗng"):
        await service.create_room([], "vi", "Host")

# 6. create_room - bad host name
@pytest.mark.asyncio
async def test_create_room_rejects_empty_or_long_host_name():
    service = GameService()
    with pytest.raises(ValueError, match="Tên chủ phòng không được để trống"):
        await service.create_room([1], "vi", "   ")
    with pytest.raises(ValueError, match="Tên chủ phòng quá dài"):
        await service.create_room([1], "vi", "A" * 21)

# 7. create_room - fetches artifacts and facts
@pytest.mark.asyncio
async def test_create_room_fetches_artifacts_and_facts(mock_db_session, mock_llm):
    service = GameService()
    room_code = await service.create_room([1], "vi", "Host")
    
    # Assert DB was queried
    assert mock_db_session.execute.call_count == 2
    
    # Assert LLM was called with the prompt containing 'Ngọ Môn' and 'Built in 1833'
    prompt_used = mock_llm.generate_response.call_args[0][0]
    assert "Ngọ Môn" in prompt_used
    assert "Built in 1833" in prompt_used
    
    assert room_code in service.active_rooms

# 8. create_room - parses json
@pytest.mark.asyncio
async def test_create_room_parses_json_code_block(mock_db_session, mock_llm):
    service = GameService()
    valid_json = """```json
{
  "questions": [
    {
      "question_text": "Q1",
      "options": ["A", "B", "C", "D"],
      "correct_option_index": 0,
      "explanation": "Exp"
    }
  ]
}
```"""
    mock_llm.generate_response.return_value = valid_json
    room_code = await service.create_room([1], "vi", "Host")
    room = service.active_rooms[room_code]
    assert len(room.questions) == 1
    assert room.questions[0]["question_text"] == "Q1"

# 9. create_room - fallback on bad json
@pytest.mark.asyncio
async def test_create_room_fallback_questions_on_bad_llm_json(mock_db_session, mock_llm):
    service = GameService()
    mock_llm.generate_response.return_value = "invalid json"
    room_code = await service.create_room([1], "vi", "Host")
    room = service.active_rooms[room_code]
    assert len(room.questions) > 0
    assert "Ngọ Môn" in room.questions[0]["options"][0]

# 10. create_room - validates question shape
@pytest.mark.asyncio
async def test_create_room_validates_question_shape(mock_db_session, mock_llm):
    # Trả về JSON hợp lệ nhưng chỉ có 3 options
    service = GameService()
    bad_shape = json.dumps({
        "questions": [
            {
                "question_text": "Q1",
                "options": ["A", "B", "C"], # thiếu 1 option
                "correct_option_index": 0,
                "explanation": "Exp"
            }
        ]
    })
    mock_llm.generate_response.return_value = bad_shape
    
    # Kì vọng fallback sẽ được gọi
    room_code = await service.create_room([1], "vi", "Host")
    room = service.active_rooms[room_code]
    assert len(room.questions) > 0
    # Fallback câu hỏi sẽ có chứa "tiếng Anh là gì" hoặc options có tên di tích
    assert "Ngọ Môn" in room.questions[0]["options"][0]

# 11. _get_fallback_questions
def test_fallback_questions_vi_en():
    service = GameService()
    arts = [{"name": "Điện Thái Hòa"}]
    
    q_vi = service._get_fallback_questions(arts, "vi")
    assert "tiếng Anh là gì" in q_vi[0]["question_text"]
    
    q_en = service._get_fallback_questions(arts, "en")
    assert "Vietnamese name" in q_en[0]["question_text"]

# 12. join_room
@pytest.mark.asyncio
async def test_join_room_rejects_missing_room_non_lobby_duplicate_long_empty():
    service = GameService()
    service.active_rooms["AAAA"] = GameRoom("AAAA", [], "", "vi")
    
    # Missing room
    with pytest.raises(ValueError, match="Không tìm thấy"):
        await service.join_room("BBBB", "P1")
        
    # Empty or long nickname
    with pytest.raises(ValueError, match="không được để trống"):
        await service.join_room("AAAA", "  ")
    with pytest.raises(ValueError, match="quá dài"):
        await service.join_room("AAAA", "A" * 21)
        
    # Duplicate
    await service.join_room("AAAA", "P1")
    with pytest.raises(ValueError, match="đã có người sử dụng"):
        await service.join_room("AAAA", "P1")
        
    # Non lobby
    service.active_rooms["AAAA"].status = "playing"
    with pytest.raises(ValueError, match="đã bắt đầu hoặc kết thúc"):
        await service.join_room("AAAA", "P2")

# 13. start_game
@pytest.mark.asyncio
async def test_start_game_requires_lobby_and_players():
    service = GameService()
    # Missing
    with pytest.raises(ValueError, match="Không tìm thấy"):
        await service.start_game("XXXX")
        
    # No players
    service.active_rooms["AAAA"] = GameRoom("AAAA", [], "", "vi")
    with pytest.raises(ValueError, match="Cần ít nhất 1 người chơi"):
        await service.start_game("AAAA")
        
    # Playing
    service.active_rooms["AAAA"].players["P1"] = {}
    service.active_rooms["AAAA"].status = "playing"
    with pytest.raises(ValueError, match="đã bắt đầu"):
        await service.start_game("AAAA")
        
    # Valid
    service.active_rooms["BBBB"] = GameRoom("BBBB", [{"question_text": "Q", "options": ["A","B","C","D"], "correct_option_index": 0}], "", "vi")
    service.active_rooms["BBBB"].players["P1"] = {"score": 0, "answers": {}}
    await service.start_game("BBBB")
    assert service.active_rooms["BBBB"].status == "playing"

# 14. submit_answer - scores correctly
@pytest.mark.asyncio
async def test_submit_answer_scores_correct_fast_answer():
    service = GameService()
    room = GameRoom("AAAA", [{"question_text": "Q", "options": ["A","B","C","D"], "correct_option_index": 1}], "", "vi")
    room.players["P1"] = {"score": 0, "answers": {}}
    room.status = "playing"
    room.current_question_index = 0
    # Simulate answering instantly
    room.question_start_time = time.time()
    
    service.active_rooms["AAAA"] = room
    res = await service.submit_answer("AAAA", "P1", 0, 1)
    
    assert res["is_correct"] is True
    assert 500 <= res["score_awarded"] <= 1000
    assert res["total_score"] == res["score_awarded"]
    assert room.players["P1"]["answers"][0]["is_correct"] is True

# 15. submit_answer - no score after time limit
@pytest.mark.asyncio
async def test_submit_answer_no_score_after_time_limit():
    service = GameService()
    room = GameRoom("AAAA", [{"question_text": "Q", "options": ["A","B","C","D"], "correct_option_index": 1}], "", "vi")
    room.players["P1"] = {"score": 0, "answers": {}}
    room.status = "playing"
    room.current_question_index = 0
    # Simulate time expired
    room.question_start_time = time.time() - 30 
    service.active_rooms["AAAA"] = room
    
    res = await service.submit_answer("AAAA", "P1", 0, 1)
    assert res["is_correct"] is True
    assert res["score_awarded"] == 0

# 16. submit_answer - rejects
@pytest.mark.asyncio
async def test_submit_answer_rejects_wrong_question_unknown_player_duplicate():
    service = GameService()
    room = GameRoom("AAAA", [{"question_text": "Q", "options": ["A","B","C","D"], "correct_option_index": 1}], "", "vi")
    room.status = "playing"
    room.current_question_index = 0
    room.players["P1"] = {"score": 0, "answers": {0: {}}}
    service.active_rooms["AAAA"] = room
    
    with pytest.raises(ValueError, match="Không tìm thấy"):
        await service.submit_answer("BBBB", "P1", 0, 1)
        
    room.status = "lobby"
    with pytest.raises(ValueError, match="Không ở trạng thái trả lời"):
        await service.submit_answer("AAAA", "P1", 0, 1)
        
    room.status = "playing"
    with pytest.raises(ValueError, match="đã trôi qua"):
        await service.submit_answer("AAAA", "P1", 1, 1)
        
    with pytest.raises(ValueError, match="Người chơi không tồn tại"):
        await service.submit_answer("AAAA", "P2", 0, 1)
        
    with pytest.raises(ValueError, match="đã nộp đáp án"):
        await service.submit_answer("AAAA", "P1", 0, 1)

# 17. submit_answer - moves scoreboard
@pytest.mark.asyncio
async def test_submit_answer_moves_scoreboard_when_all_answered():
    service = GameService()
    room = GameRoom("AAAA", [{"question_text": "Q", "options": ["A","B","C","D"], "correct_option_index": 1}], "", "vi")
    room.players["P1"] = {"score": 0, "answers": {}}
    room.players["P2"] = {"score": 0, "answers": {}}
    room.status = "playing"
    room.current_question_index = 0
    room.question_start_time = time.time()
    service.active_rooms["AAAA"] = room
    
    await service.submit_answer("AAAA", "P1", 0, 1)
    assert room.status == "playing"
    
    await service.submit_answer("AAAA", "P2", 0, 1)
    assert room.status == "scoreboard"

# 18. next_question - playing to scoreboard
@pytest.mark.asyncio
async def test_next_question_playing_to_scoreboard():
    service = GameService()
    room = GameRoom("AAAA", [{"question_text": "Q", "options": ["A","B","C","D"], "correct_option_index": 1}], "", "vi")
    room.status = "playing"
    service.active_rooms["AAAA"] = room
    
    await service.next_question("AAAA")
    assert room.status == "scoreboard"

# 19. next_question - scoreboard to next or finished
@pytest.mark.asyncio
async def test_next_question_scoreboard_to_next_or_finished():
    service = GameService()
    room = GameRoom("AAAA", [{"question_text": "Q1", "options": ["A","B","C","D"], "correct_option_index": 1}, {"question_text": "Q2", "options": ["A","B","C","D"], "correct_option_index": 2}], "", "vi")
    room.status = "scoreboard"
    room.current_question_index = 0
    service.active_rooms["AAAA"] = room
    
    await service.next_question("AAAA")
    assert room.status == "playing"
    assert room.current_question_index == 1
    
    room.status = "scoreboard"
    await service.next_question("AAAA")
    assert room.status == "finished"

# 20. end_game
@pytest.mark.asyncio
async def test_end_game_sets_finished():
    service = GameService()
    room = GameRoom("AAAA", [], "", "vi")
    room.status = "playing"
    service.active_rooms["AAAA"] = room
    
    await service.end_game("AAAA")
    assert room.status == "finished"

# 21. get_room_status - auto scoreboard
@pytest.mark.asyncio
async def test_get_room_status_auto_scoreboard_after_timer():
    service = GameService()
    room = GameRoom("AAAA", [{"question_text": "Q", "options": ["A","B","C","D"], "correct_option_index": 1}], "", "vi")
    room.status = "playing"
    room.question_start_time = time.time() - 30
    service.active_rooms["AAAA"] = room
    
    await service.get_room_status("AAAA")
    assert room.status == "scoreboard"

# 22. generate_ai_praise
@pytest.mark.asyncio
async def test_generate_ai_praise_requires_finished_and_caches_result(mock_llm):
    service = GameService()
    room = GameRoom("AAAA", [], "Ngọ Môn", "vi")
    room.status = "playing"
    service.active_rooms["AAAA"] = room
    
    with pytest.raises(ValueError, match="Trò chơi chưa kết thúc"):
        await service.generate_ai_praise("AAAA")
        
    room.status = "finished"
    room.players["P1"] = {"score": 1000}
    room.players["P2"] = {"score": 500}
    
    mock_llm.generate_response.return_value = "Chúc mừng P1"
    
    praise1 = await service.generate_ai_praise("AAAA")
    assert praise1 == "Chúc mừng P1"
    assert mock_llm.generate_response.call_count == 1
    
    praise2 = await service.generate_ai_praise("AAAA")
    assert praise2 == "Chúc mừng P1"
    # LLM should not be called again
    assert mock_llm.generate_response.call_count == 1
