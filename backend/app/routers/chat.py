from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
from app.core.deepseek_client import chat_completion, stream_chat

router = APIRouter()

# 内存模拟历史记录（改为每个助手单独字典，支持异步安全）
chat_history_db = {}
chat_locks = {}  # 每个助手一个锁，避免并发写入冲突

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    success: bool
    reply: str

def get_lock(assistant_id: int):
    if assistant_id not in chat_locks:
        chat_locks[assistant_id] = asyncio.Lock()
    return chat_locks[assistant_id]

# 发送消息（同步接口 -> 异步安全）
@router.post("/chat/{assistant_id}", response_model=ChatResponse)
async def send_chat(assistant_id: int, req: ChatRequest):
    # 异步执行阻塞操作
    reply = await asyncio.to_thread(chat_completion, req.message)

    async with get_lock(assistant_id):
        chat_history_db.setdefault(assistant_id, [])
        chat_history_db[assistant_id].append({"role": "user", "content": req.message})
        chat_history_db[assistant_id].append({"role": "assistant", "content": reply})

    return {"success": True, "reply": reply}

# 获取聊天记录
@router.get("/chat/history/{assistant_id}")
async def get_history(assistant_id: int):
    async with get_lock(assistant_id):
        history = chat_history_db.get(assistant_id, [])
        return {"success": True, "data": history}

# WebSocket 流式聊天
@router.websocket("/ws/chat/{assistant_id}")
async def websocket_chat(websocket: WebSocket, assistant_id: int):
    await websocket.accept()
    chat_history_db.setdefault(assistant_id, [])
    lock = get_lock(assistant_id)

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            if not message:
                continue

            async with lock:
                chat_history_db[assistant_id].append({"role": "user", "content": message})

            streaming_reply = ""
            # 异步调用阻塞 stream_chat
            for chunk in await asyncio.to_thread(lambda: list(stream_chat([{"role": "user", "content": message}]))):
                if "chunk" in chunk:
                    streaming_reply += chunk["chunk"]
                    await websocket.send_json({"type": "chunk", "content": chunk["chunk"]})
                elif "error" in chunk:
                    await websocket.send_json({"type": "error", "content": chunk["error"]})
                    break
                elif "done" in chunk:
                    break

            async with lock:
                chat_history_db[assistant_id].append({"role": "assistant", "content": streaming_reply})

            await websocket.send_json({"type": "end"})
    except WebSocketDisconnect:
        print(f"WebSocket {assistant_id} 连接断开")
