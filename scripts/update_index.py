#!/usr/bin/env python3
"""Инкрементальное обновление FAISS-индекса (Задание 6): SHA-1 снимок KB → diff → полное перестроение."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_vector_index import split_text_into_chunks  # type: ignore  # noqa: E402

KB_PATH = Path(os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base"))
INDEX_PATH = Path(os.getenv("FAISS_INDEX_PATH", "vector_index/faiss_index.bin"))
CHUNKS_PATH = Path(os.getenv("FAISS_CHUNKS_PATH", "vector_index/chunks.pkl"))
STATE_PATH = Path("vector_index/files_state.json")
LOG_PATH = Path(os.getenv("UPDATE_LOG_PATH", "logs/update.log"))
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("update_index")


def file_hash(path: Path) -> str:
    h = hashlib.sha1()
    h.update(path.read_bytes())
    return h.hexdigest()


def scan_kb() -> Dict[str, str]:
    """Вернёт {относительный_путь: sha1}."""
    state: Dict[str, str] = {}
    for txt in KB_PATH.rglob("*.txt"):
        rel = str(txt.relative_to(KB_PATH))
        state[rel] = file_hash(txt)
    return state


def load_state() -> Dict[str, str]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text("utf-8"))
    return {}


def save_state(state: Dict[str, str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), "utf-8")


def build_chunks_for_file(rel_path: str) -> List[dict]:
    abs_path = KB_PATH / rel_path
    text = abs_path.read_text("utf-8")
    chunks: List[dict] = []
    for i, chunk in enumerate(split_text_into_chunks(text)):
        chunks.append(
            {
                "text": chunk,
                "source": rel_path,
                "category": abs_path.parent.name,
                "filename": abs_path.name,
                "chunk_id": i,
            }
        )
    return chunks


def write_log(payload: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload["ts"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    started = time.time()
    if not KB_PATH.exists():
        logger.error("Knowledge base path %s does not exist", KB_PATH)
        write_log(
            {
                "event": "update_index",
                "status": "error",
                "error": f"kb path missing: {KB_PATH}",
            }
        )
        return 1

    old_state = load_state()
    new_state = scan_kb()

    added = sorted(set(new_state) - set(old_state))
    removed = sorted(set(old_state) - set(new_state))
    changed = sorted(
        f for f in (set(old_state) & set(new_state)) if old_state[f] != new_state[f]
    )

    logger.info(
        "scanned: %d files | added=%d changed=%d removed=%d",
        len(new_state),
        len(added),
        len(changed),
        len(removed),
    )

    if not (added or changed or removed) and INDEX_PATH.exists():
        write_log(
            {
                "event": "update_index",
                "status": "noop",
                "files": len(new_state),
                "duration_s": round(time.time() - started, 2),
            }
        )
        logger.info("nothing to update")
        return 0

    all_chunks: List[dict] = []
    for rel in sorted(new_state):
        all_chunks.extend(build_chunks_for_file(rel))

    logger.info("building embeddings for %d chunks", len(all_chunks))
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(
        [c["text"] for c in all_chunks], show_progress_bar=False
    ).astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with CHUNKS_PATH.open("wb") as f:
        pickle.dump(all_chunks, f)
    save_state(new_state)

    duration = round(time.time() - started, 2)
    payload = {
        "event": "update_index",
        "status": "ok",
        "files_total": len(new_state),
        "files_added": len(added),
        "files_changed": len(changed),
        "files_removed": len(removed),
        "chunks_total": len(all_chunks),
        "embedding_dim": dim,
        "duration_s": duration,
        "model": EMBEDDING_MODEL,
        "added": added[:20],
        "changed": changed[:20],
        "removed": removed[:20],
    }
    write_log(payload)
    logger.info(
        "index updated: chunks=%d, duration=%.2fs", len(all_chunks), duration
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
