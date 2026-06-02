import pytest
import pytest_asyncio
from core.database import engine

@pytest_asyncio.fixture(autouse=True)
async def cleanup_connections():
    yield
    # Dispose engine connection pool after each test to avoid event loop mismatches in asyncpg
    await engine.dispose()
