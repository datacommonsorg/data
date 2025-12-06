"""A demo file for The Janitor persona."""
import os
import sys
import json
import logging
from typing import List, Dict

def hello_world():
    """Prints hello world."""
    print("Hello World")

def calculation(a, b):
    """Does a calculation but has dead code."""
    result = a + b
    return result
    print("This is dead code")
    unreachable_var = 10
