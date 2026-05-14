"""
中文电商售后 Agent 演示数据库验收脚本。

用法:
    cd backend
    python scripts/check_demo_db.py

可选:
    python scripts/check_demo_db.py --db-path app/data/demo_ecommerce.sqlite
    python scripts/check_demo_db.py --require-tools
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sqlite3
import sys
import tempfile
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_ROOT / "app" / "data" / "demo_ecommerce.sqlite"

TABLES = [
    "customers",
    "products",
    "skus",
    "warehouses",
    "inventory",
    "orders",
    "order_items",
    "payments",
    "shipments",
    "shipment_events",
    "after_sales_tickets",
    "ticket_events",
    "refunds",
    "exchanges",
    "compensations",
    "attachments",
    "refund_rules",
]

MIN_COUNTS = {
    "customers": 5_000,
    "products": 800,
    "skus": 2_000,
    "orders": 20_000,
    "order_items": 35_000,
    "after_sales_tickets": 2_000,
    "shipment_events": 20_000,
}


@dataclass(frozen=True)
class SqlCheck:
    code: str
    name: str
    sql: str
    expected: int = 0


CONSISTENCY_CHECKS = [
    SqlCheck(
        "R01",
        "order_items.order_id 都能在 orders 中找到",
        """
        SELECT COUNT(*)
        FROM order_items oi
        LEFT JOIN orders o ON o.order_id = oi.order_id
        WHERE o.order_id IS NULL
        """,
    ),
    SqlCheck(
        "R02",
        "orders.customer_id 都能在 customers 中找到",
        """
        SELECT COUNT(*)
        FROM orders o
        LEFT JOIN customers c ON c.customer_id = o.customer_id
        WHERE c.customer_id IS NULL
        """,
    ),
    SqlCheck(
        "R03",
        "skus.product_id 都能在 products 中找到",
        """
        SELECT COUNT(*)
        FROM skus s
        LEFT JOIN products p ON p.product_id = s.product_id
        WHERE p.product_id IS NULL
        """,
    ),
    SqlCheck(
        "R04",
        "inventory.sku_id 都能在 skus 中找到",
        """
        SELECT COUNT(*)
        FROM inventory i
        LEFT JOIN skus s ON s.sku_id = i.sku_id
        WHERE s.sku_id IS NULL
        """,
    ),
    SqlCheck(
        "R05",
        "payments.order_id 都能在 orders 中找到",
        """
        SELECT COUNT(*)
        FROM payments p
        LEFT JOIN orders o ON o.order_id = p.order_id
        WHERE o.order_id IS NULL
        """,
    ),
    SqlCheck(
        "R06",
        "after_sales_tickets.order_id 都能在 orders 中找到",
        """
        SELECT COUNT(*)
        FROM after_sales_tickets t
        LEFT JOIN orders o ON o.order_id = t.order_id
        WHERE o.order_id IS NULL
        """,
    ),
    SqlCheck(
        "R07",
        "ticket_events.ticket_id 都能在 after_sales_tickets 中找到",
        """
        SELECT COUNT(*)
        FROM ticket_events e
        LEFT JOIN after_sales_tickets t ON t.ticket_id = e.ticket_id
        WHERE t.ticket_id IS NULL
        """,
    ),
    SqlCheck(
        "R08",
        "refunds.ticket_id 都能在 after_sales_tickets 中找到",
        """
        SELECT COUNT(*)
        FROM refunds r
        LEFT JOIN after_sales_tickets t ON t.ticket_id = r.ticket_id
        WHERE t.ticket_id IS NULL
        """,
    ),
    SqlCheck(
        "R09",
        "已签收/已完成订单应有 signed_at 或物流签收事件",
        """
        SELECT COUNT(*)
        FROM (
            SELECT o.order_id
            FROM orders o
            LEFT JOIN shipments s ON s.order_id = o.order_id
            LEFT JOIN shipment_events se
                ON se.shipment_id = s.shipment_id
                AND se.event_description LIKE '%签收%'
            WHERE o.order_status IN ('已签收', '已完成')
            GROUP BY o.order_id
            HAVING MAX(
                CASE WHEN s.signed_at IS NOT NULL OR se.event_id IS NOT NULL
                THEN 1 ELSE 0 END
            ) = 0
        )
        """,
    ),
    SqlCheck(
        "R10",
        "待支付订单不应有 shipment",
        """
        SELECT COUNT(*)
        FROM orders o
        JOIN shipments s ON s.order_id = o.order_id
        WHERE o.order_status = '待支付'
        """,
    ),
    SqlCheck(
        "R11",
        "待发货订单不应有 tracking_no",
        """
        SELECT COUNT(*)
        FROM orders o
        JOIN shipments s ON s.order_id = o.order_id
        WHERE o.order_status = '待发货'
          AND COALESCE(s.tracking_no, '') <> ''
        """,
    ),
    SqlCheck(
        "R12",
        "refund_amount 不得超过订单 paid_amount",
        """
        SELECT COUNT(*)
        FROM refunds r
        JOIN orders o ON o.order_id = r.order_id
        WHERE r.refund_amount > o.paid_amount + 0.01
        """,
    ),
    SqlCheck(
        "R13",
        "工单 created_at 不应早于订单 created_at",
        """
        SELECT COUNT(*)
        FROM after_sales_tickets t
        JOIN orders o ON o.order_id = t.order_id
        WHERE t.created_at < o.created_at
        """,
    ),
    SqlCheck(
        "R14",
        "物流事件时间不应早于订单支付时间",
        """
        SELECT COUNT(*)
        FROM shipment_events se
        JOIN shipments s ON s.shipment_id = se.shipment_id
        JOIN orders o ON o.order_id = s.order_id
        WHERE o.paid_at IS NOT NULL
          AND se.event_time < o.paid_at
        """,
    ),
    SqlCheck(
        "R15",
        "shipments.order_id 都能在 orders 中找到",
        """
        SELECT COUNT(*)
        FROM shipments s
        LEFT JOIN orders o ON o.order_id = s.order_id
        WHERE o.order_id IS NULL
        """,
    ),
    SqlCheck(
        "R16",
        "shipment_events.shipment_id 都能在 shipments 中找到",
        """
        SELECT COUNT(*)
        FROM shipment_events se
        LEFT JOIN shipments s ON s.shipment_id = se.shipment_id
        WHERE s.shipment_id IS NULL
        """,
    ),
    SqlCheck(
        "R17",
        "exchanges.ticket_id 都能在 after_sales_tickets 中找到",
        """
        SELECT COUNT(*)
        FROM exchanges e
        LEFT JOIN after_sales_tickets t ON t.ticket_id = e.ticket_id
        WHERE t.ticket_id IS NULL
        """,
    ),
    SqlCheck(
        "R18",
        "compensations.ticket_id 都能在 after_sales_tickets 中找到",
        """
        SELECT COUNT(*)
        FROM compensations c
        LEFT JOIN after_sales_tickets t ON t.ticket_id = c.ticket_id
        WHERE t.ticket_id IS NULL
        """,
    ),
    SqlCheck(
        "R19",
        "attachments.ticket_id 非空时都能在 after_sales_tickets 中找到",
        """
        SELECT COUNT(*)
        FROM attachments a
        LEFT JOIN after_sales_tickets t ON t.ticket_id = a.ticket_id
        WHERE a.ticket_id IS NOT NULL
          AND t.ticket_id IS NULL
        """,
    ),
]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def status_line(ok: bool, message: str) -> None:
    marker = "PASS" if ok else "FAIL"
    print(f"[{marker}] {message}")


def run_scale_checks(conn: sqlite3.Connection) -> bool:
    print_header("数据规模")
    all_ok = True
    for table in TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        minimum = MIN_COUNTS.get(table)
        if minimum is None:
            print(f"[INFO] {table:24s} {count:8,d}")
            continue

        ok = count >= minimum
        all_ok = all_ok and ok
        status_line(ok, f"{table:24s} {count:8,d} / 最低 {minimum:,}")
    return all_ok


def run_consistency_checks(conn: sqlite3.Connection) -> bool:
    print_header("一致性规则")
    all_ok = True
    for check in CONSISTENCY_CHECKS:
        count = conn.execute(check.sql).fetchone()[0]
        ok = count == check.expected
        all_ok = all_ok and ok
        status_line(ok, f"{check.code} {check.name}；异常数={count}")
    return all_ok


def one_row(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise RuntimeError(f"缺少工具验收样本: {sql.strip()}")
    return row


def parse_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        return json.loads(raw)
    if isinstance(raw, dict):
        return raw
    return json.loads(str(raw))


def invoke_tool(tool_obj: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    if hasattr(tool_obj, "invoke"):
        raw = tool_obj.invoke(kwargs)
    else:
        raw = tool_obj(**kwargs)
    return parse_payload(raw)


def assert_tool_status(name: str, payload: dict[str, Any], expected: set[str]) -> bool:
    status = payload.get("status")
    ok = status in expected
    status_line(ok, f"{name}: status={status}, message={payload.get('message')}")
    return ok


def make_temp_db_copy(db_path: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="demo_ecommerce_check_"))
    temp_db = temp_dir / "demo_ecommerce.sqlite"
    source = sqlite3.connect(str(db_path))
    try:
        target = sqlite3.connect(str(temp_db))
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    return temp_db


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


def run_tool_checks(db_path: Path, require_tools: bool) -> bool:
    print_header("后端工具")
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))

    try:
        tools_mod = importlib.import_module("app.langgraph.tools")
    except ModuleNotFoundError as exc:
        if exc.name != "langchain_core":
            message = f"无法导入 app.langgraph.tools，跳过工具实测。原因: {exc}"
            if require_tools:
                status_line(False, message)
                return False
            print(f"[SKIP] {message}")
            return True

        install_langchain_tool_stub()
        sys.modules.pop("app.langgraph.tools", None)
        tools_mod = importlib.import_module("app.langgraph.tools")
        print("[INFO] 当前环境未安装 langchain_core，已使用轻量 @tool stub 验证 tools.py 的 SQLite 逻辑。")
    except Exception as exc:
        message = (
            "无法导入 app.langgraph.tools，跳过工具实测。"
            "请先安装后端依赖后重试，例如在 backend 目录执行 poetry install。"
            f" 原因: {exc}"
        )
        if require_tools:
            status_line(False, message)
            return False
        print(f"[SKIP] {message}")
        return True

    temp_db = make_temp_db_copy(db_path)
    setattr(tools_mod, "DB_PATH", temp_db)

    try:
        conn = connect(temp_db)
        order = one_row(
            conn,
            """
            SELECT o.order_id, c.phone_last4
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            WHERE o.order_status IN ('已签收', '已完成', '已发货', '运输中')
            LIMIT 1
            """,
        )
        sku = one_row(conn, "SELECT sku_id FROM skus LIMIT 1")
        refund_order = one_row(
            conn,
            """
            SELECT order_id
            FROM orders
            WHERE order_status IN ('已签收', '已完成', '待发货')
            LIMIT 1
            """,
        )
        ticket = one_row(conn, "SELECT ticket_id, order_id FROM after_sales_tickets LIMIT 1")
        create_order = one_row(
            conn,
            """
            SELECT order_id
            FROM orders
            WHERE order_status NOT IN ('待支付', '已取消')
            ORDER BY order_id
            LIMIT 1
            """,
        )
        conn.close()

        results = [
            assert_tool_status(
                "query_order_status",
                invoke_tool(
                    tools_mod.query_order_status,
                    {"order_id": order["order_id"], "phone_last4": order["phone_last4"]},
                ),
                {"success"},
            ),
            assert_tool_status(
                "query_product_inventory",
                invoke_tool(tools_mod.query_product_inventory, {"sku_id": str(sku["sku_id"])}),
                {"success"},
            ),
            assert_tool_status(
                "evaluate_refund_eligibility",
                invoke_tool(
                    tools_mod.evaluate_refund_eligibility,
                    {"order_id": refund_order["order_id"], "issue_type": "七天无理由"},
                ),
                {"success"},
            ),
            assert_tool_status(
                "query_after_sales_ticket",
                invoke_tool(tools_mod.query_after_sales_ticket, {"ticket_id": ticket["ticket_id"]}),
                {"success"},
            ),
        ]

        created_payload = invoke_tool(
            tools_mod.create_after_sales_ticket,
            {
                "order_id": create_order["order_id"],
                "issue_type": "质量问题",
                "description": "验收脚本临时创建：商品存在质量问题，需测试工单写入。",
                "contact_phone": "13800001234",
            },
        )
        results.append(assert_tool_status("create_after_sales_ticket", created_payload, {"success"}))

        created_ticket = created_payload.get("data", {}).get("ticket", {}).get("ticket_id")
        if created_ticket:
            results.append(
                assert_tool_status(
                    "query_after_sales_ticket(created)",
                    invoke_tool(tools_mod.query_after_sales_ticket, {"ticket_id": created_ticket}),
                    {"success"},
                )
            )

        return all(results)
    finally:
        shutil.rmtree(temp_db.parent, ignore_errors=True)


def print_sample_ids(conn: sqlite3.Connection) -> None:
    print_header("演示样本")
    samples = {
        "订单查询": """
            SELECT o.order_id, c.phone_last4, o.order_status
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            WHERE o.order_status IN ('已发货', '运输中', '已签收', '已完成')
            LIMIT 3
        """,
        "待发货退款": """
            SELECT o.order_id, c.phone_last4, o.order_status
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            WHERE o.order_status = '待发货'
            LIMIT 3
        """,
        "库存 SKU": """
            SELECT p.product_name, s.sku_id, s.color, s.size_or_version
            FROM products p
            JOIN skus s ON s.product_id = p.product_id
            LIMIT 3
        """,
        "售后工单": """
            SELECT ticket_id, order_id, issue_type, status
            FROM after_sales_tickets
            LIMIT 3
        """,
    }
    for name, sql in samples.items():
        rows = [dict(row) for row in conn.execute(sql).fetchall()]
        print(f"[INFO] {name}: {json.dumps(rows, ensure_ascii=False)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查中文电商售后演示 SQLite 数据库。")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="SQLite 数据库路径")
    parser.add_argument("--skip-tools", action="store_true", help="跳过后端工具调用验证")
    parser.add_argument("--require-tools", action="store_true", help="工具无法导入或验证失败时返回失败")
    args = parser.parse_args()

    db_path = args.db_path.resolve()
    print("中文电商售后 Agent 演示数据库验收")
    print(f"数据库: {db_path}")

    if not db_path.exists():
        print(f"[FAIL] 数据库不存在: {db_path}")
        print("请先运行: python scripts/generate_demo_db.py")
        return 1

    conn = connect(db_path)
    try:
        scale_ok = run_scale_checks(conn)
        consistency_ok = run_consistency_checks(conn)
        print_sample_ids(conn)
    finally:
        conn.close()

    tools_ok = True
    if args.skip_tools:
        print_header("后端工具")
        print("[SKIP] 已通过 --skip-tools 跳过工具验证。")
    else:
        tools_ok = run_tool_checks(db_path, args.require_tools)

    print_header("结论")
    all_ok = scale_ok and consistency_ok and tools_ok
    status_line(all_ok, "数据库验收通过" if all_ok else "数据库验收未通过，请查看上方 FAIL 项")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
