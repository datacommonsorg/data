"""Demo file for The Typer persona."""

from typing import List, Dict, Any

def process_names(names: List[str]) -> List[str]:
    """Processes a list of names."""
    return [n.upper() for n in names]

def add_numbers(x: int, y: int) -> int:
    """Adds two numbers."""
    return x + y

def get_user_info(user_id: int) -> Dict[str, Any]:
    """Gets user info dict."""
    return {"id": user_id, "name": "Unknown"}