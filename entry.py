import glob
import os
import sys

# Ensure all site-packages directories under .venv are added to sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
for sp in glob.glob(
    os.path.join(base_dir, ".venv", "**", "site-packages"), recursive=True
):
    if sp not in sys.path:
        sys.path.insert(0, sp)

import asgi
from main import app
from workers import WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)
