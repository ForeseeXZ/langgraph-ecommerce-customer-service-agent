"use client";

import { useAssistantToolUI } from "@assistant-ui/react";
import type { ReactNode } from "react";

import { InventoryTable } from "@/components/assistant/InventoryTable";
import { OrderCard } from "@/components/assistant/OrderCard";
import { RefundCard } from "@/components/assistant/RefundCard";
import { TicketCard } from "@/components/assistant/TicketCard";
import { ToolResultCard } from "@/components/assistant/ToolResultCard";
import type { ToolCardConfig } from "@/components/assistant/types";
import {
  arrayLength,
  firstRestockEta,
  getPath,
  inventoryTotal,
  isRecord,
  parseToolResult,
  skuSpec,
  yesNo,
} from "@/components/assistant/toolResultUtils";

const TOOL_CARDS: ToolCardConfig[] = [
  {
    toolName: "query_order_status",
    title: "订单状态查询",
    fields: [
      { label: "订单号", path: "order.order_id" },
      { label: "订单状态", path: "order.order_status" },
      { label: "支付状态", path: "payment.payment_status" },
      { label: "物流公司", path: "shipment.shipping_company" },
      { label: "物流单号", path: "shipment.tracking_no" },
      { label: "配送状态", path: "shipment.delivery_status" },
      { label: "预计送达", path: "shipment.estimated_delivery" },
      { label: "售后工单数", value: (data) => arrayLength(data, "after_sales_tickets") },
    ],
  },
  {
    toolName: "query_product_inventory",
    title: "商品库存查询",
    fields: [
      { label: "商品编号", path: "products.0.product.product_id" },
      { label: "商品名称", path: "products.0.product.product_name" },
      { label: "品类", path: "products.0.product.category" },
      { label: "SKU 编号", path: "products.0.skus.0.sku.sku_id" },
      { label: "规格", value: (data) => skuSpec(data) },
      { label: "仓库数", value: (data) => arrayLength(data, "products.0.skus.0.inventory") },
      { label: "总可用库存", value: (data) => inventoryTotal(data, "available_stock") },
      { label: "最近补货", value: (data) => firstRestockEta(data) },
    ],
  },
  {
    toolName: "evaluate_refund_eligibility",
    title: "退款资格预判断",
    fields: [
      { label: "是否可继续", value: (data) => yesNo(getPath(data, "eligible")) },
      { label: "订单状态", path: "order_status" },
      { label: "售后状态", path: "after_sales_status" },
      { label: "建议动作", path: "suggested_next_action" },
      { label: "签收时间", path: "signed_at" },
      { label: "签收天数", path: "days_since_signed" },
      { label: "判断原因", path: "reason" },
    ],
  },
  {
    toolName: "query_after_sales_ticket",
    title: "售后工单查询",
    fields: [
      { label: "工单编号", path: "tickets.0.ticket.ticket_id" },
      { label: "订单号", path: "tickets.0.ticket.order_id" },
      { label: "问题类型", path: "tickets.0.ticket.issue_type" },
      { label: "工单状态", path: "tickets.0.ticket.status" },
      { label: "优先级", path: "tickets.0.ticket.priority" },
      { label: "处理组", path: "tickets.0.ticket.assigned_to" },
      { label: "流转记录", value: (data) => arrayLength(data, "tickets.0.events") },
      { label: "退款记录", value: (data) => arrayLength(data, "tickets.0.refunds") },
    ],
  },
  {
    toolName: "create_after_sales_ticket",
    title: "售后工单创建",
    fields: [
      { label: "工单编号", path: "ticket.ticket_id" },
      { label: "订单号", path: "ticket.order_id" },
      { label: "问题类型", path: "ticket.issue_type" },
      { label: "工单状态", path: "ticket.status" },
      { label: "优先级", path: "ticket.priority" },
      { label: "处理组", path: "ticket.assigned_to" },
      { label: "联系电话", path: "ticket.contact_phone" },
      { label: "响应承诺", path: "ticket.sla" },
    ],
  },
  {
    toolName: "query_refund_policy",
    title: "退款规则查询",
    fields: [
      { label: "适用品类", path: "category" },
      { label: "问题类型", path: "issue_type" },
      { label: "适用订单状态", path: "eligible_order_status" },
      { label: "处理时效", path: "processing_time" },
      { label: "退款范围", path: "refund_scope" },
      { label: "所需凭证", path: "required_evidence" },
      { label: "规则摘要", path: "rule_summary" },
    ],
  },
  {
    toolName: "query_refund_policy_rag",
    title: "RAG 政策检索",
    fields: [
      { label: "问题类型", path: "issue_type" },
      { label: "适用品类", path: "category" },
      { label: "处理时效", path: "processing_time" },
      { label: "所需凭证", path: "required_evidence" },
      { label: "限制条件", path: "limitations" },
      { label: "引用数量", value: (data) => arrayLength(data, "citations") },
      { label: "摘要", path: "answer" },
    ],
  },
  {
    toolName: "query_shipment_tracking",
    title: "物流轨迹查询",
    fields: [
      { label: "订单号", path: "order_id" },
      { label: "物流公司", path: "shipping_company" },
      { label: "物流单号", path: "tracking_no" },
      { label: "配送状态", path: "delivery_status" },
      { label: "预计送达", path: "estimated_delivery" },
      { label: "轨迹条数", value: (data) => arrayLength(data, "events") },
    ],
  },
  {
    toolName: "query_customer_tickets",
    title: "客户工单查询",
    fields: [
      { label: "工单数量", value: (data) => arrayLength(data, "tickets") },
      { label: "最近工单", path: "tickets.0.ticket.ticket_id" },
      { label: "订单号", path: "tickets.0.ticket.order_id" },
      { label: "问题类型", path: "tickets.0.ticket.issue_type" },
      { label: "工单状态", path: "tickets.0.ticket.status" },
    ],
  },
];

const SPECIALIZED_RENDERERS: Partial<Record<string, (data: unknown) => ReactNode>> = {
  query_order_status: (data) => <OrderCard data={data} />,
  query_product_inventory: (data) => <InventoryTable data={data} />,
  evaluate_refund_eligibility: (data) => <RefundCard data={data} />,
  query_after_sales_ticket: (data) => <TicketCard data={data} />,
  create_after_sales_ticket: (data) => <TicketCard data={data} />,
  query_customer_tickets: (data) => <TicketCard data={data} />,
  query_shipment_tracking: (data) => (
    <OrderCard data={{ shipment: data, shipment_events: getPath(data, "events") }} />
  ),
};

export function ToolUIs() {
  return (
    <>
      {TOOL_CARDS.map((config) => {
        const specializedRenderer = SPECIALIZED_RENDERERS[config.toolName];

        return specializedRenderer ? (
          <SpecializedToolRegistration
            key={config.toolName}
            config={config}
            renderCard={specializedRenderer}
          />
        ) : (
          <ToolRegistration key={config.toolName} config={config} />
        );
      })}
    </>
  );
}

function ToolRegistration({ config }: { config: ToolCardConfig }) {
  useAssistantToolUI({
    toolName: config.toolName,
    render: ({ result }) => (
      <ToolResultCard title={config.title} result={result} fields={config.fields} />
    ),
  });

  return null;
}

function SpecializedToolRegistration({
  config,
  renderCard,
}: {
  config: ToolCardConfig;
  renderCard: (data: unknown) => ReactNode;
}) {
  useAssistantToolUI({
    toolName: config.toolName,
    render: ({ result }) => {
      const payload = parseToolResult(result);
      const data = payload.data;

      if (!canRenderSpecialized(config.toolName, payload.status, data)) {
        return <ToolResultCard title={config.title} result={result} fields={config.fields} />;
      }

      return renderCard(data);
    },
  });

  return null;
}

function canRenderSpecialized(toolName: string, status: string | undefined, data: unknown): boolean {
  if (status && status !== "success") return false;
  if (!isRecord(data)) return false;

  switch (toolName) {
    case "query_order_status":
      return isRecord(data.order) || isRecord(data.shipment);
    case "query_shipment_tracking":
      return Boolean(data.tracking_no || data.shipping_company || hasArray(data.events));
    case "query_product_inventory":
      return hasArray(data.products);
    case "evaluate_refund_eligibility":
      return "eligible" in data || Boolean(data.reason || data.suggested_next_action);
    case "query_after_sales_ticket":
    case "create_after_sales_ticket":
    case "query_customer_tickets":
      return hasArray(data.tickets) || isRecord(data.ticket);
    default:
      return hasMeaningfulData(data);
  }
}

function hasArray(value: unknown): value is unknown[] {
  return Array.isArray(value) && value.length > 0;
}

function hasMeaningfulData(data: unknown): boolean {
  if (Array.isArray(data)) return data.length > 0;
  if (isRecord(data)) return Object.keys(data).length > 0;
  return data !== undefined && data !== null && data !== "";
}
