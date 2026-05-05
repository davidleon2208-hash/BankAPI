import json
from pathlib import Path
from datetime import datetime
import aiofiles

STORAGE_FILE = Path(__file__).resolve().parent.parent / "storage.json"
DEFAULT_DATA = {
    "users": [],
    "accounts": [],
    "transactions": [],
    "counters": {"user": 1, "account": 1, "transaction": 1},
}

async def init_storage():
    if not STORAGE_FILE.exists():
        await write_data(DEFAULT_DATA)

async def read_data():
    if not STORAGE_FILE.exists():
        await init_storage()
    async with aiofiles.open(STORAGE_FILE, mode="r", encoding="utf-8") as file:
        content = await file.read()
    if not content:
        return DEFAULT_DATA.copy()
    return json.loads(content)

async def write_data(data):
    async with aiofiles.open(STORAGE_FILE, mode="w", encoding="utf-8") as file:
        await file.write(json.dumps(data, default=str, indent=2))

async def get_user_by_username(username: str):
    data = await read_data()
    return next((user for user in data["users"] if user["username"] == username), None)

async def get_user_by_id(user_id: int):
    data = await read_data()
    return next((user for user in data["users"] if user["id"] == user_id), None)

async def create_user(username: str, password_hash: str):
    data = await read_data()
    user = {
        "id": data["counters"]["user"],
        "username": username,
        "password_hash": password_hash,
    }
    data["users"].append(user)
    data["counters"]["user"] += 1
    await write_data(data)
    return user

async def create_account(user_id: int):
    data = await read_data()
    account = {
        "id": data["counters"]["account"],
        "user_id": user_id,
        "balance": 0.0,
    }
    data["accounts"].append(account)
    data["counters"]["account"] += 1
    await write_data(data)
    return account

async def get_account_by_user(user_id: int):
    data = await read_data()
    return next((account for account in data["accounts"] if account["user_id"] == user_id), None)

async def update_account_balance(account_id: int, new_balance: float):
    data = await read_data()
    account = next((acc for acc in data["accounts"] if acc["id"] == account_id), None)
    if not account:
        return None
    account["balance"] = new_balance
    await write_data(data)
    return account

async def create_transaction(account_id: int, type: str, amount: float):
    data = await read_data()
    account = next((acc for acc in data["accounts"] if acc["id"] == account_id), None)
    if not account:
        return None
    transaction = {
        "id": data["counters"]["transaction"],
        "account_id": account_id,
        "type": type,
        "amount": amount,
        "timestamp": datetime.utcnow().isoformat(),
    }
    data["transactions"].append(transaction)
    data["counters"]["transaction"] += 1
    if type == "deposit":
        account["balance"] += amount
    elif type == "withdraw":
        account["balance"] -= amount
    await write_data(data)
    return transaction

async def get_transactions_by_account(account_id: int):
    data = await read_data()
    return [t for t in data["transactions"] if t["account_id"] == account_id]
