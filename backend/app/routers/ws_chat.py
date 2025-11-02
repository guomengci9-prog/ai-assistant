from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.deepseek_client import stream_chat
import asyncio
import json

router = APIRouter()

@router.websocket("/ws/chat/{assistant_id}")
async def websocket_chat(websocket: WebSocket, assistant_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                message = payload.get("message", "").strip()
            except Exception:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "消息格式错误"
                }))
                continue

            if not message:
                continue

            # 通过线程逐块流式发送
            def run_stream():
                for chunk in stream_chat([{"role": "user", "content": message}]):
                    if "chunk" in chunk:
                        content = chunk["chunk"]
                        step = 25  # 每次发送25字符，保证流式效果
                        for i in range(0, len(content), step):
                            asyncio.run(websocket.send_text(json.dumps({
                                "type": "chunk",
                                "content": content[i:i+step]
                            })))
                    elif "error" in chunk:
                        asyncio.run(websocket.send_text(json.dumps({
                            "type": "error",
                            "content": chunk["error"]
                        })))
                        break
                    elif "done" in chunk:
                        break

            await asyncio.to_thread(run_stream)

            # 发送结束标识
            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        print(f"WebSocket {assistant_id} 连接断开")
