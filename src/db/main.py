from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config import Config
from src.db.models import Book


# Convert sync database URL to async-compatible URL
DATABASE_URL = Config.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create the async engine
engine: AsyncEngine = create_async_engine(
    url=DATABASE_URL,
    echo=True
)

# Create the async sessionmaker
async_session = sessionmaker(
    bind=engine,  
    class_=AsyncSession,
    expire_on_commit=False
)

# Initialize database schema
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependency to provide an async session
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
