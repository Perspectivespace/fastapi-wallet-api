# Wallet API

REST API for managing user wallets with deposit and withdraw operations.

## Features

- Async FastAPI
- PostgreSQL with async SQLAlchemy
- Alembic migrations
- Concurrency-safe balance updates using `SELECT FOR UPDATE`
- Docker & docker-compose
- Tests with pytest

## Quick Start

```bash
docker-compose up --build
```

The API will be available at http://localhost:8000

- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Endpoints

### Get wallet balance

```
GET /api/v1/wallets/{wallet_uuid}
```

Returns:

```json
{
  "id": "uuid",
  "balance": 1000
}
```

### Perform operation

```
POST /api/v1/wallets/{wallet_uuid}/operation
Content-Type: application/json

{
  "operation_type": "DEPOSIT" | "WITHDRAW",
  "amount": 1000
}
```

- On first DEPOSIT a new wallet is created.
- WITHDRAW fails with 404 if wallet does not exist, or 400 if insufficient funds.

## Development

Copy `.env.example` to `.env` if needed.

### Running tests

Tests use SQLite for isolation. Install dependencies and run:

```bash
pip install -r requirements.txt
pytest
```

## Concurrency

Balance updates are protected by database row-level locks (`SELECT ... FOR UPDATE`) inside a transaction, ensuring correct behavior under concurrent requests to the same wallet.

## License

MIT
