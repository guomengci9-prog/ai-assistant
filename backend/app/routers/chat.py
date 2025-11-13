# app/routers/chat.py
import asyncio
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import (
    APIRouter,
    File,
    Form,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select

from app.core.deepseek_client import chat_completion, stream_chat
from app.core.database import Base, db_context, engine
from app.models.chat import AttachmentChunk, ChatConversation, ChatMessage
from app.models.document import Document, DocumentChunk
from app.services import assistants as assistant_service
from app.utils.embedding import (
    DEFAULT_VECTOR_DIM,
    chunk_text,
    compute_embedding,
    cosine_similarity,
)

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[2]
CHAT_UPLOAD_DIR = BASE_DIR / "uploads" / "chat"
CHAT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

# ------------------------------
# 运行时缓存/锁
# ------------------------------
chat_locks: Dict[int, Dict[str, asyncio.Lock]] = {}
assistant_cache: Dict[int, Dict] = {}
VECTOR_DIM = DEFAULT_VECTOR_DIM
CHUNK_CHAR_LIMIT = 800
CHUNK_OVERLAP = 120
MAX_ATTACHMENT_CONTEXT = 4
MAX_KNOWLEDGE_CONTEXT = 6


def get_lock(assistant_id: int, conversation_id: str):
    chat_locks.setdefault(assistant_id, {})
    if conversation_id not in chat_locks[assistant_id]:
        chat_locks[assistant_id][conversation_id] = asyncio.Lock()
    return chat_locks[assistant_id][conversation_id]


def get_assistant_profile(assistant_id: int):
    if assistant_id in assistant_cache:
        return assistant_cache[assistant_id]
    with db_context() as db:
        assistant = assistant_service.get_assistant(db, assistant_id)
    assistant_cache[assistant_id] = assistant or {}
    return assistant_cache[assistant_id]


def ensure_conversation(assistant_id: int, conversation_id: str | None = None) -> Tuple[str, bool, str]:
    """
    Ensure a conversation exists. Returns (conversation_id, created, opening_message).
    """
    opening_message = ""

    with db_context() as db:
        if conversation_id:
            existing = db.get(ChatConversation, conversation_id)
            if existing:
                return existing.id, False, opening_message

        new_id = conversation_id or str(int(time.time() * 1000))
        conversation = ChatConversation(id=new_id, assistant_id=assistant_id)
        db.add(conversation)

        assistant = get_assistant_profile(assistant_id)
        if assistant:
            opening_message = (assistant.get("opening_message") or "").strip()

        if opening_message:
            message = ChatMessage(
                conversation_id=new_id,
                assistant_id=assistant_id,
                role="assistant",
                content=opening_message,
                message_type="opening",
                hide_name=True,
            )
            db.add(message)

    return new_id, True, opening_message


def _query_history(db, assistant_id: int, conversation_id: str) -> List[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(
            ChatMessage.assistant_id == assistant_id,
            ChatMessage.conversation_id == conversation_id,
        )
        .order_by(ChatMessage.id.asc())
    )
    return list(db.scalars(stmt).all())


def load_history(assistant_id: int, conversation_id: str) -> List[dict]:
    with db_context() as db:
        messages = _query_history(db, assistant_id, conversation_id)
        return [message.to_dict() for message in messages]


def append_message_record(
    db,
    assistant_id: int,
    conversation_id: str,
    *,
    role: str,
    content: str,
    message_type: str = "text",
    attachments: List[dict] | None = None,
    hide_name: bool = False,
) -> ChatMessage:
    message = ChatMessage(
        conversation_id=conversation_id,
        assistant_id=assistant_id,
        role=role,
        content=content,
        message_type=message_type,
        attachments=attachments or [],
        hide_name=hide_name,
    )
    db.add(message)
    db.flush()
    return message


def append_message(
    assistant_id: int,
    conversation_id: str,
    *,
    role: str,
    content: str,
    message_type: str = "text",
    attachments: List[dict] | None = None,
    hide_name: bool = False,
) -> dict:
    with db_context() as db:
        message = append_message_record(
            db,
            assistant_id,
            conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            attachments=attachments,
            hide_name=hide_name,
        )
        return message.to_dict()


def append_message_and_get_history(
    assistant_id: int,
    conversation_id: str,
    *,
    role: str,
    content: str,
    message_type: str = "text",
    attachments: List[dict] | None = None,
    hide_name: bool = False,
) -> List[dict]:
    with db_context() as db:
        append_message_record(
            db,
            assistant_id,
            conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            attachments=attachments,
            hide_name=hide_name,
        )
        history = _query_history(db, assistant_id, conversation_id)
        return [message.to_dict() for message in history]


async def iterate_stream_chat(payload: List[dict]):
    """
    Bridge blocking stream_chat generator into async chunks.
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()

    def worker():
        try:
            for chunk in stream_chat(payload):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
        except Exception as exc:  # pragma: no cover - defensive
            loop.call_soon_threadsafe(queue.put_nowait, {"error": str(exc)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, sentinel)

    threading.Thread(target=worker, daemon=True).start()

    while True:
        item = await queue.get()
        if item is sentinel:
            break
        yield item


def _chunk_text(text: str, size: int = CHUNK_CHAR_LIMIT, overlap: int = CHUNK_OVERLAP) -> List[str]:
    return chunk_text(text, size, overlap)


def _extract_text_from_file(path: Path, content_type: str | None) -> str:
    content_type = (content_type or "").lower()
    suffix = path.suffix.lower()
    text_like = content_type.startswith("text/") or suffix in {
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".log",
    }
    if not text_like:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _store_attachment_chunks(
    assistant_id: int,
    conversation_id: str,
    message_id: int,
    text: str,
):
    chunks = _chunk_text(text)
    if not chunks:
        return
    with db_context() as db:
        for index, chunk in enumerate(chunks):
            embedding = compute_embedding(chunk)
            db.add(
                AttachmentChunk(
                    assistant_id=assistant_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                )
            )


def retrieve_attachment_contexts(
    assistant_id: int,
    conversation_id: str,
    query: str,
    limit: int = MAX_ATTACHMENT_CONTEXT,
) -> List[str]:
    query = (query or '').strip()
    if not query:
        return []
    query_embedding = compute_embedding(query)
    if not any(query_embedding):
        return []
    with db_context() as db:
        stmt = (
            select(AttachmentChunk)
            .where(
                AttachmentChunk.assistant_id == assistant_id,
                AttachmentChunk.conversation_id == conversation_id,
            )
            .order_by(AttachmentChunk.id.desc())
        )
        chunk_rows = db.scalars(stmt).all()
        chunks = [
            {'content': row.content, 'embedding': row.embedding or []}
            for row in chunk_rows
        ]
    scored: List[Tuple[float, str]] = []
    for chunk in chunks:
        embedding = chunk['embedding']
        score = cosine_similarity(query_embedding, embedding)
        if score <= 0:
            continue
        scored.append((score, chunk['content']))
    scored.sort(key=lambda item: item[0], reverse=True)
    contexts = []
    for score, content in scored[:limit]:
        contexts.append(f"[附件片段] 相似度 {score:.2f}\n{content}")
    return contexts


def _extract_doc_retrieval_config(doc: Document) -> Dict[str, float | int]:
    params = doc.parameters if isinstance(doc.parameters, dict) else {}
    config: Dict[str, float | int] = {}
    top_k = params.get("top_k") or params.get("retrieve_top_k")
    if isinstance(top_k, int) and top_k > 0:
        config["top_k"] = top_k
    similarity = params.get("similarity_threshold")
    if isinstance(similarity, (int, float)):
        config["similarity_threshold"] = float(similarity)
    return config


def retrieve_knowledge_contexts(
    assistant_id: int,
    query: str,
    limit: int = MAX_KNOWLEDGE_CONTEXT,
) -> List[str]:
    assistant = get_assistant_profile(assistant_id) or {}
    knowledge_ids = assistant.get("knowledge_ids") or []
    if not knowledge_ids:
        return []
    try:
        doc_ids = [int(value) for value in knowledge_ids if int(value) > 0]
    except Exception:
        doc_ids = []
    if not doc_ids or not query:
        return []

    query_embedding = compute_embedding(query)
    if not any(query_embedding):
        return []

    with db_context() as db:
        stmt = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.document_id.in_(doc_ids))
            .limit(600)
        )
        rows = db.execute(stmt).all()

    doc_configs: Dict[int, Dict[str, float | int]] = {}
    doc_hits: Dict[int, List[Tuple[float, str]]] = {}

    for chunk_row, doc in rows:
        embedding = chunk_row.embedding or []
        score = cosine_similarity(query_embedding, embedding)
        if score <= 0:
            continue
        config = doc_configs.setdefault(doc.id, _extract_doc_retrieval_config(doc))
        similarity_threshold = config.get("similarity_threshold")
        if isinstance(similarity_threshold, float) and score < similarity_threshold:
            continue
        metadata = chunk_row.chunk_metadata or {}
        section = metadata.get("section_title")
        doc_name = doc.name or f"Doc#{doc.id}"
        header = f"[知识库:{doc_name}]"
        if section:
            header += f" > {section}"
        header += f" (score {score:.2f})"
        extra = []
        if metadata.get("section_level"):
            extra.append(f"L{metadata.get('section_level')}")
        if metadata.get("category"):
            extra.append(str(metadata.get("category")))
        meta_suffix = f" [{' | '.join(extra)}]" if extra else ""
        content = f"{header}{meta_suffix}\n{chunk_row.content}"
        doc_hits.setdefault(doc.id, []).append((score, content))

    collected: List[Tuple[float, str]] = []
    for doc_id, items in doc_hits.items():
        items.sort(key=lambda item: item[0], reverse=True)
        limit_per_doc = doc_configs.get(doc_id, {}).get("top_k")
        if isinstance(limit_per_doc, int) and limit_per_doc > 0:
            items = items[:limit_per_doc]
        collected.extend(items)

    collected.sort(key=lambda item: item[0], reverse=True)
    return [content for _, content in collected[:limit]]

def build_payload_with_prompt(
    assistant_id: int,
    history: List[dict],
    attachment_contexts: List[str] | None = None,
    knowledge_contexts: List[str] | None = None,
) -> List[dict]:
    assistant = get_assistant_profile(assistant_id) or {}
    system_parts = []
    for key in ("system_prompt", "scene_prompt", "prompt_content"):
        value = (assistant.get(key) or "").strip()
        if value:
            system_parts.append(value)
    system_prompt = "\n".join(system_parts).strip()
    payload = []
    if system_prompt:
        payload.append({"role": "system", "content": system_prompt})
    if attachment_contexts:
        context_text = "\n\n".join(attachment_contexts)
        payload.append(
            {
                "role": "system",
                "content": "以下是与当前对话相关的附件片段，请参考它们回答：\n"
                + context_text,
            }
        )
    if knowledge_contexts:
        payload.append(
            {
                "role": "system",
                "content": "以下是知识库中检索到的片段，请结合它们回答：\n"
                + "\n\n".join(knowledge_contexts),
            }
        )

    for entry in history:
        if entry.get("message_type") == "attachment":
            attachments = entry.get("attachments") or []
            attachment_lines = []
            for attachment in attachments:
                filename = attachment.get("filename", "附件")
                size = attachment.get("size")
                size_info = f" ({size} bytes)" if isinstance(size, (int, float)) else ""
                attachment_lines.append(f"[附件] {filename}{size_info} -> {attachment.get('url', '')}")
            text = "\n".join(attachment_lines) or (entry.get("content") or "用户上传了附件。")
            payload.append({"role": entry.get("role", "user"), "content": text})
        else:
            payload.append(
                {
                    "role": entry.get("role", "user"),
                    "content": entry.get("content", ""),
                }
            )
    return payload

# ------------------------------
# 请求/响应模型
# ------------------------------
class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None  # 可选，如果前端传了就用

class ChatResponse(BaseModel):
    success: bool
    reply: str
    conversation_id: str

# ------------------------------
# 新建会话
# ------------------------------
@router.post("/conversation/{assistant_id}")
async def create_conversation(assistant_id: int):
    conversation_id, _, opening_message = ensure_conversation(assistant_id)
    return {
        "success": True,
        "conversation_id": conversation_id,
        "opening_message": opening_message,
    }

# ------------------------------
# 删除会话
# ------------------------------
@router.delete("/conversation/{assistant_id}/{conversation_id}")
async def delete_conversation(assistant_id: int, conversation_id: str):
    with db_context() as db:
        conversation = db.get(ChatConversation, conversation_id)
        if not conversation or conversation.assistant_id != assistant_id:
            return {"success": True}
        db.execute(
            delete(AttachmentChunk).where(
                AttachmentChunk.assistant_id == assistant_id,
                AttachmentChunk.conversation_id == conversation_id,
            )
        )
        db.execute(
            delete(ChatMessage).where(
                ChatMessage.assistant_id == assistant_id,
                ChatMessage.conversation_id == conversation_id,
            )
        )
        db.delete(conversation)
    return {"success": True}

# ------------------------------
# 发送消息（非流式）
# ------------------------------
@router.post("/chat/{assistant_id}", response_model=ChatResponse)
async def send_chat(assistant_id: int, req: ChatRequest):
    conversation_id, _, _ = ensure_conversation(assistant_id, req.conversation_id)
    lock = get_lock(assistant_id, conversation_id)

    async with lock:
        history = append_message_and_get_history(
            assistant_id,
            conversation_id,
            role="user",
            content=req.message,
        )
        context_segments = retrieve_attachment_contexts(assistant_id, conversation_id, req.message)
        knowledge_segments = retrieve_knowledge_contexts(assistant_id, req.message)
        payload = build_payload_with_prompt(
            assistant_id,
            history,
            attachment_contexts=context_segments,
            knowledge_contexts=knowledge_segments,
        )

    reply = await asyncio.to_thread(chat_completion, payload)

    async with lock:
        append_message(
            assistant_id,
            conversation_id,
            role="assistant",
            content=reply,
        )

    return {"success": True, "reply": reply, "conversation_id": conversation_id}

# ------------------------------
# 获取聊天记录
# ------------------------------
@router.get("/chat/history/{assistant_id}")
async def get_history(assistant_id: int, conversation_id: str = Query(...)):
    lock = get_lock(assistant_id, conversation_id)
    async with lock:
        history = load_history(assistant_id, conversation_id)
        return {"success": True, "data": history}

# ------------------------------
# WebSocket 流式聊天
# ------------------------------
@router.websocket("/ws/chat/{assistant_id}")
async def websocket_chat(websocket: WebSocket, assistant_id: int):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            conversation_id = data.get("conversation_id") or str(int(time.time() * 1000))
            conversation_id, _, _ = ensure_conversation(assistant_id, conversation_id)
            if not message:
                continue

            lock = get_lock(assistant_id, conversation_id)

            async with lock:
                history = append_message_and_get_history(
                    assistant_id,
                    conversation_id,
                    role="user",
                    content=message,
                )
                context_segments = retrieve_attachment_contexts(assistant_id, conversation_id, message)
                knowledge_segments = retrieve_knowledge_contexts(assistant_id, message)
                payload = build_payload_with_prompt(
                    assistant_id,
                    history,
                    attachment_contexts=context_segments,
                    knowledge_contexts=knowledge_segments,
                )
            streaming_reply = ""
            async for chunk in iterate_stream_chat(payload):
                if "chunk" in chunk:
                    streaming_reply += chunk["chunk"]
                    await websocket.send_json({"type": "chunk", "content": chunk["chunk"]})
                elif "error" in chunk:
                    await websocket.send_json({"type": "error", "content": chunk["error"]})
                    break
                elif "done" in chunk:
                    break

            async with lock:
                append_message(
                    assistant_id,
                    conversation_id,
                    role="assistant",
                    content=streaming_reply,
                )

            await websocket.send_json({"type": "end", "conversation_id": conversation_id})

    except WebSocketDisconnect:
        print(f"WebSocket {assistant_id} 连接断开")


@router.post("/chat/{assistant_id}/attachments")
async def upload_attachment(
    assistant_id: int,
    file: UploadFile = File(...),
    conversation_id: str | None = Form(None),
):
    original_name = file.filename or "attachment.bin"
    suffix = Path(original_name).suffix or ".bin"
    storage_name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex}{suffix}"
    storage_path = CHAT_UPLOAD_DIR / storage_name
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    with storage_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        relative_path = storage_path.relative_to(BASE_DIR)
        file_url = f"/{relative_path.as_posix()}"
    except ValueError:
        file_url = storage_path.as_posix()

    conversation_id, created, opening_message = ensure_conversation(assistant_id, conversation_id)
    lock = get_lock(assistant_id, conversation_id)
    attachment_payload = [
        {
            "id": str(uuid.uuid4()),
            "filename": original_name,
            "url": file_url,
            "content_type": file.content_type or "application/octet-stream",
            "size": storage_path.stat().st_size,
            "uploaded_at": int(time.time()),
        }
    ]

    async with lock:
        saved_message = append_message(
            assistant_id,
            conversation_id,
            role="user",
            content=original_name,
            message_type="attachment",
            attachments=attachment_payload,
        )

    attachment_text = _extract_text_from_file(storage_path, file.content_type)
    message_id = saved_message.get("id") if isinstance(saved_message, dict) else None
    if attachment_text and message_id:
        _store_attachment_chunks(
            assistant_id=assistant_id,
            conversation_id=conversation_id,
            message_id=message_id,
            text=attachment_text,
        )

    return {
        "success": True,
        "conversation_id": conversation_id,
        "message": saved_message,
        "opening_message": opening_message if created else "",
    }


@router.get("/conversation/{assistant_id}/{conversation_id}/opening_stream")
async def stream_opening_message(
    assistant_id: int,
    conversation_id: str,
    chunk_size: int = 8,
    delay: float = 0.05,
):
    lock = get_lock(assistant_id, conversation_id)
    async with lock:
        history = load_history(assistant_id, conversation_id)
    opening_text = ""
    for item in history:
        if item.get("message_type") == "opening":
            opening_text = item.get("content", "")
            break

    async def generator():
        if not opening_text:
            yield ""
            return
        size = max(1, chunk_size)
        for i in range(0, len(opening_text), size):
            yield opening_text[i : i + size]
            await asyncio.sleep(max(0.0, delay))

    return StreamingResponse(generator(), media_type="text/plain")
