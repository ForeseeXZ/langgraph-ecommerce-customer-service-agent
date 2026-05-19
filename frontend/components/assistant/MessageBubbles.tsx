"use client";

import { MessagePrimitive, useMessage, useThreadRuntime } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";
import { useCallback, useMemo } from "react";
import remarkGfm from "remark-gfm";

const MarkdownText = makeMarkdownText({ remarkPlugins: [remarkGfm] });

const DEFAULT_SUGGESTIONS = [
  "帮我查一下订单的物流状态",
  "七天无理由退货需要满足什么条件？",
  "查一下工单处理到哪一步了？",
];

const TOOL_SUGGESTION_MAP: Record<string, string[]> = {
  query_order_status: ["查询退款政策", "创建售后工单", "查询物流轨迹"],
  query_shipment_tracking: ["查询退款政策", "创建售后工单", "查询库存补货"],
  query_product_inventory: ["查询订单状态", "查询退款资格", "查询退款政策"],
  evaluate_refund_eligibility: ["创建售后工单", "查询退款政策"],
  query_after_sales_ticket: ["催促处理进度", "查询退款政策"],
  query_customer_tickets: ["查询工单进度", "创建售后工单"],
  create_after_sales_ticket: ["查询工单处理进度", "查询退款政策"],
  query_refund_policy: ["创建售后工单", "查询订单状态", "查询退款资格"],
  query_refund_policy_rag: ["创建售后工单", "查询订单状态", "查询退款资格"],
};

function getSuggestionsFromToolNames(toolNames: string[]): string[] {
  if (toolNames.length === 0) return DEFAULT_SUGGESTIONS;

  const seen = new Set<string>();
  const suggestions: string[] = [];

  for (const toolName of toolNames) {
    const mapped = TOOL_SUGGESTION_MAP[toolName];
    if (!mapped) continue;

    for (const suggestion of mapped) {
      if (!seen.has(suggestion)) {
        seen.add(suggestion);
        suggestions.push(suggestion);
      }
    }
  }

  return suggestions.length > 0 ? suggestions : DEFAULT_SUGGESTIONS;
}

function SuggestionChips() {
  const toolNamesJson = useMessage((message) => {
    if (message.role !== "assistant") return "[]";

    const toolNames = message.content
      .filter((part) => part.type === "tool-call")
      .map((part) => part.toolName);

    return JSON.stringify(toolNames);
  });
  const suggestions = useMemo(
    () => getSuggestionsFromToolNames(JSON.parse(toolNamesJson) as string[]),
    [toolNamesJson],
  );
  const threadRuntime = useThreadRuntime();
  const handleClick = useCallback(
    (suggestion: string) => () => threadRuntime.append(suggestion),
    [threadRuntime],
  );

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion}
          type="button"
          onClick={handleClick(suggestion)}
          className="inline-flex items-center rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1.5 text-xs font-medium text-cyan-800 shadow-sm transition hover:border-cyan-400 hover:bg-cyan-100 hover:text-cyan-950"
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
}

export function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div className="max-w-[82%] rounded-lg rounded-br-sm bg-[linear-gradient(135deg,#0f172a,#155e75)] px-4 py-3 text-sm leading-6 text-white shadow-md shadow-slate-300">
        <MessagePrimitive.Content components={{ Text: MarkdownText }} />
      </div>
    </MessagePrimitive.Root>
  );
}

export function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex items-start gap-3">
      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-xs font-semibold text-cyan-200 shadow-sm">
        售
      </div>
      <div className="max-w-[90%] space-y-1">
        <div className="rounded-lg rounded-tl-sm bg-white px-4 py-3 text-sm leading-6 text-slate-900 shadow-sm ring-1 ring-slate-200">
          <MessagePrimitive.Content components={{ Text: MarkdownText }} />
        </div>
        <SuggestionChips />
      </div>
    </MessagePrimitive.Root>
  );
}
