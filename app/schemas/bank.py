from pydantic import BaseModel, Field
from typing import Literal, Dict, Optional, Any


class TransferRequest(BaseModel):
    receiver_username: str
    amount: float = Field(..., gt=0)


class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0)


class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0)
    method: Optional[Literal["bank_transfer", "check", "atm"]] = None
    details: Optional[Dict[str, Any]] = None


class ChequeStatusUpdate(BaseModel):
    status: Literal["approved", "rejected"] 