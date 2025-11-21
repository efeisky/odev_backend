from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import authentication, project, tasks, general

app = FastAPI(title="My Python Server")

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authentication.router)
app.include_router(project.router)
app.include_router(tasks.router)
app.include_router(general.router)
