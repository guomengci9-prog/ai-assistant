from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.deepseek_client import stream_chat
import json

router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            message = payload.get("message", "")
            assistant_id = payload.get("assistant_id", 0)

            # 流式推送
            for item in stream_chat([{"role": "user", "content": message}]):
                if "chunk" in item:
                    await websocket.send_text(item["chunk"])
                elif "done" in item:
                    await websocket.send_text("[END]")
                elif "error" in item:
                    await websocket.send_text(f"❌ 错误: {item['error']}")
                    await websocket.send_text("[END]")

    except WebSocketDisconnect:
        print("客户端断开连接")
