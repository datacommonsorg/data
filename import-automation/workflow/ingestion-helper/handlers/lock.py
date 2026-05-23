import logging
from .utils import validate_params

def handle_acquire_lock(spanner, request_json):
    """Attempts to acquire the global lock for ingestion."""
    validation_error = validate_params(request_json, ['workflowId', 'timeout'])
    if validation_error:
        return (validation_error, 400)
    
    workflow = request_json['workflowId']
    timeout = request_json['timeout']
    status = spanner.acquire_lock(workflow, timeout)
    if not status:
        return ('Failed to acquire lock', 500)
    return ('OK', 200)

def handle_release_lock(spanner, request_json):
    """Releases the global ingestion lock."""
    validation_error = validate_params(request_json, ['workflowId'])
    if validation_error:
        return (validation_error, 400)
        
    workflow = request_json['workflowId']
    status = spanner.release_lock(workflow)
    if not status:
        return ('Failed to release lock', 500)
    return ('OK', 200)
