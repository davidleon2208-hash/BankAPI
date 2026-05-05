from fastapi import FastAPI, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from . import schemas
from .models import User, Account, Transaction, create_tables
from .database import get_db
from .auth import get_current_user, get_password_hash, verify_password, create_access_token

app = FastAPI(title="Banking API", description="Asynchronous Banking API with JWT Authentication")

@app.on_event("startup")
async def startup():
    await create_tables()

@app.post("/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    password_hash = await get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=password_hash)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    account = Account(user_id=db_user.id, balance=0.0)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return schemas.UserResponse(id=db_user.id, username=db_user.username)

@app.post("/token", response_model=schemas.Token)
async def login(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    db_user = result.scalars().first()
    if not db_user or not await verify_password(password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/transactions", response_model=schemas.TransactionResponse)
async def create_transaction(transaction: schemas.TransactionCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.user_id == current_user.id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if transaction.type == "withdraw" and account.balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if transaction.type == "deposit":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount
    db_transaction = Transaction(account_id=account.id, type=transaction.type, amount=transaction.amount)
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction

@app.get("/accounts/statement", response_model=schemas.AccountResponse)
async def get_statement(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.user_id == current_user.id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    transactions_result = await db.execute(select(Transaction).where(Transaction.account_id == account.id).order_by(Transaction.timestamp))
    transactions = transactions_result.scalars().all()
    return schemas.AccountResponse(id=account.id, balance=account.balance, transactions=transactions)