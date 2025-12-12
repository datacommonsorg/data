"""Demo file for The Typer persona."""

class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_display_name(self):
        return f"{self.name} ({self.age})"

    @classmethod
    def create_guest(cls):
        return cls("Guest", 0)

def find_users(query, limit=10):
    # Returns a list of User objects
    results = []
    for i in range(limit):
        results.append(User(f"User{i}", 20 + i))
    return results

def process_config(config):
    # config is a dict with string keys and any values
    if config.get("debug"):
        print("Debug mode")
    return config.get("retries", 3)