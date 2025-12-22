from flask import jsonify

def error_response(message, code="UNKNOWN_ERROR", status=400, details=None):
    response = {
        'error': message,
        'code': code
    }
    if details:
        response['details'] = details
    return jsonify(response), status

# Common Errors
def validation_error(details):
    return error_response("Validation Failed", "VALIDATION_ERROR", 400, details)

def not_found_error(message="Resource not found"):
    return error_response(message, "NOT_FOUND", 404)

def unauthorized_error(message="Unauthorized"):
    return error_response(message, "UNAUTHORIZED", 401)
