from workers import WorkerEntrypoint
from main import app

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        from workers.asgi import fetch
        return await fetch(app, request, self.env)
