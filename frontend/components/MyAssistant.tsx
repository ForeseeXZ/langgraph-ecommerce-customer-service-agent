"use client";

import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAssistantInstructions,
  useAssistantToolUI,
  useEdgeRuntime,
} from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";

const MarkdownText = makeMarkdownText();

const EXAMPLE_QUESTIONS = [
  "帮我查一下订单 SO20260418001 的物流状态",
  "SKU2001 现在还有库存吗，什么时候补货？",
  "数码产品质量问题可以怎么退款？",
  "帮我为订单 SO20260417008 创建一个质量问题售后工单",
];

function ToolUIs() {
  useAssistantToolUI({
    toolName: "query_order_status",
    render: ({ result }) => (
      <ToolResultCard
        title="订单状态查询"
        result={result}
        fields={[
          ["订单号", "order_id"],
          ["订单状态", "status"],
          ["物流公司", "shipping_company"],
          ["物流单号", "tracking_no"],
          ["预计送达", "estimated_delivery"],
        ]}
      />
    ),
  });

  useAssistantToolUI({
    toolName: "query_product_inventory",
    render: ({ result }) => (
      <ToolResultCard
        title="商品库存查询"
        result={result}
        fields={[
          ["商品编号", "product_id"],
          ["商品名称", "product_name"],
          ["可用库存", "available_stock"],
          ["锁定库存", "locked_stock"],
          ["仓库", "warehouse"],
          ["补货时间", "restock_eta"],
        ]}
      />
    ),
  });

  useAssistantToolUI({
    toolName: "query_refund_policy",
    render: ({ result }) => (
      <ToolResultCard
        title="退款规则查询"
        result={result}
        fields={[
          ["适用品类", "category"],
          ["问题类型", "issue_type"],
          ["规则摘要", "rule_summary"],
          ["处理时效", "processing_time"],
        ]}
        listField={["条件说明", "conditions"]}
      />
    ),
  });

  useAssistantToolUI({
    toolName: "create_after_sales_ticket",
    render: ({ result }) => (
      <ToolResultCard
        title="售后工单创建"
        result={result}
        fields={[
          ["工单编号", "ticket_id"],
          ["订单号", "order_id"],
          ["问题类型", "issue_type"],
          ["工单状态", "status"],
          ["联系电话", "contact_phone"],
          ["响应承诺", "sla"],
        ]}
      />
    ),
  });

  return null;
}

function ToolResultCard({
  title,
  result,
  fields,
  listField,
}: {
  title: string;
  result: any;
  fields: Array<[string, string]>;
  listField?: [string, string];
}) {
  const data = result?.data ?? {};
  const status = result?.status ?? "unknown";
  const message = result?.message ?? "工具调用已完成";
  const listItems =
    listField && Array.isArray(data?.[listField[1]]) ? data[listField[1]] : [];

  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50/90 p-4 text-sm text-slate-800 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="font-semibold text-slate-900">{title}</div>
        <span className="rounded-full bg-white px-2 py-1 text-xs text-slate-600">
          {status}
        </span>
      </div>
      <p className="mb-3 text-slate-600">{message}</p>
      <div className="grid gap-2 md:grid-cols-2">
        {fields.map(([label, key]) =>
          data?.[key] ? (
            <div key={key} className="rounded-xl bg-white px-3 py-2">
              <div className="text-xs text-slate-500">{label}</div>
              <div className="mt-1 text-sm font-medium text-slate-900">
                {String(data[key])}
              </div>
            </div>
          ) : null,
        )}
      </div>
      {listField && listItems.length > 0 ? (
        <div className="mt-3 rounded-xl bg-white px-3 py-3">
          <div className="mb-2 text-xs text-slate-500">{listField[0]}</div>
          <ul className="space-y-1 text-sm text-slate-800">
            {listItems.map((item: string) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div className="max-w-[85%] rounded-3xl rounded-br-md bg-slate-900 px-4 py-3 text-sm text-white shadow-sm">
        <MessagePrimitive.Content components={{ Text: MarkdownText }} />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex items-start gap-3">
      <div className="mt-1 flex h-9 w-9 items-center justify-center rounded-full bg-amber-500 text-xs font-semibold text-white">
        售后
      </div>
      <div className="max-w-[90%] space-y-3">
        <div className="rounded-3xl rounded-tl-md bg-white px-4 py-3 text-sm text-slate-900 shadow-sm ring-1 ring-slate-200">
          <MessagePrimitive.Content components={{ Text: MarkdownText }} />
        </div>
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantSurface() {
  useAssistantInstructions(`
你是“橙意电商”的中文售后智能客服助理。
请优先围绕订单状态、库存、退款规则、售后工单来回答。
如果涉及业务数据，请尽量调用工具，不要凭空编造。
工具返回后，先总结结果，再给出下一步建议。
`.trim());

  return (
    <>
      <ToolUIs />
      <div className="flex h-full flex-col rounded-[28px] border border-white/70 bg-white/75 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col">
          <ThreadPrimitive.Viewport className="flex-1 space-y-4 overflow-y-auto px-4 py-5 md:px-6">
            <ThreadPrimitive.Empty>
              <div className="rounded-[28px] bg-[linear-gradient(135deg,#fff7ed_0%,#fffbeb_45%,#f8fafc_100%)] p-6 shadow-sm ring-1 ring-amber-100">
                <div className="inline-flex rounded-full bg-white px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-amber-200">
                  中文电商售后 Agent Demo
                </div>
                <h2 className="mt-4 text-2xl font-semibold tracking-tight text-slate-900">
                  你好，这里是橙意电商售后中心
                </h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
                  这个演示系统支持中文售后问答，并可调用订单查询、库存查询、退款规则查询与售后工单创建工具。
                  你可以直接输入问题，或者点击下面的示例问题快速体验。
                </p>
                <div className="mt-5 grid gap-3 md:grid-cols-2">
                  {EXAMPLE_QUESTIONS.map((question) => (
                    <ThreadPrimitive.Suggestion
                      key={question}
                      prompt={question}
                      method="replace"
                      autoSend
                      className="rounded-2xl bg-white px-4 py-3 text-left text-sm text-slate-700 shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-0.5 hover:bg-amber-50"
                    >
                      {question}
                    </ThreadPrimitive.Suggestion>
                  ))}
                </div>
              </div>
            </ThreadPrimitive.Empty>

            <ThreadPrimitive.Messages
              components={{
                UserMessage,
                AssistantMessage,
              }}
            />
          </ThreadPrimitive.Viewport>

          <div className="border-t border-slate-200/80 px-4 py-4 md:px-6">
            <ComposerPrimitive.Root className="rounded-[24px] bg-slate-50 p-2 shadow-inner ring-1 ring-slate-200">
              <ComposerPrimitive.Input
                rows={4}
                placeholder="请输入售后问题，例如：帮我查一下订单 SO20260418001 的物流状态"
                className="min-h-[96px] w-full resize-none bg-transparent px-3 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
              />
              <div className="mt-2 flex items-center justify-between px-2 pb-1">
                <p className="text-xs text-slate-500">
                  演示数据为本地 mock 数据，适合课程作业展示。
                </p>
                <ComposerPrimitive.Send className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-amber-600">
                  发送
                </ComposerPrimitive.Send>
              </div>
            </ComposerPrimitive.Root>
          </div>
        </ThreadPrimitive.Root>
      </div>
    </>
  );
}

export function MyAssistant() {
  const runtime = useEdgeRuntime({
    api: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/chat",
    unstable_AISDKInterop: true,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <AssistantSurface />
    </AssistantRuntimeProvider>
  );
}
