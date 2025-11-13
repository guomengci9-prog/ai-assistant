from fastapi import APIRouter

from app.routers.chat import websocket_chat as chat_websocket_chat

router = APIRouter()
router.add_api_websocket_route("/ws/chat/{assistant_id}", chat_websocket_chat)
