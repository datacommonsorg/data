def validate_params(request_json, required_params):
    """Validates that required parameters are present in the request JSON."""
    for param in required_params:
        if param not in request_json:
            return f"'{param}' parameter is missing"
    return None
