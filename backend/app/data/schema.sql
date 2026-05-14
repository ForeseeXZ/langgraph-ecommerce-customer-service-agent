-- 中文电商售后 Agent 演示数据库 Schema
-- 目标: SQLite 3.x

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. customers — 客户
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT    NOT NULL,
    phone_last4   TEXT    NOT NULL,
    member_level  TEXT    NOT NULL CHECK (member_level IN ('普通会员','银卡会员','金卡会员','黑卡会员')),
    province      TEXT    NOT NULL,
    city          TEXT    NOT NULL,
    registered_at TEXT    NOT NULL
);

-- ============================================================
-- 2. products — 商品 SPU
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT    NOT NULL,
    category     TEXT    NOT NULL CHECK (category IN ('服饰','数码','家电','家居','美妆','母婴','运动','食品')),
    brand        TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT '在售' CHECK (status IN ('在售','下架','缺货')),
    base_price   REAL    NOT NULL,
    return_rate  REAL    DEFAULT 0,
    rating       REAL    DEFAULT 5.0
);

-- ============================================================
-- 3. skus — 商品 SKU
-- ============================================================
CREATE TABLE IF NOT EXISTS skus (
    sku_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id            INTEGER NOT NULL REFERENCES products(product_id),
    color                 TEXT,
    size_or_version       TEXT,
    price                 REAL    NOT NULL,
    supports_7days_return INTEGER NOT NULL DEFAULT 1,
    warranty_months       INTEGER DEFAULT 0
);

-- ============================================================
-- 4. warehouses — 仓库
-- ============================================================
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_name TEXT    NOT NULL,
    province       TEXT    NOT NULL,
    city           TEXT    NOT NULL
);

-- ============================================================
-- 5. inventory — 库存
-- ============================================================
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id          INTEGER NOT NULL REFERENCES skus(sku_id),
    warehouse_id    INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    available_stock INTEGER NOT NULL DEFAULT 0,
    locked_stock    INTEGER NOT NULL DEFAULT 0,
    safety_stock    INTEGER NOT NULL DEFAULT 0,
    restock_eta     TEXT,
    UNIQUE(sku_id, warehouse_id)
);

-- ============================================================
-- 6. orders — 订单
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    order_id            TEXT PRIMARY KEY,
    customer_id         INTEGER NOT NULL REFERENCES customers(customer_id),
    order_status        TEXT    NOT NULL CHECK (order_status IN ('待支付','待发货','已发货','运输中','已签收','已完成','已取消','退款中','退款成功')),
    after_sales_status  TEXT    DEFAULT '无' CHECK (after_sales_status IN ('无','部分售后','全部售后','售后完结')),
    order_total         REAL    NOT NULL,
    paid_amount         REAL    NOT NULL,
    coupon_amount       REAL    DEFAULT 0,
    shipping_fee        REAL    DEFAULT 0,
    created_at          TEXT    NOT NULL,
    paid_at             TEXT,
    completed_at        TEXT
);

-- ============================================================
-- 7. order_items — 订单明细
-- ============================================================
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id              TEXT    NOT NULL REFERENCES orders(order_id),
    product_id            INTEGER NOT NULL REFERENCES products(product_id),
    sku_id                INTEGER NOT NULL REFERENCES skus(sku_id),
    product_name_snapshot TEXT    NOT NULL,
    sku_snapshot          TEXT    NOT NULL,
    unit_price            REAL    NOT NULL,
    quantity              INTEGER NOT NULL DEFAULT 1,
    refund_eligible       INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- 8. payments — 支付
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        TEXT    NOT NULL REFERENCES orders(order_id),
    payment_method  TEXT    NOT NULL CHECK (payment_method IN ('微信支付','支付宝','银行卡','花呗','白条','货到付款')),
    payment_status  TEXT    NOT NULL CHECK (payment_status IN ('待支付','支付成功','支付失败','已退款','部分退款')),
    transaction_no  TEXT,
    paid_amount     REAL    NOT NULL,
    paid_at         TEXT,
    refunded_amount REAL    DEFAULT 0
);

-- ============================================================
-- 9. shipments — 物流
-- ============================================================
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            TEXT    NOT NULL REFERENCES orders(order_id),
    warehouse_id        INTEGER REFERENCES warehouses(warehouse_id),
    shipping_company    TEXT,
    tracking_no         TEXT,
    delivery_status     TEXT    NOT NULL CHECK (delivery_status IN ('待发货','已发货','运输中','已签收','派送中','异常')),
    estimated_delivery  TEXT,
    shipping_address    TEXT    NOT NULL,
    shipped_at          TEXT,
    signed_at           TEXT
);

-- ============================================================
-- 10. shipment_events — 物流轨迹
-- ============================================================
CREATE TABLE IF NOT EXISTS shipment_events (
    event_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id       INTEGER NOT NULL REFERENCES shipments(shipment_id),
    event_time        TEXT    NOT NULL,
    event_location    TEXT    NOT NULL,
    event_description TEXT    NOT NULL
);

-- ============================================================
-- 11. after_sales_tickets — 售后工单
-- ============================================================
CREATE TABLE IF NOT EXISTS after_sales_tickets (
    ticket_id      TEXT PRIMARY KEY,
    order_id       TEXT    NOT NULL REFERENCES orders(order_id),
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    issue_type     TEXT    NOT NULL CHECK (issue_type IN ('七天无理由','质量问题','尺码不合适','物流破损','少件漏发','未发货退款','保修咨询','发票问题','地址修改','催发货','安装问题','配件缺失','包装破损','漏液','过敏反馈')),
    description    TEXT    NOT NULL,
    contact_phone  TEXT,
    status         TEXT    NOT NULL DEFAULT '已创建' CHECK (status IN ('已创建','待补充凭证','审核中','待寄回','仓库验收中','退款中','换货处理中','已完结','已拒绝','已取消')),
    priority       TEXT    NOT NULL DEFAULT '中' CHECK (priority IN ('低','中','高','紧急')),
    assigned_to    TEXT,
    created_at     TEXT    NOT NULL,
    closed_at      TEXT,
    sla            TEXT
);

-- ============================================================
-- 12. ticket_events — 工单流转记录
-- ============================================================
CREATE TABLE IF NOT EXISTS ticket_events (
    event_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id     TEXT    NOT NULL REFERENCES after_sales_tickets(ticket_id),
    event_time    TEXT    NOT NULL,
    operator_role TEXT    NOT NULL CHECK (operator_role IN ('系统','客服','审核专员','仓库人员','财务专员','客户','主管')),
    event_type    TEXT    NOT NULL CHECK (event_type IN ('创建','提交凭证','审核通过','审核驳回','要求补充凭证','分配处理人','转交','备注','完结','拒绝','取消','待寄回通知','仓库验收','退款发起','退款完成','换货发出','补偿发放')),
    event_note    TEXT
);

-- ============================================================
-- 13. refunds — 退款
-- ============================================================
CREATE TABLE IF NOT EXISTS refunds (
    refund_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id     TEXT    NOT NULL REFERENCES after_sales_tickets(ticket_id),
    order_id      TEXT    NOT NULL REFERENCES orders(order_id),
    refund_status TEXT    NOT NULL CHECK (refund_status IN ('待审核','审核通过','待退款','退款中','已退款','拒绝退款','退款失败')),
    refund_amount REAL    NOT NULL,
    refund_reason TEXT    NOT NULL,
    requested_at  TEXT    NOT NULL,
    approved_at   TEXT,
    refunded_at   TEXT
);

-- ============================================================
-- 14. exchanges — 换货
-- ============================================================
CREATE TABLE IF NOT EXISTS exchanges (
    exchange_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id       TEXT    NOT NULL REFERENCES after_sales_tickets(ticket_id),
    order_id        TEXT    NOT NULL REFERENCES orders(order_id),
    old_sku_id      INTEGER NOT NULL REFERENCES skus(sku_id),
    new_sku_id      INTEGER NOT NULL REFERENCES skus(sku_id),
    exchange_status TEXT    NOT NULL CHECK (exchange_status IN ('待寄回','待验收','换货中','已发出','已签收','已完结')),
    new_tracking_no TEXT,
    created_at      TEXT    NOT NULL
);

-- ============================================================
-- 15. compensations — 补偿
-- ============================================================
CREATE TABLE IF NOT EXISTS compensations (
    compensation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id         TEXT    NOT NULL REFERENCES after_sales_tickets(ticket_id),
    compensation_type TEXT    NOT NULL CHECK (compensation_type IN ('优惠券','现金补偿','积分补偿','赠品','免运费','其他')),
    amount            REAL,
    description       TEXT,
    issued_at         TEXT    NOT NULL
);

-- ============================================================
-- 16. attachments — 凭证附件
-- ============================================================
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id       TEXT REFERENCES after_sales_tickets(ticket_id),
    attachment_type TEXT NOT NULL CHECK (attachment_type IN ('图片','视频','文档','截图','其他')),
    file_name       TEXT NOT NULL,
    mock_url        TEXT,
    uploaded_at     TEXT NOT NULL
);

-- ============================================================
-- 17. refund_rules — 退款规则（参考数据）
-- ============================================================
CREATE TABLE IF NOT EXISTS refund_rules (
    rule_id               TEXT PRIMARY KEY,
    category              TEXT    NOT NULL,
    issue_type            TEXT    NOT NULL,
    rule_summary          TEXT    NOT NULL,
    eligible_order_status TEXT,
    conditions            TEXT,
    required_evidence     TEXT,
    processing_time       TEXT,
    refund_scope          TEXT
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_skus_product       ON skus(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_sku      ON inventory(sku_id);
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer     ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status       ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_created      ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order   ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_sku     ON order_items(sku_id);
CREATE INDEX IF NOT EXISTS idx_payments_order      ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_order     ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipment_events_ship ON shipment_events(shipment_id);
CREATE INDEX IF NOT EXISTS idx_tickets_order       ON after_sales_tickets(order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_customer    ON after_sales_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status      ON after_sales_tickets(status);
CREATE INDEX IF NOT EXISTS idx_ticket_events_ticket ON ticket_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_refunds_ticket       ON refunds(ticket_id);
CREATE INDEX IF NOT EXISTS idx_refunds_order        ON refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_exchanges_ticket     ON exchanges(ticket_id);
CREATE INDEX IF NOT EXISTS idx_compensations_ticket ON compensations(ticket_id);
CREATE INDEX IF NOT EXISTS idx_attachments_ticket   ON attachments(ticket_id);
CREATE INDEX IF NOT EXISTS idx_refund_rules_cat_issue ON refund_rules(category, issue_type);
