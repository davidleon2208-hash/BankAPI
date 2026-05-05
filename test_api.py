import requests

BASE_URL = "http://127.0.0.1:8000"

# Register a user
response = requests.post(f"{BASE_URL}/register", json={"username": "testuser", "password": "testpass"})
print("Register:", response.status_code, response.text)

# Login
response = requests.post(f"{BASE_URL}/token", data={"username": "testuser", "password": "testpass"})
print("Login:", response.status_code, response.text)
if response.status_code == 200:
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create deposit
    response = requests.post(f"{BASE_URL}/transactions", json={"type": "deposit", "amount": 100.0}, headers=headers)
    print("Deposit:", response.status_code, response.text)

    # Create withdraw
    response = requests.post(f"{BASE_URL}/transactions", json={"type": "withdraw", "amount": 50.0}, headers=headers)
    print("Withdraw:", response.status_code, response.text)

    # Get statement
    response = requests.get(f"{BASE_URL}/accounts/statement", headers=headers)
    print("Statement:", response.status_code, response.text)