"""
Date utility functions for API endpoints
"""
from datetime import datetime, timedelta


def parse_date_filters(request):
    """
    Extract and parse date filters from Flask request
    
    Args:
        request: Flask request object
        
    Returns:
        dict: {'start_date': datetime or None, 'end_date': datetime or None}
    """
    start_date_str = request.args.get('start_date') or request.args.get('startDate')
    end_date_str = request.args.get('end_date') or request.args.get('endDate')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
    
    return {
        'start_date': start_date,
        'end_date': end_date
    }


def get_date_range(filter_type):
    """
    Get date range based on filter type
    
    Args:
        filter_type: 'today', 'this_month', 'last_30_days', or 'custom'
        
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if filter_type == 'today':
        return today_start, now
    elif filter_type == 'this_month':
        start = today_start.replace(day=1)
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month - timedelta(days=next_month.day)
        return start, end.replace(hour=23, minute=59, second=59)
    elif filter_type == 'last_30_days':
        return now - timedelta(days=30), now
    else:
        # Default to this month
        start = today_start.replace(day=1)
        return start, now
