import requests
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

print("=== Creating Rs. 200 Agent Payment Entry ===\n")

# Login as shams
print("1. Logging in as shams@gmail.com...")
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "shams@gmail.com",
    "password": "shams"
})

if resp.status_code != 200:
    print(f"   ❌ Login failed")
    exit(1)

token = resp.json()['accessToken']
print("   ✓ Login successful")

# Create ledger entry
print("\n2. Creating Rs. 200 Debit entry (Agent Payment)...")
resp = requests.post(
    f"{BASE_URL}/accounting/ledger",
    json={
        "type": "Debit",
        "amount": 200,
        "description": "Agent Payment - Test Entry",
        "date": datetime.now().strftime('%Y-%m-%d')  # Use YYYY-MM-DD format
    },
    headers={"Authorization": f"Bearer {token}"}
)

if resp.status_code in [200, 201]:
    print("   ✓ Ledger entry created successfully")
else:
    print(f"   ❌ Failed to create entry: {resp.status_code}")
    print(f"   Response: {resp.text}")
    exit(1)

# Verify with financial summary
print("\n3. Checking Financial Summary...")

# All Time
resp = requests.get(f"{BASE_URL}/agency/financial-summary", 
                   headers={"Authorization": f"Bearer {token}"})
if resp.status_code == 200:
    data = resp.json()
    print(f"   All Time:")
    print(f"   - Credit: Rs. {data['total_credit']:,.2f}")
    print(f"   - Debit: Rs. {data['total_debit']:,.2f}")
    print(f"   - Balance: Rs. {data['net_balance']:,.2f}")

# This Month
now = datetime.now()
first_day = datetime(now.year, now.month, 1)
resp = requests.get(
    f"{BASE_URL}/agency/financial-summary",
    params={
        'start_date': first_day.isoformat(),
        'end_date': now.isoformat()
    },
    headers={"Authorization": f"Bearer {token}"}
)

if resp.status_code == 200:
    data = resp.json()
    print(f"\n   This Month:")
    print(f"   - Credit: Rs. {data['total_credit']:,.2f}")
    print(f"   - Debit: Rs. {data['total_debit']:,.2f}")
    print(f"   - Balance: Rs. {data['net_balance']:,.2f}")

print("\n✅ Entry created! Refresh your dashboard to see the updated widget.")
