import os
from pymongo import MongoClient
import ssl

def fix_indexes_raw():
    uri = "mongodb+srv://shamsullahkhan94:0tG6zoyY492tcr5h@cluster0.dewflpp.mongodb.net/bannu_pilot?appName=Cluster0"
    print("Connecting to MongoDB...")
    client = MongoClient(uri)
    db = client.get_database() # default db
    
    print(f"Connected to {db.name}")
    
    coll = db.customers
    try:
        print("Dropping index 'agencyId_1_phone_1'...")
        coll.drop_index("agencyId_1_phone_1")
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        
    # Also check if other model indexes are corrupted
    try:
        print("Dropping index 'agencyId_1_passportNumber_1' just in case...")
        coll.drop_index("agencyId_1_passportNumber_1")
        print("Success!")
    except Exception as e:
        pass

if __name__ == "__main__":
    fix_indexes_raw()
