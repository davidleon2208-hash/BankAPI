from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TransactionCreate(BaseModel):
    type: str = Field(..., pattern="^(deposit|withdraw)$")
    amount: float = Field(..., gt=0)

class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: float
    timestamp: datetime

class AccountResponse(BaseModel):
    id: int
    balance: float
    transactions: List[TransactionResponse]