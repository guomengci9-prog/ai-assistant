import hashlib
import math
import re
from typing import Iterable, List, Sequence

DEFAULT_VECTOR_DIM = 96


def normalize_whitespace(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def tokenize_text(text: str) -> List[str]:
    tokens: List[str] = []
    current: List[str] = []
    building_ascii = False

    def flush():
        nonlocal current, building_ascii
        if current:
            tokens.append("".join(current))
            current = []
        building_ascii = False

    for char in text:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF:
            flush()
            tokens.append(char)
            continue
        if char.isalnum():
            if not building_ascii:
                flush()
                building_ascii = True
            current.append(char.lower())
        else:
            flush()
    flush()
    return tokens


def compute_embedding(text: str, vector_dim: int = DEFAULT_VECTOR_DIM) -> List[float]:
    tokens = tokenize_text(text)
    if not tokens:
        return [0.0] * vector_dim
    vector = [0.0] * vector_dim
    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % vector_dim
        vector[bucket] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    length = min(len(vec_a), len(vec_b))
    return sum(vec_a[i] * vec_b[i] for i in range(length))


def chunk_text(
    text: str,
    size: int,
    overlap: int,
) -> List[str]:
    clean = normalize_whitespace(text)
    if not clean:
        return []
    chunks: List[str] = []
    start = 0
    length = len(clean)
    while start < length:
        end = min(length, start + size)
        chunks.append(clean[start:end])
        if end >= length:
            break
        start = max(0, end - overlap)
    return chunks


def merge_contexts(items: Iterable[tuple[float, str]], limit: int) -> List[str]:
    sorted_items = sorted(items, key=lambda item: item[0], reverse=True)
    return [content for _, content in sorted_items[:limit] if content]
