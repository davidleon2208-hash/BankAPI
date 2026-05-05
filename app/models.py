from datetime import datetime
from typing import List

class User:
    def __init__(self, id: int, username: str, password_hash: str):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.accounts: List[Account] = []

class Account:
    def __init__(self, id: int, user_id: int, balance: float = 0.0):
        self.id = id
        self.user_id = user_id
        self.balance = balance
        self.transactions: List[Transaction] = []

class Transaction:
    def __init__(self, id: int, account_id: int, type: str, amount: float):
        self.id = id
        self.account_id = account_id
        self.type = type
        self.amount = amount
        self.timestamp = datetime.utcnow()

# In-memory storage
users_db: List[User] = []
accounts_db: List[Account] = []
transactions_db: List[Transaction] = []

# Counters for IDs
user_id_counter = 1
account_id_counter = 1
transaction_id_counter = 1