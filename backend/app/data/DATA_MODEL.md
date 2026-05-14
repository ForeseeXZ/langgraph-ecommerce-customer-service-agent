# Demo E-Commerce Database — Data Model

演示数据库 `demo_ecommerce.sqlite` 是一个 SQLite 3 数据库，模拟中文电商平台的售后业务场景。

## 数据库概览

| 表名 | 记录数 | 用途 |
|---|---|---|
| customers | 5,000 | 客户主数据 |
| products | 864 | 商品 SPU |
| skus | 3,002 | 商品 SKU（颜色/规格） |
| warehouses | 8 | 仓库 |
| inventory | 7,519 | SKU 在各仓库的库存 |
| orders | 20,000 | 订单主表 |
| order_items | 52,229 | 订单明细 |
| payments | 19,218 | 支付记录 |
| shipments | 16,139 | 物流单 |
| shipment_events | 32,419 | 物流轨迹详情 |
| after_sales_tickets | 3,476 | 售后工单 |
| ticket_events | 10,995 | 工单流转记录 |
| refunds | 1,153 | 退款记录 |
| exchanges | 627 | 换货记录 |
| compensations | 933 | 补偿记录 |
| attachments | 4,218 | 凭证附件 |
| refund_rules | 12 | 退款规则（参考数据） |

另有独立 RAG 索引库 `rag_index.sqlite`，由 `backend/app/rag_docs/official/` 和 `backend/app/rag_docs/internal/` 下的 Markdown 文档重建，用于售后政策、凭证、时效和例外情况检索。

---

## 表结构说明

### 1. customers — 客户

| 字段 | 类型 | 说明 |
|---|---|---|
| customer_id | INTEGER PK | 自增主键 |
| customer_name | TEXT | 客户姓名 |
| phone_last4 | TEXT | 手机号后四位，用于身份校验 |
| member_level | TEXT | 会员等级：普通会员/银卡会员/金卡会员/黑卡会员 |
| province | TEXT | 省份 |
| city | TEXT | 城市 |
| registered_at | TEXT | 注册时间 |

**典型查询**：按 customer_id 查询客户信息；按 phone_last4 校验身份。

### 2. products — 商品 SPU

| 字段 | 类型 | 说明 |
|---|---|---|
| product_id | INTEGER PK | 自增主键 |
| product_name | TEXT | 商品名称 |
| category | TEXT | 品类：服饰/数码/家电/家居/美妆/母婴/运动/食品 |
| brand | TEXT | 品牌 |
| status | TEXT | 销售状态：在售/下架/缺货 |
| base_price | REAL | 基准价格 |
| return_rate | REAL | 退货率（0-0.15） |
| rating | REAL | 评分（3.5-5.0） |

**典型查询**：按品类筛选商品；按商品名称模糊搜索。

### 3. skus — 商品 SKU

| 字段 | 类型 | 说明 |
|---|---|---|
| sku_id | INTEGER PK | 自增主键 |
| product_id | INTEGER FK | 关联 products |
| color | TEXT | 颜色 |
| size_or_version | TEXT | 尺码或版本 |
| price | REAL | SKU 实际售价 |
| supports_7days_return | INTEGER | 是否支持七天无理由退货 |
| warranty_months | INTEGER | 保修月数（数码/家电类） |

**典型查询**：按 product_id 查所有 SKU；按 sku_id 查价格。

### 4. warehouses — 仓库

| 字段 | 类型 | 说明 |
|---|---|---|
| warehouse_id | INTEGER PK | 自增主键 |
| warehouse_name | TEXT | 仓库名称（如"华东仓(杭州)"） |
| province | TEXT | 所在省 |
| city | TEXT | 所在市 |

8 个仓库覆盖全国七大区域：华东、华南、华北、华中、西南、西北、东北、华东二仓。

### 5. inventory — 库存

| 字段 | 类型 | 说明 |
|---|---|---|
| inventory_id | INTEGER PK | 自增主键 |
| sku_id | INTEGER FK | 关联 skus |
| warehouse_id | INTEGER FK | 关联 warehouses |
| available_stock | INTEGER | 可用库存 |
| locked_stock | INTEGER | 锁定库存（待发货订单占用） |
| safety_stock | INTEGER | 安全库存阈值 |
| restock_eta | TEXT | 预计补货日期（当库存低于安全库存时） |

UNIQUE(sku_id, warehouse_id)

**典型查询**：按 SKU 查各仓库存；按 warehouse_id 查仓库所有 SKU 库存；筛选缺货商品（available < safety）。

### 6. orders — 订单

| 字段 | 类型 | 说明 |
|---|---|---|
| order_id | TEXT PK | 订单号，格式 SO+日期+序号 |
| customer_id | INTEGER FK | 关联 customers |
| order_status | TEXT | 待支付/待发货/已发货/运输中/已签收/已完成/已取消/退款中/退款成功 |
| after_sales_status | TEXT | 售后状态：无/部分售后/全部售后/售后完结 |
| order_total | REAL | 订单总额 |
| paid_amount | REAL | 实付金额 |
| coupon_amount | REAL | 优惠券金额 |
| shipping_fee | REAL | 运费 |
| created_at | TEXT | 下单时间 |
| paid_at | TEXT | 支付时间 |
| completed_at | TEXT | 完成时间 |

**典型查询**：按 order_id 查订单详情；按 customer_id 查客户所有订单；按 order_status 筛选。

### 7. order_items — 订单明细

| 字段 | 类型 | 说明 |
|---|---|---|
| order_item_id | INTEGER PK | 自增主键 |
| order_id | TEXT FK | 关联 orders |
| product_id | INTEGER FK | 关联 products |
| sku_id | INTEGER FK | 关联 skus |
| product_name_snapshot | TEXT | 下单时的商品名称快照 |
| sku_snapshot | TEXT | 下单时的 SKU 规格快照 |
| unit_price | REAL | 下单时单价 |
| quantity | INTEGER | 购买数量 |
| refund_eligible | INTEGER | 是否可退款 |

### 8. payments — 支付

| 字段 | 类型 | 说明 |
|---|---|---|
| payment_id | INTEGER PK | 自增主键 |
| order_id | TEXT FK | 关联 orders |
| payment_method | TEXT | 微信支付/支付宝/银行卡/花呗/白条/货到付款 |
| payment_status | TEXT | 待支付/支付成功/支付失败/已退款/部分退款 |
| transaction_no | TEXT | 第三方交易流水号 |
| paid_amount | REAL | 支付金额 |
| paid_at | TEXT | 支付时间 |
| refunded_amount | REAL | 已退款金额 |

**典型查询**：按 order_id 查支付状态；按 payment_status 筛选。

### 9. shipments — 物流

| 字段 | 类型 | 说明 |
|---|---|---|
| shipment_id | INTEGER PK | 自增主键 |
| order_id | TEXT FK | 关联 orders |
| warehouse_id | INTEGER FK | 发货仓库 |
| shipping_company | TEXT | 快递公司 |
| tracking_no | TEXT | 快递单号 |
| delivery_status | TEXT | 待发货/已发货/运输中/已签收/派送中/异常 |
| estimated_delivery | TEXT | 预计送达日期 |
| shipping_address | TEXT | 收货地址 |
| shipped_at | TEXT | 发货时间 |
| signed_at | TEXT | 签收时间 |

### 10. shipment_events — 物流轨迹

| 字段 | 类型 | 说明 |
|---|---|---|
| event_id | INTEGER PK | 自增主键 |
| shipment_id | INTEGER FK | 关联 shipments |
| event_time | TEXT | 事件时间 |
| event_location | TEXT | 事件发生地 |
| event_description | TEXT | 事件描述 |

### 11. after_sales_tickets — 售后工单

| 字段 | 类型 | 说明 |
|---|---|---|
| ticket_id | TEXT PK | 工单号，格式 AS+日期+序号 |
| order_id | TEXT FK | 关联 orders |
| customer_id | INTEGER FK | 关联 customers |
| issue_type | TEXT | 问题类型（10+ 种） |
| description | TEXT | 问题描述 |
| contact_phone | TEXT | 联系电话 |
| status | TEXT | 工单状态（10 种状态） |
| priority | TEXT | 低/中/高/紧急 |
| assigned_to | TEXT | 处理组 |
| created_at | TEXT | 创建时间 |
| closed_at | TEXT | 关闭时间 |
| sla | TEXT | 服务时效承诺 |

### 12. ticket_events — 工单流转记录

| 字段 | 类型 | 说明 |
|---|---|---|
| event_id | INTEGER PK | 自增主键 |
| ticket_id | TEXT FK | 关联 after_sales_tickets |
| event_time | TEXT | 事件时间 |
| operator_role | TEXT | 操作角色：系统/客服/审核专员/仓库人员/财务专员/客户/主管 |
| event_type | TEXT | 事件类型（17 种） |
| event_note | TEXT | 事件备注 |

### 13. refunds — 退款

| 字段 | 类型 | 说明 |
|---|---|---|
| refund_id | INTEGER PK | 自增主键 |
| ticket_id | TEXT FK | 关联 after_sales_tickets |
| order_id | TEXT FK | 关联 orders |
| refund_status | TEXT | 待审核/审核通过/待退款/退款中/已退款/拒绝退款/退款失败 |
| refund_amount | REAL | 退款金额（不超过订单实付） |
| refund_reason | TEXT | 退款原因 |
| requested_at | TEXT | 申请时间 |
| approved_at | TEXT | 审批时间 |
| refunded_at | TEXT | 退款到账时间 |

### 14. exchanges — 换货

| 字段 | 类型 | 说明 |
|---|---|---|
| exchange_id | INTEGER PK | 自增主键 |
| ticket_id | TEXT FK | 关联 after_sales_tickets |
| order_id | TEXT FK | 关联 orders |
| old_sku_id | INTEGER FK | 原 SKU |
| new_sku_id | INTEGER FK | 新 SKU |
| exchange_status | TEXT | 待寄回/待验收/换货中/已发出/已签收/已完结 |
| new_tracking_no | TEXT | 新快递单号 |
| created_at | TEXT | 创建时间 |

### 15. compensations — 补偿

| 字段 | 类型 | 说明 |
|---|---|---|
| compensation_id | INTEGER PK | 自增主键 |
| ticket_id | TEXT FK | 关联 after_sales_tickets |
| compensation_type | TEXT | 优惠券/现金补偿/积分补偿/赠品/免运费/其他 |
| amount | REAL | 补偿金额/数量 |
| description | TEXT | 补偿说明 |
| issued_at | TEXT | 发放时间 |

### 16. attachments — 凭证附件

| 字段 | 类型 | 说明 |
|---|---|---|
| attachment_id | INTEGER PK | 自增主键 |
| ticket_id | TEXT FK | 关联 after_sales_tickets |
| attachment_type | TEXT | 图片/视频/文档/截图/其他 |
| file_name | TEXT | 文件名 |
| mock_url | TEXT | 模拟访问路径 |
| uploaded_at | TEXT | 上传时间 |

### 17. refund_rules — 退款规则

| 字段 | 类型 | 说明 |
|---|---|---|
| rule_id | TEXT PK | 规则编号 |
| category | TEXT | 适用品类 |
| issue_type | TEXT | 问题类型 |
| rule_summary | TEXT | 规则摘要 |
| eligible_order_status | TEXT | 适用的订单状态 |
| conditions | TEXT | 申请条件 |
| required_evidence | TEXT | 所需凭证 |
| processing_time | TEXT | 处理时效 |
| refund_scope | TEXT | 退款范围 |

---

## RAG 索引库

`backend/app/data/rag_index.sqlite` 是可重建的本地政策检索索引，不依赖联网服务或外部模型。

### rag_documents — 文档元数据

| 字段 | 类型 | 说明 |
|---|---|---|
| doc_id | TEXT PK | front matter 中的文档编号 |
| title | TEXT | 文档标题 |
| source_type | TEXT | `official` 或 `internal_sop` |
| source_url | TEXT | 官方来源 URL 或 `local://...` |
| category | TEXT | 适用品类或业务分类 |
| issue_types | TEXT | JSON 数组，适用的问题类型 |
| authority_level | TEXT | `high` / `medium` 等权威等级 |
| path | TEXT | 相对 `rag_docs` 的 Markdown 路径 |

### rag_chunks — 检索 chunk

| 字段 | 类型 | 说明 |
|---|---|---|
| chunk_id | TEXT PK | `doc_id_0001` 形式的可引用 chunk 编号 |
| doc_id | TEXT FK | 关联 `rag_documents` |
| title | TEXT | 文档标题 |
| section_title | TEXT | Markdown 小节标题 |
| content | TEXT | chunk 正文，约 500-800 中文字以内 |
| source_type | TEXT | 来源类型 |
| source_url | TEXT | 来源 URL |
| category | TEXT | 分类 |
| issue_types | TEXT | JSON 数组 |
| authority_level | TEXT | 权威等级 |

### rag_chunks_fts — FTS5 检索表

字段包括 `chunk_id`、`content`、`title`、`section_title`、`issue_types`、`category`。当前工具同时使用本地关键词打分，确保 SQLite FTS5 不可用时仍能完成课程作业级检索。

---

## 业务关系

```
customers ──< orders ──< order_items >── products ──< skus >── inventory >── warehouses
                 │
                 ├── payments
                 ├── shipments ──< shipment_events
                 └── after_sales_tickets ──< ticket_events
                          │
                          ├── refunds
                          ├── exchanges
                          ├── compensations
                          └── attachments
```

---

## 关键查询场景

### 查询订单全貌（订单+客户+支付+物流+商品）
```sql
SELECT o.*, c.customer_name, c.member_level,
       p.payment_method, p.payment_status, p.paid_amount,
       s.shipping_company, s.tracking_no, s.delivery_status
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN payments p ON o.order_id = p.order_id
LEFT JOIN shipments s ON o.order_id = s.order_id
WHERE o.order_id = 'SO20260514000001';
```

### 查询商品库存（按 SKU 汇总各仓）
```sql
SELECT s.sku_id, s.color, s.size_or_version, s.price,
       w.warehouse_name, i.available_stock, i.locked_stock, i.safety_stock
FROM skus s
JOIN inventory i ON s.sku_id = i.sku_id
JOIN warehouses w ON i.warehouse_id = w.warehouse_id
WHERE s.product_id = 1;
```

### 查询订单已有售后工单
```sql
SELECT t.*, COUNT(te.event_id) AS event_count
FROM after_sales_tickets t
LEFT JOIN ticket_events te ON t.ticket_id = te.ticket_id
WHERE t.order_id = 'SO20260514000001'
GROUP BY t.ticket_id;
```

### 创建售后工单
```sql
INSERT INTO after_sales_tickets (ticket_id, order_id, customer_id, issue_type,
    description, contact_phone, status, priority, assigned_to, created_at, sla)
VALUES ('AS20260514000001', 'SO20260514000001', 1, '质量问题',
    '商品屏幕有坏点', '13812345678', '已创建', '高', '售后质检组', datetime('now'), '24 小时内首次响应');
```

### 查询工单流转记录
```sql
SELECT te.* FROM ticket_events te
WHERE te.ticket_id = 'AS20260514000001'
ORDER BY te.event_time;
```

### 查询退款记录
```sql
SELECT r.*, t.issue_type, t.status AS ticket_status
FROM refunds r
JOIN after_sales_tickets t ON r.ticket_id = t.ticket_id
WHERE r.order_id = 'SO20260514000001';
```

---

## 数据生成

使用 `backend/scripts/generate_demo_db.py` 生成数据库，固定随机种子 `20260514`，确保每次运行生成完全相同的数据库。

```bash
cd backend
python scripts/generate_demo_db.py
```

生成后可运行验收脚本：

```bash
cd backend
python scripts/check_demo_db.py --skip-tools
```

如已安装后端 LangChain 依赖，可去掉 `--skip-tools` 同时验证工具调用链路。

构建并验证 RAG 索引：

```bash
cd backend
python scripts/build_rag_index.py
python scripts/check_rag.py
```
