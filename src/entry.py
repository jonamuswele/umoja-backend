import asgi
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from workers import WorkerEntrypoint 

app = FastAPI()

#Enable CORS for frontend
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("api/health")
async def health():
  return {"status":"online"}

@app.get("/api/users")
async def get_users(req: Request):
  env = req.scope["env"]
  result = await env.DB.prepare("SELECT * FROM users").all()
  return {"users": result.results}

class Default(WorkerEntrypoint):
  async def fetch(self, request):
    return await asgi.fetch(app, request, self.env)
