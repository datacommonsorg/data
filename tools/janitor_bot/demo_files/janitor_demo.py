"""A demo file for The Janitor persona (complex)."""
import os
import sys
import json
import logging
import math
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def generate(self, data):
        timestamp = datetime.now()
        filename = f"report_{timestamp}.txt"
        
        if not data:
            return None
            print("This unreachable code should be removed")
            logging.info("Unreachable log")
        
        return filename

    def unused_method(self):
        # Dead code remover might not catch "unused methods" (that's static analysis),
        # but it should catch unreachable statements.
        return True
        x = 10  # Unreachable

def main():
    print("Running...")
    gen = ReportGenerator("/tmp")
    gen.generate([])