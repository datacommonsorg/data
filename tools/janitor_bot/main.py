# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Entry point for Janitor Bot."""

import argparse
from .librarian import TheLibrarian
from .cleaners import TheImportCleaner, TheDeadCodeRemover
from .typer import TheTyper

# Configuration
PROJECT_ID = "stuniki-runtimes-dev"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-pro"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Janitor Bot: Code Health Automation")
    parser.add_argument(
        "--mode",
        type=str,
        default="librarian",
        choices=["librarian", "import_cleaner", "dead_code_remover", "typer"],
        help="Bot persona to run",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="tools/statvar_importer",
        help="Directory or file to scan",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes to files"
    )
    parser.add_argument(
        "--project", type=str, default=PROJECT_ID, help="GCP Project ID"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of functions per file (Librarian only)"
    )

    args = parser.parse_args()

    if args.mode == "librarian":
        bot = TheLibrarian(args.project, LOCATION, MODEL_NAME)
        bot.run(args.target, args.apply, args.limit)
    elif args.mode == "import_cleaner":
        bot = TheImportCleaner(args.project, LOCATION, MODEL_NAME)
        bot.run(args.target, args.apply, args.limit)
    elif args.mode == "dead_code_remover":
        bot = TheDeadCodeRemover(args.project, LOCATION, MODEL_NAME)
        bot.run(args.target, args.apply, args.limit)
    elif args.mode == "typer":
        bot = TheTyper(args.project, LOCATION, MODEL_NAME)
        bot.run(args.target, args.apply, args.limit)
