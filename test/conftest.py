import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from database.database import Base, get_db
from config import TEST_DB_URL
from models import Users
from models.forum import Categories, SubCategories
from models.users import Roles
from main import app
from security.auth import create_access_key
from passlib.hash import bcrypt # type: ignore

import httpx

if TEST_DB_URL[-5:] != "_test":
    raise ValueError("Test DB Name should end on _test")

engine = create_async_engine(
    url=TEST_DB_URL,
    poolclass=NullPool
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
async def roles(db):
    user_role = Roles(name="User")
    premium = Roles(name="Premium")
    admin = Roles(name="Admin")

    db.add_all([user_role, premium, admin])
    await db.commit()
    return {"user": user_role, "premium": premium, "admin": admin}

@pytest_asyncio.fixture
async def current_user(db, roles):
    user = Users(login="admin", password=bcrypt.hash("123"), email="n@n.com", name="s", pfp="static/uploads/pfps/def.png", role_id=roles["user"].id, is_banned=False, ban_reason=None, is_verified=True, verification_token="a")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    yield user

@pytest_asyncio.fixture
async def user(db, roles):
    u = Users(login="bbb", password=bcrypt.hash("123"), email="n@ns.com", name="ss", pfp="static/uploads/pfps/def.png", role_id=roles["user"].id, is_banned=False, ban_reason=None, is_verified=True, verification_token="aa")
    db.add(u)
    await db.commit()
    await db.refresh(u)
    yield u

@pytest_asyncio.fixture
async def categories(db):
    general = Categories(name="General", required_role=None)
    premium = Categories(name="Premium Lounge", required_role="Premium")
    db.add_all([general, premium])
    await db.commit()
    return {"general": general, "premium": premium}

@pytest_asyncio.fixture
async def subcategories(categories, db):
    announcements = SubCategories(name="Announcements", required_role="Admin", category_id=categories["general"].id)
    discussion = SubCategories(name="Discussion", required_role="Premium", category_id=categories["premium"].id)
    db.add_all([announcements, discussion])
    await db.commit()
    return {"announcements": announcements, "discussion": discussion}

@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        app.dependency_overrides[get_db] = override_get_db

        yield ac

        app.dependency_overrides.clear()

@pytest.fixture
def token(current_user):
    access_token = create_access_key(data={"sub": str(current_user.id)})

    return access_token