"""Demo file for The Typer persona."""

def process_names(names):
    """Processes a list of names."""
    return [n.upper() for n in names]

def add_numbers(x, y):
    """Adds two numbers."""
    return x + y

def get_user_info(user_id):
    """Gets user info dict."""
    return {"id": user_id, "name": "Unknown"}
