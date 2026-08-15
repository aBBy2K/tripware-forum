from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from config import DB_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    url=DB_URL,
    echo=False
)

print("POOL: ", engine.pool.status())

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
