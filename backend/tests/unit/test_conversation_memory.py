import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.memory.conversation_memory import ConversationMemory

@pytest.fixture
def mock_session_factory():
    with patch("services.memory.conversation_memory.async_session_factory") as mock_factory:
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        yield mock_session

@pytest.fixture
def memory():
    return ConversationMemory(max_turns=5, max_turn_chars=100)

@pytest.mark.asyncio
async def test_memory_add_turn_ignores_empty_session_or_content(memory, mock_session_factory):
    await memory.add_turn("", "user", "hello")
    mock_session_factory.add.assert_not_called()
    
    await memory.add_turn("session_1", "user", "")
    mock_session_factory.add.assert_not_called()

@pytest.mark.asyncio
async def test_memory_add_turn_truncates_long_content(memory, mock_session_factory):
    long_content = "A" * 150
    await memory.add_turn("session_1", "user", long_content)
    
    call_args = mock_session_factory.add.call_args[0][0]
    assert len(call_args.content) == 103 # 100 + "..."
    assert call_args.content.endswith("...")
    assert call_args.session_id == "session_1"

@pytest.mark.asyncio
async def test_memory_format_history_orders_old_to_new(memory, mock_session_factory):
    mock_result = MagicMock()
    
    class MockTurn:
        def __init__(self, role, content):
            self.role = role
            self.content = content
    
    mock_result.scalars.return_value.all.return_value = [
        MockTurn("user", "first"),
        MockTurn("assistant", "second")
    ]
    mock_session_factory.execute.return_value = mock_result
    
    history = await memory.format_history("session_1")
    assert history == "User: first\nAssistant: second"

@pytest.mark.asyncio
async def test_memory_get_recent_context_returns_latest_limit_in_chronological_order(memory, mock_session_factory):
    mock_result = MagicMock()
    
    class MockTurn:
        def __init__(self, role, content):
            self.role = role
            self.content = content
            
    # Mocking order_by desc limit, the db returns newest first
    mock_result.scalars.return_value.all.return_value = [
        MockTurn("assistant", "newest"),
        MockTurn("user", "older")
    ]
    mock_session_factory.execute.return_value = mock_result
    
    context = await memory.get_recent_context("session_1", limit=2)
    # The method does list(turns)[::-1]
    assert len(context) == 2
    assert context[0].content == "older"
    assert context[1].content == "newest"

@pytest.mark.asyncio
async def test_memory_clear_deletes_session_only(memory, mock_session_factory):
    await memory.clear("session_1")
    assert mock_session_factory.execute.called
    
    # Also ignore empty session
    mock_session_factory.reset_mock()
    await memory.clear("")
    mock_session_factory.execute.assert_not_called()

def test_memory_role_label_assistant_aliases():
    memory = ConversationMemory()
    assert memory._role_label("assistant") == "Assistant"
    assert memory._role_label("AI") == "Assistant"
    assert memory._role_label("bot") == "Assistant"
    assert memory._role_label("user") == "User"
    assert memory._role_label("User") == "User"
