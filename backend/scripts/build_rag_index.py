"""
构建中文电商售后 Markdown RAG 索引。

用法:
    cd backend
    python scripts/build_rag_index.py

输出:
    backend/app/data/rag_index.sqlite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.langgraph.rag import DEFAULT_CHUNK_CHARS, RAG_DB_PATH, RAG_DOCS_DIR, build_rag_index


def main() -> int:
    parser = argparse.ArgumentParser(description="构建本地 Markdown RAG 索引。")
    parser.add_argument("--docs-dir", type=Path, default=RAG_DOCS_DIR, help="Markdown 文档目录")
    parser.add_argument("--db-path", type=Path, default=RAG_DB_PATH, help="输出 SQLite 索引路径")
    parser.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS, help="chunk 最大字符数")
    args = parser.parse_args()

    stats = build_rag_index(args.docs_dir, args.db_path, args.chunk_chars)
    print("中文电商售后 RAG 索引构建完成")
    print(f"文档目录: {Path(stats['docs_dir']).resolve()}")
    print(f"索引路径: {Path(stats['db_path']).resolve()}")
    print(f"文档数量: {stats['document_count']}")
    print(f"Chunk 数量: {stats['chunk_count']}")
    print(f"FTS5: {'enabled' if stats['fts_enabled'] else 'unavailable, keyword fallback only'}")
    return 0 if stats["document_count"] and stats["chunk_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
