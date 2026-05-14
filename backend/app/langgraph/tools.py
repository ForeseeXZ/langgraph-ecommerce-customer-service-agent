import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from .rag import query_refund_policy_rag_dict

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_ecommerce.sqlite"
VALID_ISSUE_TYPES = (
    "七天无理由",
    "质量问题",
    "尺码不合适",
    "物流破损",
    "少件漏发",
    "未发货退款",
    "保修咨询",
    "发票问题",
    "地址修改",
    "催发货",
    "安装问题",
    "配件缺失",
    "包装破损",
    "漏液",
    "过敏反馈",
)


def to_payload(status: str, message: str, data: Any) -> str:
    return json.dumps(
        {
            "status": status,
            "message": message,
            "data": data,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        ensure_ascii=False,
    )


def _database_not_ready_payload() -> str:
    return to_payload(
        "database_not_ready",
        "演示数据库尚未生成，请先生成 backend/app/data/demo_ecommerce.sqlite。",
        {"database_path": str(DB_PATH)},
    )


def _get_conn() -> sqlite3.Connection | None:
    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [_row_to_dict(row) for row in rows]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None


def _active_ticket_statuses() -> tuple[str, ...]:
    return ("已创建", "待补充凭证", "审核中", "待寄回", "仓库验收中", "退款中", "换货处理中")


def _priority_for(issue_type: str, order_total: float, member_level: str) -> str:
    if order_total >= 5000 or (issue_type in ("质量问题", "物流破损") and order_total >= 2000):
        return "紧急"
    if issue_type in ("质量问题", "物流破损", "漏液", "过敏反馈", "少件漏发") or order_total >= 1000:
        return "高"
    if issue_type in ("保修咨询", "发票问题", "地址修改"):
        return "中" if member_level in ("金卡会员", "黑卡会员") else "低"
    return "中"


def _assigned_group_for(issue_type: str, member_level: str) -> str:
    if member_level == "黑卡会员":
        return "VIP客服组"
    if issue_type in ("物流破损", "少件漏发", "催发货", "地址修改"):
        return "仓储物流组"
    if issue_type in ("质量问题", "漏液", "过敏反馈", "安装问题", "配件缺失"):
        return "技术支持组"
    if issue_type in ("七天无理由", "未发货退款", "尺码不合适"):
        return "退款审核组"
    return "售后服务组"


def _next_ticket_id(conn: sqlite3.Connection) -> str:
    prefix = f"AS{datetime.now().strftime('%Y%m%d')}"
    latest = conn.execute(
        "SELECT ticket_id FROM after_sales_tickets "
        "WHERE ticket_id LIKE ? ORDER BY ticket_id DESC LIMIT 1",
        (f"{prefix}%",),
    ).fetchone()
    if latest:
        suffix = latest["ticket_id"][len(prefix):]
        if suffix.isdigit():
            return f"{prefix}{int(suffix) + 1:06d}"
    return f"{prefix}000001"


def _ticket_bundle(conn: sqlite3.Connection, ticket: sqlite3.Row) -> dict[str, Any]:
    ticket_dict = _row_to_dict(ticket)
    ticket_id = ticket_dict["ticket_id"]
    return {
        "ticket": ticket_dict,
        "events": _rows_to_dicts(
            conn.execute(
                "SELECT * FROM ticket_events WHERE ticket_id = ? ORDER BY event_time, event_id",
                (ticket_id,),
            ).fetchall()
        ),
        "refunds": _rows_to_dicts(
            conn.execute(
                "SELECT * FROM refunds WHERE ticket_id = ? ORDER BY requested_at DESC, refund_id DESC",
                (ticket_id,),
            ).fetchall()
        ),
        "exchanges": _rows_to_dicts(
            conn.execute(
                "SELECT * FROM exchanges WHERE ticket_id = ? ORDER BY created_at DESC, exchange_id DESC",
                (ticket_id,),
            ).fetchall()
        ),
        "compensations": _rows_to_dicts(
            conn.execute(
                "SELECT * FROM compensations WHERE ticket_id = ? ORDER BY issued_at DESC, compensation_id DESC",
                (ticket_id,),
            ).fetchall()
        ),
        "attachments": _rows_to_dicts(
            conn.execute(
                "SELECT * FROM attachments WHERE ticket_id = ? ORDER BY uploaded_at DESC, attachment_id DESC",
                (ticket_id,),
            ).fetchall()
        ),
    }


@tool
def query_order_status(order_id: str, phone_last4: str = "") -> str:
    """查询订单状态、支付信息、商品明细、物流信息、物流轨迹和售后状态。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        order = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        if order is None:
            return to_payload("not_found", f"未找到订单 {order_id}。", {"order_id": order_id})

        customer = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (order["customer_id"],),
        ).fetchone()
        customer_dict = _row_to_dict(customer)
        if phone_last4 and customer_dict.get("phone_last4") != phone_last4:
            return to_payload(
                "forbidden",
                "手机号后四位校验失败，请确认后再查询。",
                {"order_id": order_id},
            )

        payment = conn.execute(
            "SELECT * FROM payments WHERE order_id = ? ORDER BY payment_id DESC LIMIT 1",
            (order_id,),
        ).fetchone()
        items = conn.execute(
            "SELECT oi.*, p.category, p.brand, s.color, s.size_or_version, "
            "s.supports_7days_return, s.warranty_months "
            "FROM order_items oi "
            "JOIN products p ON oi.product_id = p.product_id "
            "JOIN skus s ON oi.sku_id = s.sku_id "
            "WHERE oi.order_id = ? ORDER BY oi.order_item_id",
            (order_id,),
        ).fetchall()
        shipment = conn.execute(
            "SELECT s.*, w.warehouse_name, w.province AS warehouse_province, w.city AS warehouse_city "
            "FROM shipments s "
            "LEFT JOIN warehouses w ON s.warehouse_id = w.warehouse_id "
            "WHERE s.order_id = ? ORDER BY s.shipment_id DESC LIMIT 1",
            (order_id,),
        ).fetchone()
        shipment_events: list[dict[str, Any]] = []
        if shipment:
            shipment_events = _rows_to_dicts(
                conn.execute(
                    "SELECT * FROM shipment_events WHERE shipment_id = ? ORDER BY event_time, event_id",
                    (shipment["shipment_id"],),
                ).fetchall()
            )
        tickets = conn.execute(
            "SELECT * FROM after_sales_tickets WHERE order_id = ? ORDER BY created_at DESC",
            (order_id,),
        ).fetchall()

        data = {
            "order": _row_to_dict(order),
            "customer": customer_dict,
            "payment": _row_to_dict(payment),
            "items": _rows_to_dicts(items),
            "shipment": _row_to_dict(shipment),
            "shipment_events": shipment_events,
            "after_sales_tickets": _rows_to_dicts(tickets),
        }
        return to_payload("success", f"已查询到订单 {order_id} 的完整售后信息。", data)
    finally:
        conn.close()


@tool
def query_product_inventory(product_id: str = "", product_name: str = "", sku_id: str = "") -> str:
    """按商品编号、商品名称或 SKU 编号查询商品、SKU、仓库库存和补货时间。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        if not any((product_id, product_name, sku_id)):
            return to_payload(
                "failed",
                "请至少提供 product_id、product_name 或 sku_id 中的一个。",
                {"product_id": product_id, "product_name": product_name, "sku_id": sku_id},
            )

        sql = (
            "SELECT p.product_id, p.product_name, p.category, p.brand, p.status, "
            "p.base_price, p.return_rate, p.rating, "
            "s.sku_id, s.color, s.size_or_version, s.price, "
            "s.supports_7days_return, s.warranty_months "
            "FROM products p JOIN skus s ON p.product_id = s.product_id "
        )
        params: tuple[Any, ...]
        if sku_id:
            sql += "WHERE s.sku_id = ? "
            params = (sku_id,)
        elif product_id:
            sql += "WHERE p.product_id = ? "
            params = (product_id,)
        else:
            sql += "WHERE p.product_name LIKE ? "
            params = (f"%{product_name}%",)
        sql += "ORDER BY p.product_id, s.sku_id LIMIT 20"

        rows = conn.execute(sql, params).fetchall()
        if not rows:
            return to_payload(
                "not_found",
                "未找到对应商品或 SKU，请提供更准确的商品编号、SKU 编号或商品名称。",
                {"product_id": product_id, "product_name": product_name, "sku_id": sku_id},
            )

        products: dict[int, dict[str, Any]] = {}
        for row in rows:
            product_key = row["product_id"]
            if product_key not in products:
                products[product_key] = {
                    "product": {
                        "product_id": row["product_id"],
                        "product_name": row["product_name"],
                        "category": row["category"],
                        "brand": row["brand"],
                        "status": row["status"],
                        "base_price": row["base_price"],
                        "return_rate": row["return_rate"],
                        "rating": row["rating"],
                    },
                    "skus": [],
                }

            inventory_rows = conn.execute(
                "SELECT i.inventory_id, i.sku_id, i.warehouse_id, i.available_stock, "
                "i.locked_stock, i.safety_stock, i.restock_eta, "
                "w.warehouse_name, w.province, w.city "
                "FROM inventory i JOIN warehouses w ON i.warehouse_id = w.warehouse_id "
                "WHERE i.sku_id = ? ORDER BY w.warehouse_id",
                (row["sku_id"],),
            ).fetchall()
            products[product_key]["skus"].append(
                {
                    "sku": {
                        "sku_id": row["sku_id"],
                        "product_id": row["product_id"],
                        "color": row["color"],
                        "size_or_version": row["size_or_version"],
                        "price": row["price"],
                        "supports_7days_return": row["supports_7days_return"],
                        "warranty_months": row["warranty_months"],
                    },
                    "inventory": _rows_to_dicts(inventory_rows),
                }
            )

        return to_payload(
            "success",
            f"已查询到 {len(products)} 个商品、{len(rows)} 个 SKU 的库存信息。",
            {"products": list(products.values())},
        )
    finally:
        conn.close()


@tool
def query_after_sales_ticket(ticket_id: str = "", order_id: str = "") -> str:
    """查询售后工单状态、流转记录，以及关联的退款、换货、补偿和附件信息。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        if not ticket_id and not order_id:
            return to_payload(
                "failed",
                "请至少提供 ticket_id 或 order_id 中的一个。",
                {"ticket_id": ticket_id, "order_id": order_id},
            )

        if ticket_id and order_id:
            tickets = conn.execute(
                "SELECT t.*, c.customer_name, c.phone_last4, c.member_level "
                "FROM after_sales_tickets t JOIN customers c ON t.customer_id = c.customer_id "
                "WHERE t.ticket_id = ? AND t.order_id = ? ORDER BY t.created_at DESC",
                (ticket_id, order_id),
            ).fetchall()
        elif ticket_id:
            tickets = conn.execute(
                "SELECT t.*, c.customer_name, c.phone_last4, c.member_level "
                "FROM after_sales_tickets t JOIN customers c ON t.customer_id = c.customer_id "
                "WHERE t.ticket_id = ?",
                (ticket_id,),
            ).fetchall()
        else:
            tickets = conn.execute(
                "SELECT t.*, c.customer_name, c.phone_last4, c.member_level "
                "FROM after_sales_tickets t JOIN customers c ON t.customer_id = c.customer_id "
                "WHERE t.order_id = ? ORDER BY t.created_at DESC",
                (order_id,),
            ).fetchall()

        if not tickets:
            return to_payload(
                "not_found",
                "未找到相关售后工单。",
                {"ticket_id": ticket_id, "order_id": order_id},
            )

        bundles = [_ticket_bundle(conn, ticket) for ticket in tickets]
        return to_payload("success", f"共查询到 {len(bundles)} 个售后工单。", {"tickets": bundles})
    finally:
        conn.close()


@tool
def evaluate_refund_eligibility(order_id: str, issue_type: str) -> str:
    """基于订单状态、签收时间、商品退款属性和已有工单做退款资格预判断。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        order = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        if order is None:
            return to_payload("not_found", f"未找到订单 {order_id}。", {"order_id": order_id})

        order_dict = _row_to_dict(order)
        tickets = conn.execute(
            "SELECT * FROM after_sales_tickets WHERE order_id = ? ORDER BY created_at DESC",
            (order_id,),
        ).fetchall()
        active_tickets = [
            _row_to_dict(ticket)
            for ticket in tickets
            if ticket["status"] in _active_ticket_statuses()
        ]
        shipment = conn.execute(
            "SELECT * FROM shipments WHERE order_id = ? ORDER BY shipment_id DESC LIMIT 1",
            (order_id,),
        ).fetchone()
        items = conn.execute(
            "SELECT order_item_id, product_id, sku_id, product_name_snapshot, "
            "sku_snapshot, refund_eligible FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()

        order_status = order_dict["order_status"]
        after_sales_status = order_dict.get("after_sales_status") or "无"
        signed_at = shipment["signed_at"] if shipment else None
        signed_dt = _parse_dt(signed_at)
        days_since_signed = (datetime.now() - signed_dt).days if signed_dt else None
        has_refund_eligible_item = any(row["refund_eligible"] for row in items)

        eligible = True
        suggested_next_action = "create_after_sales_ticket"
        reason = "订单满足基础结构化条件，可继续创建售后工单进入人工审核。"

        if order_status in ("待支付", "已取消"):
            eligible = False
            suggested_next_action = "none"
            reason = "订单处于待支付或已取消状态，不可申请普通售后。"
        elif active_tickets:
            eligible = False
            suggested_next_action = "query_after_sales_ticket"
            reason = "该订单已有进行中的售后工单，建议先查询现有工单处理进度。"
        elif order_status == "待发货":
            if issue_type == "未发货退款":
                reason = "订单尚未发货，可申请未发货退款。"
            else:
                reason = "订单尚未发货，可创建售后工单由客服确认处理方式。"
        elif order_status in ("已发货", "运输中"):
            reason = "订单已发货但尚未签收，可创建售后工单跟进物流或异常场景。"
        elif order_status in ("已签收", "已完成"):
            if issue_type in ("质量问题", "物流破损", "包装破损", "漏液", "过敏反馈", "少件漏发"):
                reason = "已签收订单遇到质量、破损或少件类问题，可创建售后工单并补充凭证。"
            elif issue_type in ("七天无理由", "尺码不合适"):
                if not has_refund_eligible_item:
                    eligible = False
                    suggested_next_action = "manual_review"
                    reason = "订单商品标记为不支持无理由退款，可能需要人工审核。"
                elif days_since_signed is not None and days_since_signed > 7:
                    eligible = False
                    suggested_next_action = "manual_review"
                    reason = "订单签收已超过 7 天，无理由退款可能需要人工审核。"
                else:
                    reason = "订单商品支持退款且签收时间满足基础判断，可继续创建售后工单。"
            elif not has_refund_eligible_item:
                eligible = False
                suggested_next_action = "manual_review"
                reason = "订单商品存在不支持退款标记，该问题类型可能需要人工审核。"
        elif order_status in ("退款中", "退款成功"):
            eligible = False
            suggested_next_action = "query_after_sales_ticket"
            reason = "订单已处于退款流程或退款成功状态，建议查询售后或退款记录。"

        data = {
            "eligible": eligible,
            "reason": reason,
            "order_status": order_status,
            "after_sales_status": after_sales_status,
            "suggested_next_action": suggested_next_action,
            "signed_at": signed_at,
            "days_since_signed": days_since_signed,
            "has_refund_eligible_item": has_refund_eligible_item,
            "existing_active_tickets": active_tickets,
        }
        return to_payload("success", "已完成退款资格结构化预判断。", data)
    finally:
        conn.close()


@tool
def create_after_sales_ticket(
    order_id: str,
    issue_type: str,
    description: str,
    contact_phone: str,
) -> str:
    """创建售后工单，并写入初始工单流转记录。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        order = conn.execute(
            "SELECT o.*, c.customer_name, c.member_level FROM orders o "
            "JOIN customers c ON o.customer_id = c.customer_id "
            "WHERE o.order_id = ?",
            (order_id,),
        ).fetchone()
        if order is None:
            return to_payload("not_found", "订单不存在，无法创建售后工单。", {"order_id": order_id})

        if issue_type not in VALID_ISSUE_TYPES:
            return to_payload(
                "failed",
                "问题类型不在演示数据库支持范围内，请改用已有售后问题类型。",
                {"issue_type": issue_type, "valid_issue_types": list(VALID_ISSUE_TYPES)},
            )

        order_dict = _row_to_dict(order)
        if order_dict["order_status"] in ("待支付", "已取消"):
            return to_payload(
                "failed",
                "待支付或已取消订单不能创建普通售后工单。",
                {"order_id": order_id, "order_status": order_dict["order_status"]},
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        priority = _priority_for(issue_type, float(order_dict["order_total"]), order_dict["member_level"])
        assigned_to = _assigned_group_for(issue_type, order_dict["member_level"])
        sla = "12 小时内首次响应" if priority == "紧急" else (
            "24 小时内首次响应" if priority == "高" else "48 小时内首次响应"
        )

        conn.execute("BEGIN IMMEDIATE")
        ticket_id = _next_ticket_id(conn)
        conn.execute(
            "INSERT INTO after_sales_tickets (ticket_id, order_id, customer_id, issue_type, "
            "description, contact_phone, status, priority, assigned_to, created_at, sla) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ticket_id,
                order_id,
                order_dict["customer_id"],
                issue_type,
                description,
                contact_phone,
                "已创建",
                priority,
                assigned_to,
                now,
                sla,
            ),
        )
        conn.execute(
            "INSERT INTO ticket_events (ticket_id, event_time, operator_role, event_type, event_note) "
            "VALUES (?, ?, ?, ?, ?)",
            (ticket_id, now, "系统", "创建", f"工单已创建，客户提交售后申请：{issue_type}"),
        )
        conn.commit()

        ticket = conn.execute(
            "SELECT * FROM after_sales_tickets WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()
        return to_payload(
            "success",
            f"售后工单 {ticket_id} 已创建。",
            _ticket_bundle(conn, ticket),
        )
    except sqlite3.Error as exc:
        conn.rollback()
        return to_payload("failed", "数据库写入工单失败。", {"order_id": order_id, "error": str(exc)})
    finally:
        conn.close()


@tool
def query_refund_policy(issue_type: str, category: str = "通用") -> str:
    """查询退款或退换货规则；当前仍读取演示库中的 refund_rules 参考规则。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        rule = conn.execute(
            "SELECT * FROM refund_rules WHERE issue_type = ? AND category = ?",
            (issue_type, category),
        ).fetchone()
        if rule is None:
            rule = conn.execute(
                "SELECT * FROM refund_rules WHERE issue_type = ? ORDER BY category LIMIT 1",
                (issue_type,),
            ).fetchone()
        if rule is None:
            return to_payload(
                "not_found",
                "未找到对应退款规则，建议改用更具体的问题类型或交由 RAG 政策工具处理。",
                {"category": category, "issue_type": issue_type},
            )
        return to_payload("success", f"已查询到 {rule['issue_type']} 的退款规则。", _row_to_dict(rule))
    finally:
        conn.close()


@tool
def query_refund_policy_rag(
    issue_type: str,
    category: str = "通用",
    question: str = "",
    order_status: str = "",
    product_name: str = "",
) -> str:
    """基于本地 Markdown RAG 索引查询售后政策、凭证、时效和例外情况，并返回引用。"""
    result = query_refund_policy_rag_dict(
        issue_type=issue_type,
        category=category,
        question=question,
        order_status=order_status,
        product_name=product_name,
    )
    return to_payload(result["status"], result["message"], result["data"])


@tool
def query_shipment_tracking(order_id: str = "", tracking_no: str = "") -> str:
    """兼容旧工具：按订单号或快递单号查询物流轨迹详情。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        if order_id:
            shipment = conn.execute(
                "SELECT s.*, w.warehouse_name FROM shipments s "
                "LEFT JOIN warehouses w ON s.warehouse_id = w.warehouse_id "
                "WHERE s.order_id = ? ORDER BY s.shipment_id DESC LIMIT 1",
                (order_id,),
            ).fetchone()
        elif tracking_no:
            shipment = conn.execute(
                "SELECT s.*, w.warehouse_name FROM shipments s "
                "LEFT JOIN warehouses w ON s.warehouse_id = w.warehouse_id "
                "WHERE s.tracking_no = ? ORDER BY s.shipment_id DESC LIMIT 1",
                (tracking_no,),
            ).fetchone()
        else:
            shipment = None

        if shipment is None:
            return to_payload(
                "not_found",
                "未找到对应的物流信息。",
                {"order_id": order_id, "tracking_no": tracking_no},
            )

        shipment_dict = _row_to_dict(shipment)
        shipment_dict["events"] = _rows_to_dicts(
            conn.execute(
                "SELECT * FROM shipment_events WHERE shipment_id = ? ORDER BY event_time, event_id",
                (shipment_dict["shipment_id"],),
            ).fetchall()
        )
        return to_payload(
            "success",
            f"已查询到物流轨迹，共 {len(shipment_dict['events'])} 条记录。",
            shipment_dict,
        )
    finally:
        conn.close()


@tool
def query_customer_tickets(customer_phone: str = "", order_id: str = "") -> str:
    """兼容旧工具：查询客户或订单关联的售后工单及处理进度。"""
    conn = _get_conn()
    if conn is None:
        return _database_not_ready_payload()

    try:
        if order_id:
            tickets = conn.execute(
                "SELECT t.* FROM after_sales_tickets t WHERE t.order_id = ? ORDER BY t.created_at DESC",
                (order_id,),
            ).fetchall()
        elif customer_phone:
            tickets = conn.execute(
                "SELECT t.* FROM after_sales_tickets t "
                "JOIN customers c ON t.customer_id = c.customer_id "
                "WHERE t.contact_phone = ? OR c.phone_last4 = ? "
                "ORDER BY t.created_at DESC",
                (customer_phone, customer_phone[-4:]),
            ).fetchall()
        else:
            tickets = []

        if not tickets:
            return to_payload(
                "not_found",
                "未找到相关售后工单。",
                {"customer_phone": customer_phone, "order_id": order_id},
            )
        return to_payload(
            "success",
            f"共查询到 {len(tickets)} 个售后工单。",
            {"tickets": [_ticket_bundle(conn, ticket) for ticket in tickets]},
        )
    finally:
        conn.close()


tools = [
    query_order_status,
    query_product_inventory,
    query_after_sales_ticket,
    evaluate_refund_eligibility,
    create_after_sales_ticket,
    query_refund_policy_rag,
    query_refund_policy,
    query_shipment_tracking,
    query_customer_tickets,
]
