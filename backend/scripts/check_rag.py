"""
中文电商售后 RAG 验收脚本。

用法:
    cd backend
    python scripts/check_rag.py

可选:
    python scripts/check_rag.py --rebuild
    python scripts/check_rag.py --db-path app/data/rag_index.sqlite
"""

from __future__ import annotations

import argparse
import importlib
import json
import sqlite3
import sys
import types
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.langgraph.rag import RAG_DB_PATH, RAG_DOCS_DIR, build_rag_index


CASES = [
    {
        "name": "七天无理由退货条件",
        "issue_type": "七天无理由",
        "category": "通用",
        "question": "七天无理由退货需要满足什么条件？",
        "expected_terms": ["七天", "完好"],
    },
    {
        "name": "拆封与七天无理由",
        "issue_type": "七天无理由",
        "category": "通用",
        "question": "商品拆封了还能七天无理由退吗？",
        "expected_terms": ["拆封", "完好"],
    },
    {
        "name": "衣服吊牌剪掉",
        "issue_type": "七天无理由",
        "category": "服饰鞋包",
        "question": "衣服吊牌剪了还能退吗？",
        "expected_terms": ["吊牌"],
    },
    {
        "name": "数码质量凭证",
        "issue_type": "质量问题",
        "category": "数码电子",
        "question": "数码产品质量问题需要提供什么凭证？",
        "expected_terms": ["故障", "照片"],
    },
    {
        "name": "手机 10 天故障",
        "issue_type": "质量问题",
        "category": "数码电子",
        "question": "手机用了 10 天出故障，能退还是只能修？",
        "expected_terms": ["15", "换货"],
    },
    {
        "name": "家电安装后质量问题",
        "issue_type": "质量问题",
        "category": "家用电器",
        "question": "家电安装后发现质量问题怎么处理？",
        "expected_terms": ["安装", "质量"],
    },
    {
        "name": "物流破损照片",
        "issue_type": "物流破损",
        "category": "物流配送",
        "question": "物流破损应该上传哪些照片？",
        "expected_terms": ["外包装", "照片"],
    },
    {
        "name": "少件漏发证明",
        "issue_type": "少件漏发",
        "category": "物流配送",
        "question": "少件漏发怎么证明？",
        "expected_terms": ["发货清单", "照片"],
    },
    {
        "name": "发票工单",
        "issue_type": "发票问题",
        "category": "订单管理",
        "question": "发票问题能不能创建售后？",
        "expected_terms": ["发票", "工单"],
    },
    {
        "name": "未发货退款到账",
        "issue_type": "未发货退款",
        "category": "退货退款",
        "question": "未发货订单退款多久到账？",
        "expected_terms": ["3-7", "工作日"],
    },
    {
        "name": "超过 7 天退货",
        "issue_type": "七天无理由",
        "category": "通用",
        "question": "超过 7 天还能退货吗？",
        "expected_terms": ["超过", "人工审核"],
    },
    {
        "name": "定制商品七天无理由",
        "issue_type": "七天无理由",
        "category": "通用",
        "question": "定制商品支持七天无理由吗？",
        "expected_terms": ["定制", "不适用"],
    },
    {
        "name": "美妆拆封后过敏",
        "issue_type": "过敏反馈",
        "category": "美妆",
        "question": "美妆拆封后过敏怎么处理？",
        "expected_terms": ["过敏", "人工审核"],
    },
    {
        "name": "包装破损与商品破损",
        "issue_type": "包装破损",
        "category": "物流配送",
        "question": "包装破损和商品破损有什么区别？",
        "expected_terms": ["包装破损", "商品破损"],
    },
    {
        "name": "工单优先级",
        "issue_type": "工单优先级",
        "category": "工单管理",
        "question": "工单优先级怎么判断？",
        "expected_terms": ["订单金额", "会员等级"],
    },
]

NEGATIVE_CASE = {
    "issue_type": "火星售后",
    "category": "通用",
    "question": "火星仓库的星际退货政策是什么？",
}


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def status_line(ok: bool, message: str) -> None:
    marker = "PASS" if ok else "FAIL"
    print(f"[{marker}] {message}")


def parse_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        return json.loads(raw)
    if isinstance(raw, dict):
        return raw
    return json.loads(str(raw))


def install_langchain_tool_stub() -> None:
    fake_core = types.ModuleType("langchain_core")
    fake_tools = types.ModuleType("langchain_core.tools")

    def tool(func: Any = None, *args: Any, **kwargs: Any) -> Any:
        def decorator(inner: Any) -> Any:
            return inner

        if callable(func):
            return decorator(func)
        return decorator

    fake_tools.tool = tool
    sys.modules.setdefault("langchain_core", fake_core)
    sys.modules["langchain_core.tools"] = fake_tools


def load_tools_module() -> Any:
    try:
        return importlib.import_module("app.langgraph.tools")
    except ModuleNotFoundError as exc:
        if exc.name != "langchain_core":
            raise
        install_langchain_tool_stub()
        sys.modules.pop("app.langgraph.tools", None)
        print("[INFO] 当前环境未安装 langchain_core，已使用轻量 @tool stub 验证 RAG 工具逻辑。")
        return importlib.import_module("app.langgraph.tools")


def invoke_tool(tool_obj: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    if hasattr(tool_obj, "invoke"):
        return parse_payload(tool_obj.invoke(kwargs))
    return parse_payload(tool_obj(**kwargs))


def ensure_index(db_path: Path, rebuild: bool) -> None:
    if rebuild or not db_path.exists():
        stats = build_rag_index(RAG_DOCS_DIR, db_path)
        print(
            "[INFO] 已构建 RAG 索引: "
            f"documents={stats['document_count']}, chunks={stats['chunk_count']}, "
            f"fts_enabled={stats['fts_enabled']}"
        )


def run_schema_checks(db_path: Path) -> bool:
    print_header("索引结构")
    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
            ).fetchall()
        }
        required = {"rag_documents", "rag_chunks", "rag_chunks_fts"}
        all_ok = True
        for table in sorted(required):
            ok = table in tables
            all_ok = all_ok and ok
            status_line(ok, f"存在表 {table}")

        doc_count = conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
        status_line(doc_count >= 10, f"文档数量 {doc_count}")
        status_line(chunk_count >= 30, f"Chunk 数量 {chunk_count}")
        return all_ok and doc_count >= 10 and chunk_count >= 30
    finally:
        conn.close()


def case_text(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    return json.dumps(data, ensure_ascii=False)


def run_query_checks(tools_mod: Any) -> bool:
    print_header("验收问题")
    all_ok = True
    for case in CASES:
        payload = invoke_tool(
            tools_mod.query_refund_policy_rag,
            {
                "issue_type": case["issue_type"],
                "category": case["category"],
                "question": case["question"],
            },
        )
        data = payload.get("data") or {}
        citations = data.get("citations") or []
        text = case_text(payload)
        ok = (
            payload.get("status") == "success"
            and len(citations) >= 1
            and any(term in text for term in case["expected_terms"])
        )
        all_ok = all_ok and ok
        status_line(
            ok,
            f"{case['name']}: status={payload.get('status')}, citations={len(citations)}",
        )

    print_header("低置信兜底")
    negative = invoke_tool(tools_mod.query_refund_policy_rag, NEGATIVE_CASE)
    negative_ok = negative.get("status") == "not_found"
    status_line(negative_ok, f"无关问题返回 {negative.get('status')}")
    return all_ok and negative_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="验证中文电商售后 RAG 索引和工具。")
    parser.add_argument("--db-path", type=Path, default=RAG_DB_PATH, help="RAG SQLite 索引路径")
    parser.add_argument("--rebuild", action="store_true", help="验证前重建 RAG 索引")
    args = parser.parse_args()

    db_path = args.db_path.resolve()
    print("中文电商售后 Agent RAG 验收")
    print(f"索引: {db_path}")
    ensure_index(db_path, args.rebuild)

    if not db_path.exists():
        status_line(False, "RAG 索引不存在，请先运行 python scripts/build_rag_index.py")
        return 1

    schema_ok = run_schema_checks(db_path)
    tools_mod = load_tools_module()
    query_ok = run_query_checks(tools_mod)

    print_header("结论")
    all_ok = schema_ok and query_ok
    status_line(all_ok, "RAG 验收通过" if all_ok else "RAG 验收未通过，请查看上方 FAIL 项")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
