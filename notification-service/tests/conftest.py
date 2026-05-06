import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.core.dependencies import get_current_user_token, TokenData

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    async def override_get_current_user_token():
        return TokenData(user_id="test-user", role="member")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_token] = override_get_current_user_token
    async with AsyncClient(transport=ASGITransport(app=app, lifespan="off"), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
