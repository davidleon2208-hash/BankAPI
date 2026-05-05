from fastapi import FastAPI, Depends, HTTPException, Form
from . import schemas, auth, storage
from datetime import timedelta

app = FastAPI(title="Banking API", description="Asynchronous Banking API with JWT Authentication")

@app.on_event("startup")
async def startup():
    await storage.init_storage()

@app.post("/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate):
    if await storage.get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    password_hash = await auth.get_password_hash(user.password)
    db_user = await storage.create_user(user.username, password_hash)
    await storage.create_account(db_user["id"])
    return schemas.UserResponse(id=db_user["id"], username=db_user["username"])

@app.post("/token", response_model=schemas.Token)
async def login(username: str = Form(...), password: str = Form(...)):
    db_user = await storage.get_user_by_username(username)
    if not db_user or not await auth.verify_password(password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": db_user["username"]}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/transactions", response_model=schemas.TransactionResponse)
async def create_transaction(transaction: schemas.TransactionCreate, current_user: dict = Depends(auth.get_current_user)):
    account = await storage.get_account_by_user(current_user["id"])
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if transaction.type == "withdraw" and account["balance"] < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    db_transaction = await storage.create_transaction(account["id"], transaction.type, transaction.amount)
    return schemas.TransactionResponse(id=db_transaction["id"], type=db_transaction["type"], amount=db_transaction["amount"], timestamp=db_transaction["timestamp"])

@app.get("/accounts/statement", response_model=schemas.AccountResponse)
async def get_statement(current_user: dict = Depends(auth.get_current_user)):
    account = await storage.get_account_by_user(current_user["id"])
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    transactions = await storage.get_transactions_by_account(account["id"])
    transaction_models = [schemas.TransactionResponse(id=t["id"], type=t["type"], amount=t["amount"], timestamp=t["timestamp"]) for t in transactions]
    return schemas.AccountResponse(id=account["id"], balance=account["balance"], transactions=transaction_models)