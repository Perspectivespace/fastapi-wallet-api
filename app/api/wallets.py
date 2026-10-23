from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Wallet
from app.schemas import OperationType, WalletOperation, WalletResponse

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.get("/{wallet_uuid}", response_model=WalletResponse)
async def get_wallet(
    wallet_uuid: UUID,
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_uuid))
    wallet = result.scalar_one_or_none()
    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )
    return WalletResponse.model_validate(wallet)


@router.post("/{wallet_uuid}/operation", response_model=WalletResponse)
async def wallet_operation(
    wallet_uuid: UUID,
    operation: WalletOperation,
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    # Use SELECT FOR UPDATE to lock the row for concurrency safety
    result = await db.execute(
        select(Wallet).where(Wallet.id == wallet_uuid).with_for_update()
    )
    wallet = result.scalar_one_or_none()

    if wallet is None:
        if operation.operation_type == OperationType.WITHDRAW:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )
        # Create wallet on first deposit
        wallet = Wallet(id=wallet_uuid, balance=0)
        db.add(wallet)
        # Flush to get it into the session before update
        await db.flush()

    if operation.operation_type == OperationType.DEPOSIT:
        wallet.balance += operation.amount
    elif operation.operation_type == OperationType.WITHDRAW:
        if wallet.balance < operation.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient funds",
            )
        wallet.balance -= operation.amount

    await db.flush()
    await db.refresh(wallet)
    return WalletResponse.model_validate(wallet)
