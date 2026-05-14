# Mock Data Model

当前 demo 使用本地 JSON 作为轻量 mock 数据层，模拟 4 张核心业务表：

## 1. orders.json

用于模拟订单主表与订单明细表的聚合结果，关键字段包括：

- `order_id`：订单号
- `customer`：用户信息，含姓名、手机号后四位、会员等级
- `order_status`：订单状态
- `after_sales_status`：售后状态
- `payment`：支付信息
- `delivery`：物流与收货信息
- `items`：订单商品列表
- `timeline`：订单时间线
- `created_at`：下单时间

## 2. products.json

用于模拟商品基础信息与库存信息，关键字段包括：

- `product_id`：商品编号
- `product_name`：商品名称
- `category`：品类
- `brand`：品牌
- `price`：标价
- `status`：商品销售状态
- `available_stock` / `locked_stock` / `safety_stock`：库存相关字段
- `warehouse` / `restock_eta`：仓储与补货字段
- `specs`：规格信息
- `sales_metrics`：销量、退货率、评分

## 3. refund_rules.json

用于模拟退款与售后规则表，关键字段包括：

- `rule_id`：规则编号
- `category`：适用品类
- `issue_type`：问题类型
- `rule_summary`：规则摘要
- `eligible_order_status`：适用订单状态
- `conditions`：申请条件
- `required_evidence`：所需凭证
- `processing_time`：处理时效
- `refund_scope`：退款范围

## 4. tickets.json

用于模拟售后工单表，关键字段包括：

- `ticket_id`：工单号
- `order_id`：关联订单号
- `issue_type`：问题类型
- `description`：问题描述
- `contact_phone`：联系电话
- `status`：处理状态
- `priority`：优先级
- `assigned_to`：处理组
- `latest_progress`：最近进度
- `created_at` / `sla`：创建时间与承诺时效

## 推荐实现方案

对于课程作业 demo，建议继续使用 JSON：

- 零部署成本
- 数据结构清晰，便于展示
- 容易手工修改和扩充

如果后续要加“多条件筛选”“统计报表”“工单流转记录”，再升级到 SQLite 更合适。
