from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import (
    admin_assistants,
    admin_docs,
    admin_users,
    assistants,
    auth,
    chat,
    ws_chat,
)

app = FastAPI(title="AI Assistant Backend")
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(assistants.router, prefix="/api")
app.include_router(admin_assistants.router, prefix="/api")
app.include_router(admin_docs.router, prefix="/api")
app.include_router(admin_users.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ws_chat.router)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/")
def root():
    return {"message": "Backend running successfully"}
