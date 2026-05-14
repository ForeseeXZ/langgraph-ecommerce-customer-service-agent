from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


APP_ROOT = Path(__file__).resolve().parent.parent
RAG_DOCS_DIR = APP_ROOT / "rag_docs"
RAG_DB_PATH = APP_ROOT / "data" / "rag_index.sqlite"

DEFAULT_CHUNK_CHARS = 760
MIN_RELEVANCE_SCORE = 18

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；!?;])")

ISSUE_ALIASES = {
    "七天无理由": ["七天无理由", "七日无理由", "7天", "七天", "无理由", "商品完好", "二次销售", "拆封", "吊牌", "定制", "定作"],
    "质量问题": ["质量问题", "性能故障", "故障", "坏了", "无法开机", "屏幕异常", "质量", "修理", "换货"],
    "尺码不合适": ["尺码不合适", "尺码", "试穿", "换码", "衣服"],
    "物流破损": ["物流破损", "破损", "碎裂", "变形", "运输损坏", "快递破损"],
    "少件漏发": ["少件漏发", "少件", "漏发", "缺少", "没收到", "发货清单"],
    "未发货退款": ["未发货退款", "未发货", "待发货", "取消订单", "多久到账"],
    "保修咨询": ["保修咨询", "保修", "维修点", "三包", "免费维修"],
    "发票问题": ["发票问题", "发票", "抬头", "税号", "补开", "电子发票"],
    "地址修改": ["地址修改", "修改地址", "收货地址", "拦截"],
    "催发货": ["催发货", "催促发货", "什么时候发货"],
    "安装问题": ["安装问题", "安装", "上门安装", "安装后", "安装质量"],
    "配件缺失": ["配件缺失", "缺配件", "充电器", "数据线", "说明书", "配件"],
    "包装破损": ["包装破损", "外包装", "包装箱", "礼品包装", "面单"],
    "漏液": ["漏液", "泄漏", "漏水", "鼓包", "安全隐患"],
    "过敏反馈": ["过敏反馈", "过敏", "红肿", "瘙痒", "人身健康", "美妆", "化妆品"],
    "工单优先级": ["工单优先级", "优先级", "SLA", "响应时效", "处理组", "工单"],
}

CATEGORY_ALIASES = {
    "通用": ["通用", "消费者", "平台"],
    "退货退款": ["退货退款", "退款", "退货", "七天无理由", "未发货退款"],
    "服饰鞋包": ["服饰鞋包", "服饰", "服装", "衣服", "鞋", "吊牌", "尺码"],
    "数码电子": ["数码电子", "数码", "手机", "电脑", "平板", "耳机", "电子"],
    "家用电器": ["家用电器", "家电", "电器", "安装", "维修"],
    "物流配送": ["物流配送", "物流", "快递", "少件", "漏发", "破损", "包装"],
    "订单管理": ["订单管理", "发票", "地址", "催发货"],
    "工单管理": ["工单管理", "工单", "优先级", "SLA"],
    "三包": ["三包", "保修", "维修", "质量问题", "手机", "家电"],
    "美妆": ["美妆", "化妆品", "过敏", "漏液", "面膜", "口红"],
}

KNOWN_TERMS = sorted(
    {
        term
        for values in list(ISSUE_ALIASES.values()) + list(CATEGORY_ALIASES.values())
        for term in values
    }
    | {
        "凭证",
        "照片",
        "视频",
        "时效",
        "多久",
        "到账",
        "例外",
        "不适用",
        "人工审核",
        "流程",
        "条件",
        "签收",
        "超过",
        "10天",
        "10 天",
        "15天",
        "15 天",
        "24小时",
        "48小时",
        "7日内",
        "7 日内",
        "发货清单",
        "开箱",
        "面单",
        "发票",
        "三包凭证",
        "商品破损",
        "包装破损",
        "定制商品",
    },
    key=len,
    reverse=True,
)
BROAD_QUERY_TERMS = {"通用", "退货", "退款", "售后", "商品", "政策"}


@dataclass(frozen=True)
class RagDocument:
    doc_id: str
    title: str
    source_type: str
    source_url: str
    category: str
    issue_types: list[str]
    authority_level: str
    path: str


@dataclass(frozen=True)
class RagChunk:
    chunk_id: str
    doc_id: str
    title: str
    section_title: str
    content: str
    source_type: str
    source_url: str
    category: str
    issue_types: list[str]
    authority_level: str
    path: str
    chunk_index: int


def build_rag_index(
    docs_dir: Path | str = RAG_DOCS_DIR,
    db_path: Path | str = RAG_DB_PATH,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
) -> dict[str, Any]:
    docs_dir = Path(docs_dir)
    db_path = Path(db_path)
    documents: list[RagDocument] = []
    chunks: list[RagChunk] = []

    for markdown_path in sorted(docs_dir.rglob("*.md")):
        document, document_chunks = parse_markdown_file(markdown_path, docs_dir, chunk_chars)
        documents.append(document)
        chunks.extend(document_chunks)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        _create_schema(conn)
        fts_enabled = _create_fts_table(conn)

        conn.executemany(
            """
            INSERT INTO rag_documents (
                doc_id, title, source_type, source_url, category,
                issue_types, authority_level, path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    doc.doc_id,
                    doc.title,
                    doc.source_type,
                    doc.source_url,
                    doc.category,
                    json.dumps(doc.issue_types, ensure_ascii=False),
                    doc.authority_level,
                    doc.path,
                )
                for doc in documents
            ],
        )
        conn.executemany(
            """
            INSERT INTO rag_chunks (
                chunk_id, doc_id, title, section_title, content, source_type,
                source_url, category, issue_types, authority_level, path, chunk_index
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk.chunk_id,
                    chunk.doc_id,
                    chunk.title,
                    chunk.section_title,
                    chunk.content,
                    chunk.source_type,
                    chunk.source_url,
                    chunk.category,
                    json.dumps(chunk.issue_types, ensure_ascii=False),
                    chunk.authority_level,
                    chunk.path,
                    chunk.chunk_index,
                )
                for chunk in chunks
            ],
        )
        if fts_enabled:
            conn.executemany(
                """
                INSERT INTO rag_chunks_fts (
                    chunk_id, content, title, section_title, issue_types, category
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.content,
                        chunk.title,
                        chunk.section_title,
                        " ".join(chunk.issue_types),
                        chunk.category,
                    )
                    for chunk in chunks
                ],
            )

        conn.commit()
    finally:
        conn.close()

    return {
        "db_path": str(db_path),
        "docs_dir": str(docs_dir),
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "fts_enabled": fts_enabled,
    }


def parse_markdown_file(
    markdown_path: Path,
    docs_dir: Path = RAG_DOCS_DIR,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
) -> tuple[RagDocument, list[RagChunk]]:
    raw = markdown_path.read_text(encoding="utf-8")
    metadata, body = _parse_front_matter(raw)
    title = _as_string(metadata.get("title")) or _first_heading(body) or markdown_path.stem
    doc_id = _as_string(metadata.get("doc_id")) or _slugify(markdown_path.stem)
    issue_types = _as_list(metadata.get("issue_types"))
    source_type = _as_string(metadata.get("source_type")) or _source_type_from_path(markdown_path)
    rel_path = str(markdown_path.relative_to(docs_dir)).replace("\\", "/")
    document = RagDocument(
        doc_id=doc_id,
        title=title,
        source_type=source_type,
        source_url=_as_string(metadata.get("source_url")) or f"local://{doc_id}",
        category=_as_string(metadata.get("category")) or "通用",
        issue_types=issue_types,
        authority_level=_as_string(metadata.get("authority_level")) or "medium",
        path=rel_path,
    )

    chunks: list[RagChunk] = []
    chunk_index = 1
    for section_title, section_content in _iter_markdown_sections(body, title):
        for piece in _split_content(section_content, chunk_chars):
            chunks.append(
                RagChunk(
                    chunk_id=f"{doc_id}_{chunk_index:04d}",
                    doc_id=doc_id,
                    title=document.title,
                    section_title=section_title,
                    content=piece,
                    source_type=document.source_type,
                    source_url=document.source_url,
                    category=document.category,
                    issue_types=document.issue_types,
                    authority_level=document.authority_level,
                    path=document.path,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

    return document, chunks


def query_refund_policy_rag_dict(
    issue_type: str,
    category: str = "通用",
    question: str = "",
    order_status: str = "",
    product_name: str = "",
    top_k: int = 6,
    db_path: Path | str = RAG_DB_PATH,
) -> dict[str, Any]:
    db_path = Path(db_path)
    if not db_path.exists():
        return {
            "status": "not_found",
            "message": "RAG 索引尚未生成，请先运行 python scripts/build_rag_index.py。",
            "data": {
                "issue_type": issue_type,
                "category": category,
                "citations": [],
                "database_path": str(db_path),
            },
        }

    query_text = " ".join(part for part in [issue_type, category, question, order_status, product_name] if part)
    inferred_issue_type = _infer_issue_type(query_text)
    effective_issue_type = issue_type.strip() or inferred_issue_type or "未指定"
    effective_category = category.strip() or _infer_category(query_text) or "通用"

    hits = search_rag_chunks(
        issue_type=effective_issue_type,
        category=effective_category,
        question=question,
        order_status=order_status,
        product_name=product_name,
        top_k=top_k,
        db_path=db_path,
    )
    if not hits:
        return {
            "status": "not_found",
            "message": "演示知识库中未找到足够相关的售后政策。",
            "data": {
                "issue_type": effective_issue_type,
                "category": effective_category,
                "citations": [],
            },
        }

    profile = _policy_profile(effective_issue_type, effective_category, question)
    citations = [_citation_from_hit(hit) for hit in hits]
    snippets = [_make_snippet(hit["content"], query_text) for hit in hits[:3]]
    data = {
        "answer": _compose_answer(profile["answer"], snippets, product_name),
        "issue_type": effective_issue_type,
        "category": effective_category,
        "required_evidence": profile["required_evidence"],
        "processing_time": profile["processing_time"],
        "limitations": profile["limitations"],
        "citations": citations,
    }
    return {
        "status": "success",
        "message": "已检索到相关售后政策。",
        "data": data,
    }


def search_rag_chunks(
    issue_type: str,
    category: str = "通用",
    question: str = "",
    order_status: str = "",
    product_name: str = "",
    top_k: int = 6,
    db_path: Path | str = RAG_DB_PATH,
) -> list[dict[str, Any]]:
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    query_text = " ".join(part for part in [issue_type, category, question, order_status, product_name] if part)
    terms = _query_terms(query_text)
    inferred_issue_type = _infer_issue_type(query_text)
    inferred_category = _infer_category(query_text)
    effective_issue_type = issue_type.strip() or inferred_issue_type
    effective_category = category.strip() or inferred_category or "通用"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT chunk_id, doc_id, title, section_title, content, source_type,
                   source_url, category, issue_types, authority_level, path, chunk_index
            FROM rag_chunks
            """
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()

    scored: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["issue_types_list"] = _loads_list(item.get("issue_types"))
        score, matched_terms = _score_chunk(
            item,
            effective_issue_type,
            effective_category,
            terms,
            query_text,
        )
        if score >= MIN_RELEVANCE_SCORE:
            item["score"] = score
            item["matched_terms"] = matched_terms
            scored.append(item)

    scored.sort(
        key=lambda item: (
            -item["score"],
            0 if item["authority_level"] == "high" else 1,
            0 if item["source_type"] == "official" else 1,
            item["doc_id"],
            item["chunk_index"],
        )
    )
    return _diversify(scored, top_k)


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE rag_documents (
            doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_url TEXT NOT NULL,
            category TEXT NOT NULL,
            issue_types TEXT NOT NULL,
            authority_level TEXT NOT NULL,
            path TEXT NOT NULL
        );

        CREATE TABLE rag_chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            title TEXT NOT NULL,
            section_title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_url TEXT NOT NULL,
            category TEXT NOT NULL,
            issue_types TEXT NOT NULL,
            authority_level TEXT NOT NULL,
            path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            FOREIGN KEY (doc_id) REFERENCES rag_documents(doc_id)
        );

        CREATE INDEX idx_rag_chunks_doc_id ON rag_chunks(doc_id);
        CREATE INDEX idx_rag_chunks_category ON rag_chunks(category);
        CREATE INDEX idx_rag_chunks_source_type ON rag_chunks(source_type);
        CREATE INDEX idx_rag_chunks_authority ON rag_chunks(authority_level);
        """
    )


def _create_fts_table(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE rag_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                content,
                title,
                section_title,
                issue_types,
                category
            )
            """
        )
    except sqlite3.OperationalError:
        return False
    return True


def _parse_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw.strip()

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, raw.strip()

    metadata: dict[str, Any] = {}
    current_key = ""
    for line in lines[1:end_index]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1].isspace():
            if stripped.startswith("- ") and current_key:
                metadata.setdefault(current_key, [])
                if isinstance(metadata[current_key], list):
                    metadata[current_key].append(_clean_yaml_value(stripped[2:]))
            continue

        key, sep, value = line.partition(":")
        if not sep:
            continue
        current_key = key.strip()
        value = value.strip()
        if value == "":
            metadata[current_key] = []
        elif value.startswith("[") and value.endswith("]"):
            metadata[current_key] = [
                _clean_yaml_value(part)
                for part in value[1:-1].split(",")
                if part.strip()
            ]
        else:
            metadata[current_key] = _clean_yaml_value(value)

    return metadata, "\n".join(lines[end_index + 1 :]).strip()


def _iter_markdown_sections(body: str, doc_title: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading_stack: list[tuple[int, str]] = []
    current_title = doc_title
    current_lines: list[str] = []

    def flush() -> None:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append((current_title, content))

    for line in body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            heading = _strip_markdown(match.group(2).strip())
            heading_stack[:] = [(h_level, h_title) for h_level, h_title in heading_stack if h_level < level]
            heading_stack.append((level, heading))
            parts = [title for h_level, title in heading_stack if h_level >= 2]
            current_title = " > ".join(parts) or heading or doc_title
            current_lines = []
        else:
            current_lines.append(line)

    flush()
    return sections


def _split_content(content: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []

    for block in _paragraph_blocks(content):
        if len(block) > max_chars:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
            chunks.extend(_split_long_block(block, max_chars))
            continue

        projected = len("\n\n".join(current + [block]))
        if current and projected > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = [block]
        else:
            current.append(block)

    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def _paragraph_blocks(content: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        if not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line.rstrip())
    if current:
        blocks.append("\n".join(current).strip())
    return blocks


def _split_long_block(block: str, max_chars: int) -> list[str]:
    if "\n" in block:
        pieces: list[str] = []
        current: list[str] = []
        for line in block.splitlines():
            projected = len("\n".join(current + [line]))
            if current and projected > max_chars:
                pieces.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            pieces.append("\n".join(current).strip())
        return pieces

    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_RE.split(block) if sentence.strip()]
    pieces = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) > max_chars:
            pieces.append(current.strip())
            current = sentence
        else:
            current = f"{current}{sentence}"
    if current:
        pieces.append(current.strip())
    return pieces or [block[:max_chars]]


def _score_chunk(
    item: dict[str, Any],
    issue_type: str,
    category: str,
    terms: list[str],
    query_text: str,
) -> tuple[int, list[str]]:
    title = item["title"]
    section = item["section_title"]
    content = item["content"]
    chunk_category = item["category"]
    issue_types = item["issue_types_list"]
    issue_text = " ".join(issue_types)
    haystack = " ".join([title, section, content, chunk_category, issue_text])
    score = 0
    matched_terms: list[str] = []

    if issue_type:
        issue_terms = [issue_type, *ISSUE_ALIASES.get(issue_type, [])]
        if issue_type in issue_types:
            score += 50
            matched_terms.append(issue_type)
        for term in issue_terms:
            if not term:
                continue
            if term in issue_text:
                score += 14
                matched_terms.append(term)
            if term in title:
                score += 12
                matched_terms.append(term)
            if term in section:
                score += 10
                matched_terms.append(term)
            if term in content:
                score += min(12, content.count(term) * 3)
                matched_terms.append(term)

    score += _category_score(category, chunk_category, haystack)

    for term in terms:
        term_score = 0
        if term in title:
            term_score += 8
        if term in section:
            term_score += 7
        if term in issue_text:
            term_score += 7
        if term in chunk_category:
            term_score += 5
        if term in content:
            term_score += min(10, content.count(term) * 2)
        if term_score:
            score += term_score
            matched_terms.append(term)

    if item["authority_level"] == "high":
        score += 6
    elif item["authority_level"] == "medium":
        score += 3
    if item["source_type"] == "official":
        score += 5
    elif item["source_type"] == "internal_sop":
        score += 2

    score += _intent_section_bonus(query_text, section, item["source_type"])
    return score, sorted(set(matched_terms), key=matched_terms.index)


def _category_score(category: str, chunk_category: str, haystack: str) -> int:
    if not category:
        return 0
    if category == "通用":
        return 5 if chunk_category == "通用" else 0
    if category == chunk_category or category in chunk_category or chunk_category in category:
        return 25

    aliases = CATEGORY_ALIASES.get(category, [category])
    for known_category, known_aliases in CATEGORY_ALIASES.items():
        if category == known_category or category in known_aliases:
            aliases = [*aliases, known_category, *known_aliases]

    if any(alias and alias in chunk_category for alias in aliases):
        return 18
    if any(alias and alias in haystack for alias in aliases):
        return 10
    return 0


def _intent_section_bonus(query_text: str, section: str, source_type: str) -> int:
    bonus = 0
    if any(term in query_text for term in ["凭证", "照片", "视频", "上传", "证明"]):
        if "凭证" in section:
            bonus += 25
        if source_type == "internal_sop":
            bonus += 8
    if any(term in query_text for term in ["时效", "多久", "到账", "SLA", "响应"]):
        if any(term in section for term in ["时效", "SLA", "流程"]):
            bonus += 20
        if source_type == "internal_sop":
            bonus += 6
    if any(term in query_text for term in ["例外", "不适用", "超过", "定制", "定作", "吊牌", "拆封"]):
        if any(term in section for term in ["不适用", "注意", "商品完好", "例外"]):
            bonus += 18
        if source_type == "official":
            bonus += 6
    if any(term in query_text for term in ["流程", "怎么处理", "创建", "能不能创建"]):
        if "流程" in section:
            bonus += 15
        if source_type == "internal_sop":
            bonus += 6
    if any(term in query_text for term in ["优先级", "SLA", "处理组"]):
        if any(term in section for term in ["优先级", "SLA", "处理组"]):
            bonus += 30
        if source_type == "internal_sop":
            bonus += 8
    return bonus


def _query_terms(query_text: str) -> list[str]:
    normalized = query_text.replace("十天", "10天").replace("十五天", "15天")
    terms = [term for term in KNOWN_TERMS if term and term in normalized and term not in BROAD_QUERY_TERMS]
    for token in re.findall(r"[A-Za-z0-9_]+", normalized):
        if len(token) >= 2:
            terms.append(token)
    return sorted(set(terms), key=lambda item: (-len(item), item))


def _infer_issue_type(text: str) -> str:
    normalized = text.replace("十天", "10天").replace("十五天", "15天")
    best_issue = ""
    best_score = 0
    for issue_type, aliases in ISSUE_ALIASES.items():
        score = 0
        for alias in [issue_type, *aliases]:
            if alias and alias in normalized:
                score += len(alias)
        if score > best_score:
            best_issue = issue_type
            best_score = score
    return best_issue


def _infer_category(text: str) -> str:
    best_category = ""
    best_score = 0
    for category, aliases in CATEGORY_ALIASES.items():
        score = 0
        for alias in [category, *aliases]:
            if alias and alias in text:
                score += len(alias)
        if score > best_score:
            best_category = category
            best_score = score
    return best_category


def _policy_profile(issue_type: str, category: str, question: str) -> dict[str, Any]:
    profiles: dict[str, dict[str, Any]] = {
        "七天无理由": {
            "answer": "根据演示知识库，七天无理由通常要求消费者在签收次日起 7 日内提出，商品保持完好且不影响二次销售。拆封查验一般不当然影响完好，但定制商品、密封破损影响安全卫生、吊牌剪除、激活或明显使用贬损等情况需要人工审核或可能不适用。",
            "required_evidence": ["订单号", "手机号后四位", "商品整体照片", "包装完整照片"],
            "processing_time": "演示系统规则：审核通过后进入退货流程，退货签收后 7 日内审核退款；到账通常还取决于支付渠道。",
            "limitations": ["超过 7 天需要人工审核", "影响二次销售可能不支持", "特殊商品或已单独确认不适用的商品可能不支持"],
        },
        "质量问题": {
            "answer": "根据演示知识库，质量问题需要先确认故障性质、购买或签收时间和保修状态。数码、家电等三包商品通常按 7 日、15 日和保修期内的规则区分退货、换货和维修，具体结论以凭证和检测审核为准。",
            "required_evidence": ["订单号", "问题照片或视频", "故障现象描述", "发票或三包凭证"],
            "processing_time": "演示系统规则：质量问题通常 24 小时内首次响应；高价值订单可能升级为 12 小时内响应。",
            "limitations": ["人为损坏需人工审核", "自行拆修或非授权维修可能影响保修", "外观瑕疵和性能故障需区分处理"],
        },
        "尺码不合适": {
            "answer": "根据演示知识库，尺码不合适属于七天无理由的变体场景，通常要求签收 7 天以内、未穿着外出、商品和吊牌保持完整。",
            "required_evidence": ["订单号", "手机号后四位", "商品整体照片", "吊牌完整照片", "试穿或尺码说明"],
            "processing_time": "演示系统规则：通常 48 小时内首次响应，审核通过后进入退换货流程。",
            "limitations": ["吊牌剪掉或有穿着痕迹可能不支持", "超过 7 天需要人工审核"],
        },
        "物流破损": {
            "answer": "根据演示知识库，物流破损应优先核实签收时间、外包装状态和商品受损情况。用户应保留原包装、面单和破损商品，必要时快递公司可能上门核验。",
            "required_evidence": ["订单号", "外包装破损照片（含面单）", "商品破损照片", "开箱视频片段"],
            "processing_time": "演示系统规则：常规物流破损 24 小时内响应，大额破损可升级为 12 小时内响应。",
            "limitations": ["签收超过 48 小时认定难度加大", "无开箱照片或视频时需补充其他佐证", "外包装完好但内部破损需人工判断"],
        },
        "少件漏发": {
            "answer": "根据演示知识库，少件漏发需要核对订单明细、实际收到商品和包裹外包装状态。外包装完好更倾向仓库漏发，外包装破损则需结合物流责任核查。",
            "required_evidence": ["订单号", "收到的全部商品照片", "发货清单对比", "包裹称重记录或开箱视频"],
            "processing_time": "演示系统规则：少件漏发通常 24 小时内响应；确认漏发后可安排补发或退款。",
            "limitations": ["高价值少件需仓库和物流交叉验证", "配件缺失和独立商品少件需区分"],
        },
        "未发货退款": {
            "answer": "根据演示知识库，待发货且已支付的订单可以申请未发货退款，通常先确认订单状态，再创建售后工单进入审核。",
            "required_evidence": ["订单号", "手机号后四位", "退款原因"],
            "processing_time": "演示系统规则：24 小时内首次响应，1-2 个工作日完成退款审核，审核通过后 3-7 个工作日原路退回。",
            "limitations": ["已发货但未签收可能需拒收或人工审核", "实际到账时间取决于支付渠道"],
        },
        "保修咨询": {
            "answer": "根据演示知识库，保修咨询应先确认购买时间、商品保修月数、故障是否属于保修覆盖范围，再判断免费维修、付费维修或换货路径。",
            "required_evidence": ["订单号或序列号", "故障描述", "发票或三包凭证"],
            "processing_time": "演示系统规则：保修咨询通常 48 小时内响应；金卡或黑卡会员可升级为中优先级。",
            "limitations": ["人为损坏、超保或自行拆修通常不在免费保修范围内"],
        },
        "发票问题": {
            "answer": "根据演示知识库，发票问题可以创建售后工单。未开票、信息错误和补开/丢失会走不同处理路径，电子发票通常可线上处理，纸质发票补开可能需要人工介入。",
            "required_evidence": ["订单号", "发票抬头和税号", "错误发票截图或接收邮箱"],
            "processing_time": "演示系统规则：发票问题通常 48 小时内响应，电子发票一般 1-3 个工作日开具或重开。",
            "limitations": ["纸质发票补开需人工处理", "企业资质变更类发票信息需财务审核"],
        },
        "安装问题": {
            "answer": "根据演示知识库，家电安装后发现异常需要区分商品故障和安装不当。应先保留安装记录、问题照片或视频，再创建工单交由技术支持组处理。",
            "required_evidence": ["订单号", "安装记录或预约信息", "问题照片或视频", "故障现象描述"],
            "processing_time": "演示系统规则：安装问题通常 48 小时内响应；涉及漏液或安全隐患应升级处理。",
            "limitations": ["自行改装或非授权安装可能影响责任判断", "安装不当和商品质量故障需人工核实"],
        },
        "包装破损": {
            "answer": "根据演示知识库，包装破损要区分外包装破损、商品原包装破损和商品本身破损。商品未受损时通常先补充照片核实；商品受损则按物流破损或质量问题处理。",
            "required_evidence": ["订单号", "包装各角度照片", "面单照片", "商品状态照片"],
            "processing_time": "演示系统规则：包装破损通常 24 小时内响应。",
            "limitations": ["只包装破损不等于商品破损", "礼品包装或影响二次销售时需人工判断"],
        },
        "漏液": {
            "answer": "根据演示知识库，漏液属于可能涉及安全隐患的场景，应先提醒用户断电、远离漏液区域并保留现场，再创建紧急或高优先级工单。",
            "required_evidence": ["订单号", "漏液部位照片", "包装或商品状态照片", "安全处置说明"],
            "processing_time": "演示系统规则：漏液通常按高优先级处理，严重场景 12 小时内响应。",
            "limitations": ["安全风险优先于退换货判断", "责任需结合物流、安装和商品质量核实"],
        },
        "过敏反馈": {
            "answer": "根据演示知识库，过敏反馈涉及人身健康，不应直接判定责任。Agent 应收集过敏部位照片、使用时间和商品信息，并创建工单转人工审核。",
            "required_evidence": ["订单号", "过敏部位清晰照片", "使用时间描述", "商品成分或标签照片"],
            "processing_time": "演示系统规则：过敏反馈通常 24 小时内响应并转人工审核。",
            "limitations": ["不能直接认定一定是商品问题", "需排除个人过敏史和使用方式等因素"],
        },
        "工单优先级": {
            "answer": "根据演示知识库，工单优先级由问题类型、订单金额和会员等级共同决定。高价值订单、质量问题、物流破损、漏液和过敏反馈会提高优先级，黑卡会员会分配到 VIP 客服组。",
            "required_evidence": ["问题类型", "订单金额", "会员等级", "订单号"],
            "processing_time": "演示系统规则：紧急 12 小时内首次响应，高优先级 24 小时内首次响应，中低优先级 48 小时内首次响应。",
            "limitations": ["SLA 为演示系统内部规则", "最终优先级以系统创建工单时计算结果为准"],
        },
    }

    inferred_issue_type = _infer_issue_type(" ".join([issue_type, category, question]))
    return profiles.get(issue_type) or profiles.get(inferred_issue_type) or {
        "answer": "根据演示知识库，需结合命中文档的政策条款和内部 SOP 判断处理方式；涉及订单事实时应先查询订单并进行资格预判断。",
        "required_evidence": ["订单号", "问题描述", "相关照片或视频"],
        "processing_time": "演示系统规则：一般售后问题按 24-48 小时内首次响应处理。",
        "limitations": ["资料不足时需要人工审核", "演示系统规则不代表真实平台承诺"],
    }


def _compose_answer(base_answer: str, snippets: list[str], product_name: str) -> str:
    parts = [base_answer]
    if product_name:
        parts.append(f"涉及商品：{product_name}。")
    useful_snippets = [snippet for snippet in snippets if snippet]
    if useful_snippets:
        parts.append("命中文档要点：" + "；".join(useful_snippets[:2]))
    return "".join(parts)


def _make_snippet(content: str, query_text: str, max_chars: int = 120) -> str:
    terms = _query_terms(query_text)
    lines = [_strip_markdown(line.strip()) for line in content.splitlines() if line.strip()]
    preferred = [
        line
        for line in lines
        if any(term in line for term in terms)
        and not set(line) <= {"|", "-", " "}
    ]
    candidate = preferred[0] if preferred else (lines[0] if lines else "")
    candidate = re.sub(r"\s+", " ", candidate).strip()
    if len(candidate) <= max_chars:
        return candidate
    return candidate[: max_chars - 1].rstrip() + "..."


def _citation_from_hit(hit: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": hit["chunk_id"],
        "title": hit["title"],
        "source_url": hit["source_url"],
        "section_title": hit["section_title"],
        "source_type": hit["source_type"],
        "authority_level": hit["authority_level"],
    }


def _diversify(items: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_doc: dict[str, int] = {}
    for item in items:
        if per_doc.get(item["doc_id"], 0) >= 2:
            continue
        selected.append(item)
        per_doc[item["doc_id"]] = per_doc.get(item["doc_id"], 0) + 1
        if len(selected) >= top_k:
            return selected

    if len(selected) < top_k:
        selected_ids = {item["chunk_id"] for item in selected}
        for item in items:
            if item["chunk_id"] in selected_ids:
                continue
            selected.append(item)
            if len(selected) >= top_k:
                break
    return selected


def _clean_yaml_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _as_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value).strip()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value).strip()]


def _loads_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        loaded = json.loads(str(value))
    except json.JSONDecodeError:
        return [part.strip() for part in str(value).split(",") if part.strip()]
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def _first_heading(body: str) -> str:
    for line in body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return _strip_markdown(match.group(2).strip())
    return ""


def _strip_markdown(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = value.replace("**", "").replace("__", "")
    value = re.sub(r"^\s*[-*+]\s+", "", value)
    value = re.sub(r"^\s*\d+\.\s+", "", value)
    return value.strip()


def _source_type_from_path(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    if "official" in parts:
        return "official"
    if "internal" in parts:
        return "internal_sop"
    return "local"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    return slug or "rag_document"
