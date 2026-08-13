import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.database import Base
from config import TEST_DB_URL
from models import Users

engine = create_async_engine(
    url=TEST_DB_URL
)

TestSession = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db():
    async with TestSession() as ts:
        yield ts

@pytest_asyncio.fixture
async def current_user():
    user = Users(login="admin", password="123", email="n@n.com", name="s", pfp="static/uploads/pfps/def.png", role_id=1, is_banned=False, ban_reason=None, is_verified=True, verification_token="a")
    yield user