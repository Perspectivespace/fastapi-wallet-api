import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(setup_db) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_wallet_not_found(client: AsyncClient):
    wallet_id = uuid.uuid4()
    response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deposit_creates_wallet_and_updates_balance(client: AsyncClient):
    wallet_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(wallet_id)
    assert data["balance"] == 1000

    # Get balance
    response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["balance"] == 1000


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(client: AsyncClient):
    wallet_id = uuid.uuid4()
    # First deposit
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 500},
    )
    # Withdraw more
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 600},
    )
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


@pytest.mark.asyncio
async def test_withdraw_success(client: AsyncClient):
    wallet_id = uuid.uuid4()
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 300},
    )
    assert response.status_code == 200
    assert response.json()["balance"] == 700


@pytest.mark.asyncio
async def test_invalid_amount(client: AsyncClient):
    wallet_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": -100},
    )
    assert response.status_code == 422
