"""
Financial calculation services
Shared logic for calculating credits, debits, and balances
"""
from models.ledger import LedgerEntry
from models.agent import Agent
from models.miscellaneous_expense import MiscellaneousExpense
from bson import ObjectId


class FinancialService:
    @staticmethod
    def calculate_total_debit(agency_id, start_date=None, end_date=None):
        """
        Calculate total debit from multiple sources:
        1. Ledger entries with type='Debit'
        2. Agent payments
        3. Miscellaneous expenses
        
        Args:
            agency_id: Agency ObjectId or string
            start_date: Optional datetime filter
            end_date: Optional datetime filter
            
        Returns:
            dict with breakdown: {
                'ledger_debit': float,
                'agent_payments': float,
                'misc_expenses': float,
                'total_debit': float
            }
        """
        # Ensure ObjectId
        if isinstance(agency_id, str):
            agency_id = ObjectId(agency_id)
        
        # 1. Ledger debits
        ledger_filters = {'agencyId': agency_id, 'type': 'Debit'}
        if start_date:
            ledger_filters['date__gte'] = start_date
        if end_date:
            ledger_filters['date__lte'] = end_date
            
        debit_entries = LedgerEntry.objects(**ledger_filters)
        ledger_debit = sum(float(entry.amount) for entry in debit_entries)
        
        # 2. Agent payments
        agent_filters = {'created_by_agency': agency_id}
        if start_date:
            agent_filters['created_at__gte'] = start_date
        if end_date:
            agent_filters['created_at__lte'] = end_date
            
        agents = Agent.objects(**agent_filters)
        agent_payments = sum(float(agent.amount_paid or 0) for agent in agents)
        
        # 3. Miscellaneous expenses
        misc_filters = {'agencyId': agency_id}
        if start_date:
            misc_filters['expense_date__gte'] = start_date
        if end_date:
            misc_filters['expense_date__lte'] = end_date
            
        misc_expenses = MiscellaneousExpense.objects(**misc_filters)
        misc_debit = sum(float(expense.amount) for expense in misc_expenses)
        
        # Total
        total_debit = ledger_debit + agent_payments + misc_debit
        
        return {
            'ledger_debit': ledger_debit,
            'agent_payments': agent_payments,
            'misc_expenses': misc_debit,
            'total_debit': total_debit
        }
    
    @staticmethod
    def calculate_total_credit(agency_id, start_date=None, end_date=None):
        """
        Calculate total credit from ledger entries
        
        Args:
            agency_id: Agency ObjectId or string
            start_date: Optional datetime filter
            end_date: Optional datetime filter
            
        Returns:
            float: Total credit amount
        """
        # Ensure ObjectId
        if isinstance(agency_id, str):
            agency_id = ObjectId(agency_id)
        
        filters = {'agencyId': agency_id, 'type': 'Credit'}
        if start_date:
            filters['date__gte'] = start_date
        if end_date:
            filters['date__lte'] = end_date
            
        credit_entries = LedgerEntry.objects(**filters)
        return sum(float(entry.amount) for entry in credit_entries)
