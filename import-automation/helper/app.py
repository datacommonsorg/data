# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fastapi import FastAPI
from routes import imports, events, database
from utils.logging import log_requests
from __init__ import __version__

app = FastAPI(
    title="Data Commons Import Helper",
    description="FastAPI service providing helper routines for Import Automation workflow.",
    version=__version__
)

# Register the centralized HTTP request/response logging middleware
app.middleware("http")(log_requests)

# Include APIRouters
app.include_router(events.router)
app.include_router(imports.router)
app.include_router(database.router)
