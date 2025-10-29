from fastapi import APIRouter
from pydantic import BaseModel
from app.core.deepseek_client import chat_completion, stream_chat

router = APIRouter()

# 内存模拟历史记录（未来可以换数据库）
chat_history_db = {}

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    success: bool
    reply: str

# 发送消息（同步接口，用 chat_completion）
@router.post("/chat/{assistant_id}", response_model=ChatResponse)
async def send_chat(assistant_id: int, req: ChatRequest):
    reply = chat_completion(req.message)

    # 保存历史
    chat_history_db.setdefault(assistant_id, [])
    chat_history_db[assistant_id].append({"role": "user", "content": req.message})
    chat_history_db[assistant_id].append({"role": "assistant", "content": reply})

    return {"success": True, "reply": reply}

# 获取聊天记录
@router.get("/chat/history/{assistant_id}")
async def get_history(assistant_id: int):
    history = chat_history_db.get(assistant_id, [])
    return {"success": True, "data": history}

# WebSocket 流式聊天
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/chat/{assistant_id}")
async def websocket_chat(websocket: WebSocket, assistant_id: int):
    await websocket.accept()
    chat_history_db.setdefault(assistant_id, [])

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            if not message.strip():
                continue

            # 保存用户消息
            chat_history_db[assistant_id].append({"role": "user", "content": message})
            streaming_reply = ""

            # 调用 DeepSeek 流式接口
            for chunk in stream_chat([{"role": "user", "content": message}]):
                if "chunk" in chunk:
                    streaming_reply += chunk["chunk"]
                    await websocket.send_text(chunk["chunk"])
                elif "error" in chunk:
                    await websocket.send_text(f"❌ 错误: {chunk['error']}")
                    break
                elif "done" in chunk:
                    break

            # 保存助手回复到历史
            chat_history_db[assistant_id].append({"role": "assistant", "content": streaming_reply})

            # 告诉前端流结束
            await websocket.send_text("[END]")

    except WebSocketDisconnect:
        print(f"WebSocket {assistant_id} 连接断开")
