import requests

BASE_URL = "http://localhost:5000/api"

print("=== Deleting Test Ledger Entries ===\n")

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

# Get all ledger entries
print("\n2. Fetching ledger entries...")
resp = requests.get(f"{BASE_URL}/accounting/ledger", 
                   headers={"Authorization": f"Bearer {token}"})

if resp.status_code == 200:
    ledger = resp.json()
    
    # Find test entries (description contains "Agent Payment - Test Entry")
    test_entries = [e for e in ledger if 'Test Entry' in e.get('description', '')]
    
    print(f"   Found {len(test_entries)} test entries to delete:")
    for e in test_entries:
        entry_id = e['_id'].get('$oid') if isinstance(e['_id'], dict) else e['_id']
        print(f"   - Rs. {e['amount']} - {e['description']} (ID: {entry_id})")
    
    if len(test_entries) == 0:
        print("   No test entries found!")
        exit(0)
    
    # Confirm deletion
    print(f"\n3. Deleting {len(test_entries)} test entries...")
    deleted_count = 0
    
    for e in test_entries:
        entry_id = e['_id'].get('$oid') if isinstance(e['_id'], dict) else e['_id']
        
        # Delete the entry
        resp = requests.delete(
            f"{BASE_URL}/accounting/ledger/{entry_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if resp.status_code == 200:
            deleted_count += 1
            print(f"   ✓ Deleted entry: Rs. {e['amount']} - {e['description']}")
        else:
            print(f"   ❌ Failed to delete entry {entry_id}: {resp.status_code}")
    
    print(f"\n✅ Successfully deleted {deleted_count} test entries!")
    
    # Show updated totals
    print("\n4. Checking updated Financial Summary...")
    resp = requests.get(f"{BASE_URL}/agency/financial-summary", 
                       headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code == 200:
        summary = resp.json()
        print(f"   Total Credit: Rs. {summary['total_credit']:,.2f}")
        print(f"   Total Debit: Rs. {summary['total_debit']:,.2f}")
        print(f"   Net Balance: Rs. {summary['net_balance']:,.2f}")

print("\n=== Deletion Complete ===")
