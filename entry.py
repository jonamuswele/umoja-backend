import sys
import os
import glob

# Ensure site-packages from .venv are appended to sys.path after built-in Pyodide packages.
# This allows Pyodide to use its precompiled WebAssembly packages (like pydantic-core)
# while still loading pure Python packages (like fastapi) from .venv.
base_dir = os.path.dirname(os.path.abspath(__file__))
for sp in glob.glob(os.path.join(base_dir, ".venv", "**", "site-packages"), recursive=True):
    if sp not in sys.path:
        sys.path.append(sp)

import asgi
from main import app
from workers import WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)
