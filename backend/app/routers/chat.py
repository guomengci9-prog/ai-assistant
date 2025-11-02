# app/routers/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
import asyncio
from app.core.deepseek_client import chat_completion, stream_chat
import time
import uuid

router = APIRouter()

# ------------------------------
# 数据存储（内存模拟，可改成数据库）
# ------------------------------
chat_history_db = {}  # { assistant_id: { conversation_id: [ {role, content}, ... ] } }
chat_locks = {}       # { assistant_id: { conversation_id: Lock() } }

def get_lock(assistant_id: int, conversation_id: str):
    chat_locks.setdefault(assistant_id, {})
    if conversation_id not in chat_locks[assistant_id]:
        chat_locks[assistant_id][conversation_id] = asyncio.Lock()
    return chat_locks[assistant_id][conversation_id]

# ------------------------------
# 请求/响应模型
# ------------------------------
class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None  # 可选，如果前端传了就用

class ChatResponse(BaseModel):
    success: bool
    reply: str

# ------------------------------
# 新建会话
# ------------------------------
@router.post("/conversation/{assistant_id}")
async def create_conversation(assistant_id: int):
    conversation_id = str(int(time.time() * 1000))  # 时间戳ID
    chat_history_db.setdefault(assistant_id, {})
    chat_history_db[assistant_id][conversation_id] = []
    return {"success": True, "conversation_id": conversation_id}

# ------------------------------
# 删除会话
# ------------------------------
@router.delete("/conversation/{assistant_id}/{conversation_id}")
async def delete_conversation(assistant_id: int, conversation_id: str):
    if assistant_id in chat_history_db and conversation_id in chat_history_db[assistant_id]:
        del chat_history_db[assistant_id][conversation_id]
    return {"success": True}

# ------------------------------
# 发送消息（非流式）
# ------------------------------
@router.post("/chat/{assistant_id}", response_model=ChatResponse)
async def send_chat(assistant_id: int, req: ChatRequest):
    # 确认会话ID
    conversation_id = req.conversation_id or str(int(time.time() * 1000))
    chat_history_db.setdefault(assistant_id, {})
    chat_history_db[assistant_id].setdefault(conversation_id, [])

    # 异步执行阻塞函数
    reply = await asyncio.to_thread(chat_completion, req.message)

    async with get_lock(assistant_id, conversation_id):
        chat_history_db[assistant_id][conversation_id].append({"role": "user", "content": req.message})
        chat_history_db[assistant_id][conversation_id].append({"role": "assistant", "content": reply})

    return {"success": True, "reply": reply, "conversation_id": conversation_id}

# ------------------------------
# 获取聊天记录
# ------------------------------
@router.get("/chat/history/{assistant_id}")
async def get_history(assistant_id: int, conversation_id: str = Query(...)):
    chat_history_db.setdefault(assistant_id, {})
    async with get_lock(assistant_id, conversation_id):
        history = chat_history_db[assistant_id].get(conversation_id, [])
        return {"success": True, "data": history}

# ------------------------------
# WebSocket 流式聊天
# ------------------------------
@router.websocket("/ws/chat/{assistant_id}")
async def websocket_chat(websocket: WebSocket, assistant_id: int):
    await websocket.accept()
    chat_history_db.setdefault(assistant_id, {})

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            conversation_id = data.get("conversation_id") or str(int(time.time() * 1000))
            if not message:
                continue

            chat_history_db[assistant_id].setdefault(conversation_id, [])
            lock = get_lock(assistant_id, conversation_id)

            async with lock:
                chat_history_db[assistant_id][conversation_id].append({"role": "user", "content": message})

            streaming_reply = ""
            # 异步调用阻塞函数 stream_chat
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
                chat_history_db[assistant_id][conversation_id].append({"role": "assistant", "content": streaming_reply})

            await websocket.send_json({"type": "end", "conversation_id": conversation_id})

    except WebSocketDisconnect:
        print(f"WebSocket {assistant_id} 连接断开")
