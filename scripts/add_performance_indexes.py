"""
Script to add performance indexes to MongoDB collections
Run this once to optimize query performance
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mongoengine import connect
from app.models.ledger import LedgerEntry
from models.booking import Booking
from models.ticket_booking import TicketBooking
from models.visa_booking import VisaBooking
from models.miscellaneous_expense import MiscellaneousExpense
from models.agent import Agent
from models.customer import Customer
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGODB_URI')
connect(host=mongo_uri)

print("Adding performance indexes...")

# Get database connection
db = LedgerEntry._get_db()

# LedgerEntry indexes
print("Adding LedgerEntry indexes...")
db.ledger_entries.create_index([('agencyId', 1), ('date', -1)])
db.ledger_entries.create_index([('agencyId', 1), ('type', 1), ('date', -1)])

# Booking indexes  
print("Adding Booking indexes...")
db.bookings.create_index([('agencyId', 1), ('createdAt', -1)])
db.bookings.create_index([('agencyId', 1), ('status', 1)])
db.bookings.create_index([('agencyId', 1), ('balanceDue', 1)])
db.bookings.create_index([('customerId', 1)])

# TicketBooking indexes
print("Adding TicketBooking indexes...")
db.ticketbookings.create_index([('sellerAgencyId', 1), ('created_at', -1)])
db.ticketbookings.create_index([('buyerAgencyId', 1), ('created_at', -1)])
db.ticketbookings.create_index([('status', 1)])

# VisaBooking indexes
print("Adding VisaBooking indexes...")
db.visabookings.create_index([('seller_agency_id', 1), ('created_at', -1)])
db.visabookings.create_index([('buyer_agency_id', 1), ('created_at', -1)])
db.visabookings.create_index([('status', 1)])

# MiscellaneousExpense indexes
print("Adding MiscellaneousExpense indexes...")
db.miscellaneous_expenses.create_index([('agencyId', 1), ('expense_date', -1)])

# Agent indexes
print("Adding Agent indexes...")
db.agents.create_index([('created_by_agency', 1), ('created_at', -1)])

# Customer indexes
print("Adding Customer indexes...")
db.customers.create_index([('agencyId', 1)])
db.customers.create_index([('email', 1)])

print("✅ All indexes created successfully!")
print("\nTo verify indexes, run:")
print("  db.ledger_entries.getIndexes()")
