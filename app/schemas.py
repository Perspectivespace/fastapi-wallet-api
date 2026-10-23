from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperation(BaseModel):
    operation_type: OperationType
    amount: int = Field(..., gt=0, description="Amount must be positive integer")

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class WalletResponse(BaseModel):
    id: UUID
    balance: int

    model_config = {"from_attributes": True}
