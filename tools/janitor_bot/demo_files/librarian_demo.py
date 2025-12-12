"""Demo file for The Librarian persona (Complex)."""
import asyncio
import functools

def log_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

class AsyncProcessor:
    def __init__(self, concurrency=5):
        self.concurrency = concurrency
    
    @log_execution
    async def fetch_data(self, urls):
        # Fetches data from multiple URLs
        results = []
        for url in urls:
            results.append(f"Data from {url}")
        return results

    @staticmethod
    def normalize(text):
        return text.lower().strip()

    def complex_logic(self, items):
        def _helper(x):
            return x * 2
        
        return [_helper(i) for i in items]
