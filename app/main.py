from fastapi import FastAPI, Depends, HTTPException, status, Form
from . import schemas, auth
from .models import users_db, accounts_db, transactions_db, user_id_counter, account_id_counter, transaction_id_counter, User, Account, Transaction
from .auth import get_current_user, get_password_hash, verify_password, create_access_token
from datetime import timedelta

app = FastAPI(title="Banking API", description="Asynchronous Banking API with JWT Authentication")

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate):
    try:
        if any(u.username == user.username for u in users_db):
            raise HTTPException(status_code=400, detail="Username already registered")
        global user_id_counter
        db_user = User(id=user_id_counter, username=user.username, password_hash=get_password_hash(user.password[:72]))
        users_db.append(db_user)
        user_id_counter += 1
        # Create an account for the user
        global account_id_counter
        account = Account(id=account_id_counter, user_id=db_user.id, balance=0.0)
        accounts_db.append(account)
        db_user.accounts.append(account)
        account_id_counter += 1
        return schemas.UserResponse(id=db_user.id, username=db_user.username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/token", response_model=schemas.Token)
def login(username: str = Form(...), password: str = Form(...)):
    db_user = next((u for u in users_db if u.username == username), None)
    if not db_user or not verify_password(password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/transactions", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, current_user: User = Depends(get_current_user)):
    account = next((a for a in accounts_db if a.user_id == current_user.id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if transaction.type == "withdraw" and account.balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    global transaction_id_counter
    db_transaction = Transaction(id=transaction_id_counter, account_id=account.id, type=transaction.type, amount=transaction.amount)
    transactions_db.append(db_transaction)
    account.transactions.append(db_transaction)
    if transaction.type == "deposit":
        account.balance += transaction.amount
    elif transaction.type == "withdraw":
        account.balance -= transaction.amount
    transaction_id_counter += 1
    return schemas.TransactionResponse(id=db_transaction.id, type=db_transaction.type, amount=db_transaction.amount, timestamp=db_transaction.timestamp)

@app.get("/accounts/statement", response_model=schemas.AccountResponse)
def get_statement(current_user: User = Depends(get_current_user)):
    account = next((a for a in accounts_db if a.user_id == current_user.id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    transactions = [schemas.TransactionResponse(id=t.id, type=t.type, amount=t.amount, timestamp=t.timestamp) for t in account.transactions]
    return schemas.AccountResponse(id=account.id, balance=account.balance, transactions=transactions)