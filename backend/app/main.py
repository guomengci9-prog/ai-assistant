from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, assistants, chat, ws_chat

app = FastAPI(title="AI Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(assistants.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ws_chat.router)  # WebSocket流式接口

@app.get("/")
def root():
    return {"message": "Backend running successfully ✅"}
