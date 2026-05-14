import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
PRODUCTS_FILE = DATA_DIR / "products.json"
REFUND_RULES_FILE = DATA_DIR / "refund_rules.json"
TICKETS_FILE = DATA_DIR / "tickets.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
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


@tool
def query_order_status(order_id: str, phone_last4: str = "") -> str:
    """查询订单状态、物流信息和预计送达时间。适用于用户咨询发货进度、签收状态和物流单号。"""
    orders = load_json(ORDERS_FILE)
    order = next((item for item in orders if item["order_id"] == order_id), None)

    if order is None:
        return to_payload("not_found", f"未找到订单 {order_id}", {"order_id": order_id})

    if phone_last4 and order["customer"]["phone_last4"] != phone_last4:
        return to_payload(
            "forbidden",
            "手机号后四位校验失败，请确认后再查询。",
            {"order_id": order_id},
        )

    return to_payload("success", f"已查询到订单 {order_id} 的售后信息。", order)


@tool
def query_product_inventory(product_id: str = "", product_name: str = "") -> str:
    """查询商品库存、锁定库存、仓库和补货时间。适用于用户咨询是否有货、何时补货。"""
    products = load_json(PRODUCTS_FILE)
    product = next(
        (
            item
            for item in products
            if (product_id and item["product_id"] == product_id)
            or (product_name and product_name in item["product_name"])
        ),
        None,
    )

    if product is None:
        return to_payload(
            "not_found",
            "未找到对应商品，请提供更准确的商品编号或商品名称。",
            {"product_id": product_id, "product_name": product_name},
        )

    return to_payload("success", f"已查询到商品 {product['product_name']} 的库存信息。", product)


@tool
def query_refund_policy(issue_type: str, category: str = "通用") -> str:
    """查询退款或退换货规则。适用于用户咨询七天无理由、质量问题、尺码不合适等售后政策。"""
    rules = load_json(REFUND_RULES_FILE)
    rule = next(
        (
            item
            for item in rules
            if item["issue_type"] == issue_type and item["category"] == category
        ),
        None,
    )

    if rule is None:
        rule = next((item for item in rules if item["issue_type"] == issue_type), None)

    if rule is None:
        return to_payload(
            "not_found",
            "未找到对应退款规则，请改用更具体的问题类型。",
            {"category": category, "issue_type": issue_type},
        )

    return to_payload("success", f"已查询到 {rule['issue_type']} 的退款规则。", rule)


@tool
def create_after_sales_ticket(
    order_id: str,
    issue_type: str,
    description: str,
    contact_phone: str,
) -> str:
    """创建售后工单。适用于用户需要登记质量问题、退款申请、补发或人工跟进。"""
    orders = load_json(ORDERS_FILE)
    order = next((item for item in orders if item["order_id"] == order_id), None)
    if order is None:
        return to_payload("not_found", "订单不存在，无法创建售后工单。", {"order_id": order_id})

    tickets = load_json(TICKETS_FILE)
    ticket_id = f"AS{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ticket = {
        "ticket_id": ticket_id,
        "order_id": order_id,
        "issue_type": issue_type,
        "description": description,
        "contact_phone": contact_phone,
        "status": "已创建",
        "priority": "中",
        "assigned_to": "售后服务组",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sla": "24 小时内首次响应",
        "latest_progress": "工单已进入待分配队列",
    }
    tickets.append(ticket)
    dump_json(TICKETS_FILE, tickets)

    return to_payload("success", f"售后工单 {ticket_id} 已创建。", ticket)


tools = [
    query_order_status,
    query_product_inventory,
    query_refund_policy,
    create_after_sales_ticket,
]
