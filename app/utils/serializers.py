import json

from datetime import datetime

def _convert_mongo_types(data):
    """Recursively convert MongoDB ObjectId objects to strings and Date objects to ISO strings"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == '$oid':
                # This is an ObjectId, return just the string value
                return value
            elif key == '$date':
                # This is a Date, value is usually timestamp in milliseconds
                if isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value / 1000.0).isoformat()
                return value
            elif isinstance(value, dict) and '$oid' in value:
                # This field contains an ObjectId
                result[key] = value['$oid']
            elif isinstance(value, dict) and '$date' in value:
                # This field contains a Date
                date_val = value['$date']
                if isinstance(date_val, (int, float)):
                    result[key] = datetime.fromtimestamp(date_val / 1000.0).isoformat()
                else:
                    result[key] = date_val
            elif isinstance(value, dict) and '$numberDecimal' in value:
                # Handle Decimal serialization from MongoEngine
                result[key] = float(value['$numberDecimal'])
            elif isinstance(value, (dict, list)):
                # Recursively process nested structures
                result[key] = _convert_mongo_types(value)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [_convert_mongo_types(item) for item in data]
    else:
        return data

def mongo_to_dict(obj):
    """
    Converts a MongoEngine Document or QuerySet to a dict/list
    compatible with jsonify (by going through to_json()).
    """
    if obj is None:
        return None
        
    # QuerySet or Document
    if hasattr(obj, 'to_json'):
        data = json.loads(obj.to_json())
        result = _convert_mongo_types(data)
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and '_id' in item:
                    item['id'] = item['_id']
        elif isinstance(result, dict) and '_id' in result:
            result['id'] = result['_id']
        return result
    
    # List of documents
    if isinstance(obj, list):
        data_list = [mongo_to_dict(item) for item in obj]
        # Ensure id is injected for each item if missing
        if isinstance(data_list, list): # Should always be true
            for item in data_list:
                if isinstance(item, dict) and '_id' in item and 'id' not in item:
                    item['id'] = item['_id']
        return data_list
        
    return obj
